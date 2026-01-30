# Attuned Payments & Subscriptions

## Overview

Attuned uses a hybrid payment architecture:
- **RevenueCat**: Central subscription management hub (single source of truth)
- **Stripe**: External payments for US users (0% platform fee)
- **Apple/Google IAP**: Fallback for non-US users (15-30% fee)

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  FlutterFlow    │────▶│  RevenueCat  │────▶│  Flask Backend  │
│  (Frontend)     │     │  (Hub)       │     │  (Webhooks)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Region Detect   │     │ Stripe (US)  │     │    Supabase     │
│ US → Stripe     │     │ IAP (non-US) │     │ (subscription   │
│ Other → IAP     │     └──────────────┘     │  state)         │
└─────────────────┘                          └─────────────────┘
```

## Pricing

| Plan | Standard | Discounted (20% off) |
|------|----------|---------------------|
| Monthly | $4.99/month | $3.99/month |
| Annual | $29.99/year | $23.99/year |

**Free Tier**: Lifetime limit of 10 activities (configurable via `app_config.free_tier_activity_limit`)

## Database Schema

See `backend/migrations/027_add_subscription_enhancements.sql` for full schema.

### Key Tables

- **influencers** - Marketing partners who distribute promo codes
- **promo_codes** - Discount codes with usage limits and expiration
- **promo_redemptions** - Tracks which users redeemed which codes

### Users Table Subscription Columns

```sql
subscription_platform TEXT;          -- 'stripe' | 'apple' | 'google'
subscription_product_id TEXT;        -- 'attuned_monthly' | 'attuned_annual'
subscription_expires_at TIMESTAMPTZ;
subscription_cancelled_at TIMESTAMPTZ;
billing_issue_detected_at TIMESTAMPTZ;
revenuecat_app_user_id TEXT;
stripe_customer_id TEXT;
lifetime_activity_count INTEGER DEFAULT 0;
pending_promo_code TEXT;             -- Set during validation
promo_code_used TEXT;                -- Set on purchase webhook
```

## Implementation Patterns

### Promo Code Validation Flow

1. User enters code in app
2. App calls `POST /api/promo/validate` with code
3. Backend validates code and sets `user.pending_promo_code`
4. App shows discounted offering in RevenueCat
5. User completes purchase
6. RevenueCat sends `INITIAL_PURCHASE` webhook
7. Backend creates `promo_redemption`, clears `pending_promo_code`, sets `promo_code_used`

### Subscription Service (Event Handler)

The `SubscriptionService` class handles all RevenueCat webhook events:

```python
# backend/src/services/subscription_service.py
class SubscriptionService:
    STORE_MAP = {
        'APP_STORE': 'apple',
        'PLAY_STORE': 'google',
        'STRIPE': 'stripe',
    }

    @classmethod
    def process_webhook_event(cls, user: User, event: dict) -> dict:
        handlers = {
            'INITIAL_PURCHASE': cls._handle_initial_purchase,
            'RENEWAL': cls._handle_renewal,
            'CANCELLATION': cls._handle_cancellation,
            'UNCANCELLATION': cls._handle_uncancellation,
            'EXPIRATION': cls._handle_expiration,
            'BILLING_ISSUE': cls._handle_billing_issue,
            'PRODUCT_CHANGE': cls._handle_product_change,
        }
        handler = handlers.get(event.get('type'))
        if not handler:
            return {'handled': False}
        return handler(user, event)
```

### Webhook Authentication

Uses Bearer token (not HMAC signature) for simplicity:

```python
# backend/src/routes/webhooks.py
def verify_webhook_auth():
    secret = os.environ.get('REVENUECAT_WEBHOOK_SECRET')
    if not secret:
        return False
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    return auth_header[7:] == secret
```

### Idempotency Patterns

Every event handler checks current state before making changes:

```python
# Skip if already premium with same product
if (user.subscription_tier == 'premium' and
        user.subscription_product_id == product_id):
    return {'handled': True, 'skipped': True}

# Skip if already cancelled
if user.subscription_cancelled_at is not None:
    return {'handled': True, 'skipped': True}
```

## API Endpoints

### Promo Validation
`POST /api/promo/validate`
- Auth: JWT required
- Body: `{ "code": "VANESSA" }`
- Sets `user.pending_promo_code` on success
- Returns offering_id for RevenueCat

### Subscription Status
`GET /api/subscriptions/status/<user_id>`
- Auth: JWT required (own user only)
- Returns tier, expiry, activity counts, billing status

### Activity Limit Check
`GET /api/subscriptions/check-limit/<user_id>`
- Auth: JWT required (own user only)
- Returns `has_limit`, `limit_reached`, `remaining`

### Webhook
`POST /api/webhooks/revenuecat`
- Auth: Bearer token (REVENUECAT_WEBHOOK_SECRET)
- Always returns 200 to prevent retries
- Delegates to SubscriptionService

## Testing Requirements

Every endpoint must have:
1. **401 test** - Request without auth token
2. **403 test** - Request with wrong user's token
3. **Success test** - Happy path
4. **Error case tests** - Invalid input, not found

Test files:
- `tests/test_promo_codes.py` - Promo validation logic
- `tests/test_subscription_service.py` - Event handlers (unit tests)
- `tests/test_webhooks.py` - HTTP layer + auth
- `tests/test_subscription_limits.py` - Limit checks and increments

## Environment Variables

```bash
# Required for webhooks
REVENUECAT_WEBHOOK_SECRET=your_webhook_secret_here

# Optional
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

## RevenueCat Configuration

### Offerings
| Offering ID | Products | Use Case |
|-------------|----------|----------|
| `default` | attuned_monthly ($4.99), attuned_annual ($29.99) | Standard pricing |
| `discounted_20_percent` | attuned_monthly_discounted ($3.99), attuned_annual_discounted ($23.99) | Promo code users |

### Webhook Configuration
- URL: `https://attuned-backend.onrender.com/api/webhooks/revenuecat`
- Auth: Bearer token in Authorization header
- Events: All subscription lifecycle events

## Influencer Performance Query

```sql
SELECT
  i.name AS influencer,
  i.platform,
  pc.code,
  pc.redemption_count AS redemptions,
  (SELECT COUNT(*) FROM promo_redemptions pr
   WHERE pr.promo_code_id = pc.id) AS tracked_redemptions
FROM influencers i
JOIN promo_codes pc ON i.id = pc.influencer_id
WHERE i.status = 'active'
ORDER BY pc.redemption_count DESC;
```

## Common Patterns

### Checking Subscription Access

```python
def is_premium(user):
    return (
        user.subscription_tier == 'premium' and
        (user.subscription_expires_at is None or
         user.subscription_expires_at > datetime.now(timezone.utc))
    )
```

### Activity Limit Enforcement

```python
limit = get_config_int('free_tier_activity_limit', 10)
used = user.lifetime_activity_count or 0
can_play = user.subscription_tier == 'premium' or used < limit
```

### Store Name Mapping

```python
STORE_MAP = {
    'APP_STORE': 'apple',
    'PLAY_STORE': 'google',
    'STRIPE': 'stripe',
    'AMAZON': 'amazon',
    'PROMOTIONAL': 'promo'
}
platform = STORE_MAP.get(event.get('store'), 'unknown')
```
