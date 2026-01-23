# Backend Subscription API - Frontend Handshake Document

> **For Frontend Agent**: This document explains the backend subscription APIs you'll integrate with. The backend handles all subscription state persistence, webhook processing, and promo code attribution.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   FlutterFlow   │────────▶│    RevenueCat    │────────▶│  Flask Backend  │
│   (Frontend)    │         │   (Purchases)    │         │   (Webhooks)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                                                         │
        │  1. Validate promo code                                 │
        │  2. Get subscription status                             │
        │◀────────────────────────────────────────────────────────│
        │                                                         │
        │  RevenueCat sends webhook on purchase ─────────────────▶│
        │                                                         │
        │  3. Sync status (reflects webhook updates)              │
        │◀────────────────────────────────────────────────────────│
```

**Key Principle**: The backend is the source of truth for subscription state. RevenueCat sends webhooks to update the backend, and the frontend reads state from backend APIs.

---

## API Endpoints

### 1. Promo Code Validation

**Endpoint**: `POST /api/promo/validate`

**Purpose**: Validate a promo code and get the RevenueCat offering ID for discounted pricing.

**Auth**: JWT Bearer token required

**Request**:
```json
{
  "code": "VANESSA"
}
```

**Response (Success)**:
```json
{
  "valid": true,
  "code": "VANESSA",
  "discount_percent": 20,
  "influencer_name": "Vanessa Marin",
  "offering_id": "discounted_20_percent"
}
```

**Response (Invalid)**:
```json
{
  "valid": false,
  "error": "Code not found"
}
```

**Possible Errors**:
| Error Message | Meaning |
|---------------|---------|
| `"Code not found"` | Promo code doesn't exist |
| `"Code is inactive"` | Code has been deactivated |
| `"Code has expired"` | Past expiration date |
| `"Maximum redemptions reached"` | Usage limit hit |
| `"Code already used"` | This user already redeemed a code |

**Side Effect**: On success, sets `user.pending_promo_code` in the database. This is cleared when the purchase webhook arrives.

**Frontend Action**: Use the returned `offering_id` when calling RevenueCat's purchase flow.

---

### 2. Subscription Status

**Endpoint**: `GET /api/subscriptions/status/[user_id]`

> **FlutterFlow Note**: Use `[user_id]` syntax for path parameters, not `<user_id>`.

**Purpose**: Get complete subscription state for display and decision-making.

**Auth**: JWT Bearer token required (must be own user_id)

**Response (Premium User)**:
```json
{
  "user_id": "uuid-here",
  "subscription_tier": "premium",
  "is_premium": true,
  "expires_at": "2026-02-22T00:00:00+00:00",
  "is_cancelled": false,
  "platform": "stripe",
  "product_id": "attuned_monthly",
  "activities_used": 5,
  "activities_limit": null,
  "activities_remaining": null,
  "has_billing_issue": false,
  "promo_code_used": "VANESSA"
}
```

**Response (Free User)**:
```json
{
  "user_id": "uuid-here",
  "subscription_tier": "free",
  "is_premium": false,
  "expires_at": null,
  "is_cancelled": false,
  "platform": null,
  "product_id": null,
  "activities_used": 3,
  "activities_limit": 10,
  "activities_remaining": 7,
  "has_billing_issue": false,
  "promo_code_used": null
}
```

**Field Definitions**:

| Field | Type | Description |
|-------|------|-------------|
| `subscription_tier` | string | `"premium"` or `"free"` |
| `is_premium` | bool | `true` if premium AND not expired |
| `expires_at` | string/null | ISO timestamp of subscription end |
| `is_cancelled` | bool | User cancelled but still has access |
| `platform` | string/null | `"stripe"`, `"apple"`, `"google"`, or null |
| `product_id` | string/null | RevenueCat product identifier |
| `activities_used` | int | Lifetime activities consumed |
| `activities_limit` | int/null | Limit for free tier (null for premium) |
| `activities_remaining` | int/null | Activities left (null for premium) |
| `has_billing_issue` | bool | Payment failed, needs attention |
| `promo_code_used` | string/null | Redeemed promo code |

---

### 3. Activity Limit Check (Quick Check)

**Endpoint**: `GET /api/subscriptions/check-limit/[user_id]`

**Purpose**: Quick check if user can play (used before starting game).

**Auth**: JWT Bearer token required

**Response (Free User Under Limit)**:
```json
{
  "has_limit": true,
  "limit_reached": false,
  "activities_used": 3,
  "limit": 10,
  "remaining": 7
}
```

**Response (Free User At Limit)**:
```json
{
  "has_limit": true,
  "limit_reached": true,
  "activities_used": 10,
  "limit": 10,
  "remaining": 0
}
```

**Response (Premium User)**:
```json
{
  "has_limit": false,
  "limit_reached": false,
  "remaining": -1
}
```

---

### 4. Increment Activity Count

**Endpoint**: `POST /api/subscriptions/increment-activity/[user_id]`

**Purpose**: Called after an activity is presented to user.

**Auth**: JWT Bearer token required

**Note**: Only increments for free tier users. Premium users are no-op.

**Response**:
```json
{
  "success": true,
  "lifetime_activity_count": 4
}
```

---

## Webhook Processing (Backend Internal)

The backend receives webhooks from RevenueCat at `POST /api/webhooks/revenuecat`. The frontend does NOT call this endpoint.

**Events Handled**:

| Event | Backend Action |
|-------|----------------|
| `INITIAL_PURCHASE` | Set user to premium, record platform/product, process promo attribution |
| `RENEWAL` | Update expiration date |
| `CANCELLATION` | Set `subscription_cancelled_at` (user keeps access until expiry) |
| `UNCANCELLATION` | Clear `subscription_cancelled_at` |
| `EXPIRATION` | Downgrade user to free tier |
| `BILLING_ISSUE` | Set `billing_issue_detected_at` flag |
| `PRODUCT_CHANGE` | Update product_id (monthly↔annual) |

**Promo Attribution**: If user has `pending_promo_code` set when `INITIAL_PURCHASE` arrives, the backend:
1. Creates a `promo_redemption` record
2. Increments the promo code's usage count
3. Sets `user.promo_code_used`
4. Clears `user.pending_promo_code`

---

## Integration Flow

### Flow 1: User Purchases Without Promo Code

```
1. Frontend: Show SubscriptionIntroPage
2. Frontend: User taps "Annual" or "Monthly"
3. Frontend: Call RevenueCat purchase with offering_id = "default"
4. RevenueCat: Process payment, send INITIAL_PURCHASE webhook to backend
5. Backend: Update user to premium
6. Frontend: Call GET /api/subscriptions/status/[user_id]
7. Frontend: Update app state with subscription info
8. Frontend: Navigate to success/home
```

### Flow 2: User Purchases With Promo Code

```
1. Frontend: Show SubscriptionIntroPage
2. Frontend: User enters promo code, taps "Apply"
3. Frontend: Call POST /api/promo/validate with code
4. Backend: Validate code, set user.pending_promo_code, return offering_id
5. Frontend: Store offering_id ("discounted_20_percent"), show discounted prices
6. Frontend: User taps "Annual" or "Monthly"
7. Frontend: Call RevenueCat purchase with offering_id = "discounted_20_percent"
8. RevenueCat: Process payment at discounted price, send webhook
9. Backend: Update user to premium, attribute promo code
10. Frontend: Call GET /api/subscriptions/status/[user_id]
11. Frontend: Update app state (includes promo_code_used)
12. Frontend: Navigate to success/home
```

### Flow 3: App Launch Subscription Sync

```
1. Frontend: App launches, user is authenticated
2. Frontend: Call GET /api/subscriptions/status/[user_id]
3. Frontend: Update isPremium, activitiesRemaining app state
4. Frontend: Conditionally show premium/free UI
```

### Flow 4: Game Start Limit Check

```
1. Frontend: User taps "Play"
2. Frontend: Call GET /api/subscriptions/check-limit/[user_id]
3. If limit_reached == true:
   - Show upgrade prompt
4. Else:
   - Start game
   - After activity shown: Call POST /api/subscriptions/increment-activity/[user_id]
```

---

## Timing Considerations

### Webhook Delay

After a RevenueCat purchase completes, there may be a 1-5 second delay before the webhook updates the backend. If the frontend calls `/status` immediately after purchase, it might still show `free`.

**Recommended Approach**:
- After purchase success from RevenueCat, wait 2 seconds before calling sync
- Or optimistically set `isPremium = true` locally, then confirm with sync

### Promo Code Expiration

The `pending_promo_code` on the user has no timeout. If a user validates a code but never purchases, the code stays pending. This is acceptable - it gets cleared/used on next purchase.

---

## Error Handling

All endpoints return standard error responses:

**401 Unauthorized** (no/invalid JWT):
```json
{"error": "Unauthorized"}
```

**403 Forbidden** (accessing another user's data):
```json
{"error": "Unauthorized"}
```

**404 Not Found**:
```json
{"error": "User not found"}
```

**500 Server Error**:
```json
{"error": "Validation failed"}
```

---

## App State Mapping

Recommended frontend app state based on backend responses:

| App State Variable | Source |
|--------------------|--------|
| `isPremium` | `subscriptionStatus.is_premium` |
| `activitiesRemaining` | `subscriptionStatus.activities_remaining` |
| `subscriptionStatus` | Full response from `/status` endpoint |
| `appliedPromoCode` | From `/promo/validate` response, cleared after purchase |
| `appliedOfferingId` | From `/promo/validate` response (`offering_id`) |

---

## Testing Notes

### Sandbox Testing
- Use RevenueCat sandbox mode
- Backend webhook endpoint works with sandbox events
- Promo codes work the same in sandbox

### Test Promo Codes
Create test codes in the database:
```sql
INSERT INTO influencers (name, email, platform, status)
VALUES ('Test Influencer', 'test@test.com', 'test', 'active');

INSERT INTO promo_codes (influencer_id, code, discount_percent, revenuecat_offering_id, is_active)
VALUES ((SELECT id FROM influencers WHERE name = 'Test Influencer'), 'TEST20', 20, 'discounted_20_percent', true);
```

---

## Questions?

If the backend behavior doesn't match this document, check:
1. Is the code deployed? (merge to develop triggers Render deploy)
2. Is the webhook secret configured? (`REVENUECAT_WEBHOOK_SECRET` on Render)
3. Is migration 027 applied? (creates required tables/columns)
