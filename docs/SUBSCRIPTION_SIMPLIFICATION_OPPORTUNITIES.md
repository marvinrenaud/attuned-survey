# Subscription Implementation: Opportunities to Simplify Frontend

> **Analysis of the Frontend Implementation Guide vs Backend Capabilities**
>
> Goal: Identify where we can reduce frontend complexity by leveraging backend more.

---

## Summary

| Opportunity | Impact | Recommendation |
|-------------|--------|----------------|
| Price display from backend | Medium | **Implement** |
| Webhook confirmation polling | Medium | **Defer** (timing usually fine) |
| Pending promo retrieval | Low | **Skip** (current flow works) |
| Restore purchases endpoint | Low | **Defer** to post-MVP |

---

## 1. Price Display from Backend Config

### Current State (Frontend)
The frontend guide hardcodes prices:
```dart
// Section 5.6
"Intimacy all year: $29.99"
"Intimacy all year: $23.99 (was $29.99)"
```

### Opportunity
Backend already stores prices in `app_config`:
```sql
('monthly_price_usd', '4.99')
('annual_price_usd', '29.99')
('promo_discount_percent', '20')
```

### Proposed Backend Enhancement
Add a pricing endpoint:

```
GET /api/subscriptions/pricing
```

Response:
```json
{
  "monthly": {
    "price": 4.99,
    "price_display": "$4.99/month"
  },
  "annual": {
    "price": 29.99,
    "price_display": "$29.99/year",
    "monthly_equivalent": 2.50
  },
  "discounted_monthly": {
    "price": 3.99,
    "price_display": "$3.99/month",
    "original_price": 4.99,
    "discount_percent": 20
  },
  "discounted_annual": {
    "price": 23.99,
    "price_display": "$23.99/year",
    "original_price": 29.99,
    "discount_percent": 20
  }
}
```

### Benefits
- Change prices without app update
- Single source of truth
- A/B testing prices possible

### Recommendation
**Implement this.** Low effort, reduces hardcoding.

---

## 2. Webhook Confirmation Polling

### Current State
Frontend guide (Section 6.2) shows:
1. RevenueCat purchase completes
2. Frontend immediately calls `syncSubscriptionStatus`
3. Hope webhook has arrived

### Potential Issue
Webhook may take 1-5 seconds. Frontend might get stale `free` status.

### Proposed Backend Enhancement
Add polling endpoint:

```
GET /api/subscriptions/await-premium/<user_id>?timeout=10
```

- Polls database every 500ms for up to `timeout` seconds
- Returns immediately when `subscription_tier = 'premium'`
- Returns timeout error if not found

### Alternative
Frontend just waits 2 seconds before sync. Simpler, usually works.

### Recommendation
**Defer.** The 2-second delay approach is simpler and webhook latency is typically under 2 seconds. Only implement if we see real issues.

---

## 3. Pending Promo Code Retrieval

### Current State
Frontend stores promo validation result in page state:
- `promoApplied`
- `discountPercent`
- `appliedOfferingId`

If user navigates away and returns, this state is lost.

### Current Backend State
Backend stores `user.pending_promo_code` which persists.

### Proposed Enhancement
Add endpoint to retrieve pending promo details:

```
GET /api/promo/pending
```

Response (if pending):
```json
{
  "has_pending": true,
  "code": "VANESSA",
  "discount_percent": 20,
  "offering_id": "discounted_20_percent"
}
```

Response (if none):
```json
{
  "has_pending": false
}
```

### Recommendation
**Skip for MVP.** The current flow has user validate promo and immediately purchase on same page. Edge case of navigation away is rare.

---

## 4. Restore Purchases Endpoint

### Current State
Frontend guide mentions "Restore Purchases" as deferred (Appendix B).

RevenueCat handles restore via SDK, but backend doesn't have visibility.

### Proposed Enhancement
Backend endpoint to trigger RevenueCat sync:

```
POST /api/subscriptions/restore
```

This would:
1. Call RevenueCat API to get current entitlements
2. Update user subscription state
3. Return updated status

### Recommendation
**Defer to post-MVP.** RevenueCat SDK handles restore. Only needed if we want backend to proactively sync.

---

## 5. Activity Limit Enforcement Location

### Current State (Correct)
Frontend guide correctly states:
> "Activity Limit Enforcement - Backend handles via game API"

The game API already checks limits before returning activities.

### Verification Needed
Ensure the game/recommendation API:
1. Checks `check-limit` before returning activities
2. Calls `increment-activity` after activity is shown
3. Returns appropriate response when limit reached

### Recommendation
**Verify existing game API handles this.** No new work needed if already implemented.

---

## 6. Subscription Management URLs

### Current State
Frontend hardcodes platform URLs:
```dart
// Section 7.2
iOS: "https://apps.apple.com/account/subscriptions"
Android: "https://play.google.com/store/account/subscriptions"
```

### Proposed Enhancement
Return management URL from status endpoint:

```json
{
  ...existing fields...,
  "management_url": "https://apps.apple.com/account/subscriptions"
}
```

Backend determines URL based on `subscription_platform` field.

### Recommendation
**Nice to have.** Could implement easily, but hardcoding in frontend is also fine since these URLs rarely change.

---

## Implementation Priority

### Do Now (Before Frontend Starts)
1. **Pricing endpoint** - Prevents hardcoded prices

### Do If Issues Arise
2. **Webhook polling** - Only if sync timing is problematic

### Post-MVP
3. **Restore purchases endpoint**
4. **Pending promo retrieval**
5. **Management URL in response**

---

## Current Backend Capabilities (Already Optimal)

These are already well-designed and frontend should use as-is:

| Capability | Backend Endpoint | Notes |
|------------|------------------|-------|
| Promo validation | `POST /api/promo/validate` | Returns offering_id for RevenueCat |
| Subscription status | `GET /api/subscriptions/status/<id>` | Complete state in one call |
| Activity limit check | `GET /api/subscriptions/check-limit/<id>` | Quick boolean check |
| Activity increment | `POST /api/subscriptions/increment-activity/<id>` | Fire-and-forget |
| Webhook processing | `POST /api/webhooks/revenuecat` | Handles all RevenueCat events |

The frontend guide's approach of:
1. Validate promo → get offering_id
2. Purchase via RevenueCat with offering_id
3. Sync status after purchase

...is the correct architecture. No changes needed to the core flow.
