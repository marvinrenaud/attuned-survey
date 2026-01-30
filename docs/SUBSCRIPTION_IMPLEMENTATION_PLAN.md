# Subscription Implementation Plan

> **Complete guide for implementing subscriptions in Attuned**
>
> Last Updated: 2026-01-23

---

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   FlutterFlow   │────────▶│    RevenueCat    │────────▶│  Flask Backend  │
│   (Frontend)    │         │   (Purchases)    │         │   (Webhooks)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌─────────┐    ┌───────────┐    ┌─────────┐
              │  Apple  │    │  Google   │    │ Stripe  │
              │   IAP   │    │   Play    │    │         │
              └─────────┘    └───────────┘    └─────────┘
```

**Key Principle**: Backend is source of truth for subscription state. Frontend reads from backend API, not RevenueCat SDK.

---

## Pricing Structure

| Plan | Regular Price | Discounted (20% off) |
|------|---------------|----------------------|
| Monthly | $4.99/month | $3.99/month |
| Annual | $29.99/year | $23.99/year |

**Free Tier**: 10 lifetime activities (configurable via `app_config.free_tier_activity_limit`)

---

## Backend Implementation Status

### Completed ✅

| Component | Status | Notes |
|-----------|--------|-------|
| Migration 027 | ✅ Applied | Adds subscription columns to users table |
| User model fields | ✅ Done | `subscription_tier`, `lifetime_activity_count`, etc. |
| `/api/subscriptions/status/[user_id]` | ✅ Done | Get subscription state |
| `/api/subscriptions/check-limit/[user_id]` | ✅ Done | Quick limit check |
| `/api/subscriptions/increment-activity/[user_id]` | ✅ Done | Increment activity count |
| `/api/subscriptions/pricing` | ✅ Done | Public pricing endpoint |
| `/api/promo/validate` | ✅ Done | Validate promo codes, returns `offering_id` |
| `/api/webhooks/revenuecat` | ✅ Done | Webhook handler with Bearer auth |
| Gameplay lifetime limits | ✅ Done | Game API uses `lifetime_activity_count` |
| Promo attribution | ✅ Done | Links purchases to influencer codes |

### Environment Variables (Render)

| Variable | Status | Description |
|----------|--------|-------------|
| `REVENUECAT_WEBHOOK_SECRET` | ✅ Set | Bearer token for webhook auth |

---

## RevenueCat Configuration (Required)

### Products to Create

Create these products in **App Store Connect** and **Google Play Console**:

| Product ID | Price | Description |
|------------|-------|-------------|
| `attuned_monthly` | $4.99 | Regular monthly subscription |
| `attuned_annual` | $29.99 | Regular annual subscription |
| `attuned_monthly_discounted` | $3.99 | Discounted monthly (promo codes) |
| `attuned_annual_discounted` | $23.99 | Discounted annual (promo codes) |

### Offerings to Create in RevenueCat

| Offering ID | Products | When Used |
|-------------|----------|-----------|
| `default` | `attuned_monthly`, `attuned_annual` | Normal purchases |
| `discounted_20_percent` | `attuned_monthly_discounted`, `attuned_annual_discounted` | After promo code validated |

### Entitlement

Create one entitlement: `premium_access`

### Webhook Configuration

| Setting | Value |
|---------|-------|
| URL | `https://attuned-backend.onrender.com/api/webhooks/revenuecat` |
| Authorization | Bearer token (same as `REVENUECAT_WEBHOOK_SECRET`) |

---

## Promo Code Approach

**Using Approach 2: Custom Promo Codes with Separate Offerings**

This gives us:
- Influencer attribution tracking
- Backend control over code validity, limits, expiration
- Consistent behavior across all platforms

**Flow:**
```
1. User enters promo code "VANESSA"
2. Frontend calls POST /api/promo/validate
3. Backend returns { offering_id: "discounted_20_percent", ... }
4. Frontend calls RevenueCat.purchase() with that offering_id
5. RevenueCat presents $3.99/$23.99 products (from discounted offering)
6. User purchases
7. RevenueCat sends webhook to backend
8. Backend sees pending_promo_code, creates attribution record
```

**NOT using platform-native offers** because they don't support influencer attribution.

---

## Frontend Implementation (FlutterFlow)

### RevenueCat SDK Setup

1. Add RevenueCat Flutter SDK to project
2. Configure API keys:
   - iOS: `appl_xxxxx`
   - Android: `goog_xxxxx`

### Critical: User Identification

**When**: On purchase page (before presenting products)

**Why**: RevenueCat needs to know the user ID to include it in webhooks

```dart
// Call this before presenting purchase UI
await Purchases.logIn(currentUserUid);
```

### API Calls (FlutterFlow Syntax)

| Endpoint | Path Parameter |
|----------|----------------|
| `/api/subscriptions/status/[user_id]` | Use `[user_id]` not `<user_id>` |
| `/api/subscriptions/check-limit/[user_id]` | Use `[user_id]` not `<user_id>` |
| `/api/subscriptions/pricing` | None (public) |
| `/api/promo/validate` | None (POST body) |

### No CORS Proxy Needed

Backend has CORS configured for FlutterFlow origins. Call directly:
```
https://attuned-backend.onrender.com/api/...
```

---

## Integration Flows

### Flow 1: Normal Purchase (No Promo Code)

```
1. User navigates to SubscriptionIntroPage
2. Frontend: GET /api/subscriptions/pricing → display prices
3. Frontend: Purchases.logIn(userId)
4. Frontend: Get offerings, present "default" offering products
5. User taps "Subscribe"
6. RevenueCat processes payment
7. RevenueCat sends INITIAL_PURCHASE webhook → Backend updates user
8. Frontend: Wait 2 seconds
9. Frontend: GET /api/subscriptions/status/[user_id]
10. Frontend: Update app state, navigate to success
```

### Flow 2: Purchase with Promo Code

```
1. User navigates to SubscriptionIntroPage
2. Frontend: GET /api/subscriptions/pricing → display regular prices
3. User enters promo code, taps "Apply"
4. Frontend: POST /api/promo/validate { code: "VANESSA" }
5. Backend: Returns { valid: true, offering_id: "discounted_20_percent", discount_percent: 20 }
6. Frontend: Show discounted prices, store offering_id
7. Frontend: Purchases.logIn(userId)
8. Frontend: Get offerings, present "discounted_20_percent" offering products
9. User taps "Subscribe"
10. RevenueCat processes payment at discounted price
11. RevenueCat sends webhook → Backend updates user + attributes promo
12. Frontend: Wait 2 seconds
13. Frontend: GET /api/subscriptions/status/[user_id]
14. Frontend: Update app state (promo_code_used will be set)
```

### Flow 3: App Launch Sync

```
1. App launches, user authenticated
2. Frontend: GET /api/subscriptions/status/[user_id]
3. Frontend: Update isPremium, activitiesRemaining in app state
4. Frontend: Show appropriate UI based on subscription status
```

### Flow 4: Game with Limit Enforcement

```
1. User taps "Play"
2. Game API internally checks lifetime_activity_count
3. If limit reached: Returns LIMIT_REACHED card type
4. Frontend: Shows upgrade prompt
5. If under limit: Returns normal activity card
6. Game API automatically increments count for free users
```

---

## Testing Checklist

### Backend Testing (Done ✅)
- [x] 320+ tests passing
- [x] Subscription status endpoint
- [x] Activity limit endpoints
- [x] Promo validation
- [x] Webhook handler
- [x] Gameplay limit enforcement

### RevenueCat Testing (TODO)
- [ ] Products created in App Store Connect
- [ ] Products created in Google Play Console
- [ ] Offerings configured in RevenueCat
- [ ] Webhook URL configured
- [ ] Sandbox purchase test (iOS)
- [ ] Sandbox purchase test (Android)

### Frontend Testing (TODO)
- [ ] Pricing endpoint integration
- [ ] Subscription status display
- [ ] Promo code validation flow
- [ ] Purchase flow (normal)
- [ ] Purchase flow (with promo)
- [ ] Post-purchase status sync
- [ ] Limit reached UI

---

## Troubleshooting

### 403 on subscription endpoints
- Check JWT token is valid and not expired
- Verify user_id in URL matches token's `sub` claim
- FlutterFlow: Use `[user_id]` syntax, not `<user_id>`

### Webhook not updating user
- Check `REVENUECAT_WEBHOOK_SECRET` is set on Render
- Verify webhook URL in RevenueCat dashboard
- Check Render logs for webhook errors

### Promo code not attributed
- Ensure `/api/promo/validate` is called BEFORE purchase
- Check `pending_promo_code` is set on user
- Verify webhook includes correct `app_user_id`

### User shows as free after purchase
- Webhook may have 1-5 second delay
- Wait 2 seconds before calling `/status`
- Check RevenueCat dashboard for webhook delivery status

---

## Related Documentation

- `docs/BACKEND_SUBSCRIPTION_HANDSHAKE.md` - Detailed API reference for frontend
- `docs/SUBSCRIPTION_SIMPLIFICATION_OPPORTUNITIES.md` - Future simplification ideas
- `.claude/skills/attuned-payments/SKILL.md` - Payment patterns and code examples
