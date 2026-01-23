# Subscription Backend Implementation Plan

**Date:** 2026-01-22
**Branch:** `feature/subscription-revenuecat-backend`
**Status:** Pending Approval

## Overview

Implement subscription backend for RevenueCat integration with Stripe (US) and Apple/Google IAP (international). RevenueCat is the single source of truth - our backend only receives webhooks.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Activity limits | Lifetime (10 total) | Configurable via app_config |
| Migration for existing users | Zero-out | Fresh start with new model |
| Webhook secret storage | Environment variable | Consistent with existing secrets |
| Existing webhook stubs | Remove | RevenueCat replaces direct store webhooks |
| Subscription state tracking | Timestamps | `cancelled_at`, `billing_issue_at` for debugging |
| Stripe integration | RevenueCat-managed | We store `stripe_customer_id` if provided |
| Promo redemption | On webhook (Option C) | Most reliable, no app callback needed |
| Promo validation | Associate on validate | Sets `pending_promo_code` immediately |
| RevenueCat API key | Skip for now | Only receiving webhooks, not calling API |
| Webhook auth | Bearer token | RevenueCat's standard approach |

## Database Schema

### Migration: `027_add_subscription_enhancements.sql`

#### Users Table Additions

```sql
ALTER TABLE users ADD COLUMN subscription_platform TEXT;
ALTER TABLE users ADD COLUMN subscription_product_id TEXT;
ALTER TABLE users ADD COLUMN revenuecat_app_user_id TEXT;
ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN lifetime_activity_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN pending_promo_code TEXT;
ALTER TABLE users ADD COLUMN promo_code_used TEXT;
ALTER TABLE users ADD COLUMN subscription_cancelled_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN billing_issue_detected_at TIMESTAMPTZ;
```

#### Promo Codes Table (NEW)

```sql
CREATE TABLE promo_codes (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    influencer_name TEXT,
    discount_percent INTEGER DEFAULT 20,
    stripe_coupon_id TEXT,
    revenuecat_offering_id TEXT DEFAULT 'discounted_20_percent',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ,
    max_redemptions INTEGER,
    redemption_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_promo_codes_code ON promo_codes(code);
CREATE INDEX idx_promo_codes_active ON promo_codes(is_active) WHERE is_active = true;
```

#### Promo Redemptions Table (NEW)

```sql
CREATE TABLE promo_redemptions (
    id SERIAL PRIMARY KEY,
    promo_code_id INTEGER REFERENCES promo_codes(id),
    user_id UUID REFERENCES users(id),
    subscription_product TEXT,
    original_price DECIMAL(10,2),
    discounted_price DECIMAL(10,2),
    redeemed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_promo_redemptions_user ON promo_redemptions(user_id);
CREATE INDEX idx_promo_redemptions_code ON promo_redemptions(promo_code_id);
```

#### RLS Policies

```sql
-- promo_codes: service role only (no client access)
ALTER TABLE promo_codes ENABLE ROW LEVEL SECURITY;
-- No policies - service role bypasses RLS

-- promo_redemptions: users read their own only
ALTER TABLE promo_redemptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY promo_redemptions_select_own ON promo_redemptions
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);
```

#### AppConfig Seeds

```sql
INSERT INTO app_config (key, value, description) VALUES
  ('free_tier_activity_limit', '10', 'Lifetime activities for free users'),
  ('monthly_price_usd', '4.99', 'Monthly subscription price'),
  ('annual_price_usd', '29.99', 'Annual subscription price');
```

#### Zero-Out Existing Users

```sql
UPDATE users SET lifetime_activity_count = 0 WHERE subscription_tier = 'free';
```

---

## API Endpoints

### Promo Validation

**Endpoint:** `POST /api/promo/validate`
**Auth:** Required (JWT)

**Request:**
```json
{ "code": "VANESSA" }
```

**Response (success):**
```json
{
  "valid": true,
  "code": "VANESSA",
  "discount_percent": 20,
  "influencer_name": "Vanessa Marin",
  "offering_id": "discounted_20_percent"
}
```

**Response (error):**
```json
{
  "valid": false,
  "error": "Code not found" | "Code has expired" | "Maximum redemptions reached" | "Code already used"
}
```

**Logic:**
1. Find code (case-insensitive)
2. Check code validity (active, not expired, under max)
3. Check user hasn't already redeemed this code (query `promo_redemptions`)
4. Set `user.pending_promo_code`
5. Return offering info

### RevenueCat Webhook

**Endpoint:** `POST /api/webhooks/revenuecat`
**Auth:** Bearer token in Authorization header

**Events Handled:**

| Event | Action |
|-------|--------|
| `INITIAL_PURCHASE` | Set premium, store platform/product, process pending promo |
| `RENEWAL` | Update `subscription_expires_at` |
| `CANCELLATION` | Set `subscription_cancelled_at` |
| `UNCANCELLATION` | Clear `subscription_cancelled_at` |
| `EXPIRATION` | Downgrade to free tier |
| `BILLING_ISSUE` | Set `billing_issue_detected_at` |
| `PRODUCT_CHANGE` | Update `subscription_product_id` |
| `SUBSCRIBER_ALIAS` | Store `revenuecat_app_user_id` |

**Idempotency:** Each handler checks current state before updating.

### Subscription Status

**Endpoint:** `GET /api/subscriptions/status/<user_id>`
**Auth:** Required, owner only

**Response:**
```json
{
  "user_id": "uuid",
  "subscription_tier": "premium",
  "is_premium": true,
  "expires_at": "2026-02-22T00:00:00Z",
  "is_cancelled": false,
  "platform": "stripe",
  "product_id": "attuned_monthly_premium",
  "activities_used": 5,
  "activities_limit": null,
  "activities_remaining": null,
  "has_billing_issue": false,
  "promo_code_used": "VANESSA"
}
```

### Activity Limit Check

**Endpoint:** `GET /api/subscriptions/check-limit/<user_id>`
**Auth:** Required, owner only

**Response (free user):**
```json
{
  "has_limit": true,
  "limit_reached": false,
  "activities_used": 5,
  "limit": 10,
  "remaining": 5
}
```

**Response (premium user):**
```json
{
  "has_limit": false,
  "limit_reached": false,
  "remaining": -1
}
```

### Activity Increment

**Endpoint:** `POST /api/subscriptions/increment-activity/<user_id>`
**Auth:** Required, owner only

Increments `lifetime_activity_count` for free users only.

---

## File Structure

### New Files (7)

```
backend/
├── migrations/
│   ├── 027_add_subscription_enhancements.sql
│   └── 027_rollback.sql
├── src/
│   ├── models/
│   │   ├── promo_code.py
│   │   └── promo_redemption.py
│   ├── routes/
│   │   ├── promo.py
│   │   └── webhooks.py
│   └── services/
│       └── subscription_service.py
└── tests/
    ├── test_promo_codes.py
    ├── test_webhooks.py
    └── test_subscription_service.py
```

### Modified Files (4)

```
backend/src/
├── models/
│   ├── __init__.py              # Add PromoCode, PromoRedemption exports
│   └── user.py                   # Add 9 new columns
├── routes/
│   └── subscriptions.py          # Lifetime limits, remove old stubs
└── main.py                       # Register promo_bp, webhooks_bp
```

### Updated Tests (1)

```
backend/tests/
└── test_subscription_limits.py   # Daily → lifetime model
```

---

## Implementation Phases

### Phase 1: Foundation

| Step | Task |
|------|------|
| 1.1 | Create migration `027_add_subscription_enhancements.sql` |
| 1.2 | Create rollback `027_rollback.sql` |
| 1.3 | Run migration, verify tables exist |
| 1.4 | Create `models/promo_code.py`, `promo_redemption.py` |
| 1.5 | Update `models/user.py` with new columns |
| 1.6 | Update `models/__init__.py` exports |

**Checkpoint:** `python -c "from src.models import PromoCode, PromoRedemption"` succeeds

---

### Phase 2: Subscription Limits

| Step | Task |
|------|------|
| 2.1 | Update `routes/subscriptions.py` - change to lifetime limits |
| 2.2 | Remove old webhook stubs from `subscriptions.py` |
| 2.3 | Update `test_subscription_limits.py` for lifetime model |
| 2.4 | **Run:** `pytest tests/test_subscription_limits.py -v` |

**Checkpoint:** All lifetime limit tests pass

---

### Phase 3: Promo Validation

| Step | Task |
|------|------|
| 3.1 | Create `routes/promo.py` |
| 3.2 | Register blueprint in `main.py` |
| 3.3 | Write `test_promo_codes.py` |
| 3.4 | **Run:** `pytest tests/test_promo_codes.py -v` |

**Checkpoint:** Promo validation works, `pending_promo_code` gets set

---

### Phase 4: Subscription Service

| Step | Task |
|------|------|
| 4.1 | Create `services/subscription_service.py` |
| 4.2 | Write `test_subscription_service.py` |
| 4.3 | **Run:** `pytest tests/test_subscription_service.py -v` |

**Checkpoint:** Event handlers work in isolation

---

### Phase 5: Webhook Endpoint

| Step | Task |
|------|------|
| 5.1 | Create `routes/webhooks.py` |
| 5.2 | Register blueprint in `main.py` |
| 5.3 | Write `test_webhooks.py` |
| 5.4 | **Run:** `pytest tests/test_webhooks.py -v` |

**Checkpoint:** Full HTTP flow works end-to-end

---

### Phase 6: Full Verification

| Step | Task |
|------|------|
| 6.1 | **Run:** `pytest tests/ -v` (entire suite) |
| 6.2 | Manual test with RevenueCat test webhook |
| 6.3 | Code review |

**Checkpoint:** All tests pass, ready for deploy

---

## Environment Variables

Add to `.env` and Render:

```
REVENUECAT_WEBHOOK_SECRET=your_secret_here
```

---

## Post-Implementation Checklist

- [ ] Migration runs successfully on Supabase
- [ ] All new tests pass
- [ ] Existing test suite still passes
- [ ] Promo code validation works end-to-end
- [ ] Webhook signature verification works
- [ ] Manual test with RevenueCat test webhook
- [ ] Update Render environment variables
- [ ] Configure RevenueCat webhook URL in dashboard

---

## Notes

- Verify RevenueCat's exact webhook auth mechanism during implementation
- Promo `original_price` stored as NULL (unknown from webhook), `discounted_price` = actual payment
- Keep `daily_activity_count` columns for backward compatibility during transition
- Service role bypasses RLS for promo_codes table
