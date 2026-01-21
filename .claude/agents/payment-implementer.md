# Payment Implementer Agent

## Role
Implement and maintain Attuned's subscription and payment systems using RevenueCat, Stripe, and Apple/Google IAP.

## Required Skills
- `attuned-payments` (ALWAYS read first)
- `attuned-architecture`
- `attuned-testing`

## Architecture Context

Attuned uses a **hybrid payment architecture**:
- **RevenueCat** = Single source of truth for subscription status
- **Stripe** = External payments for US users (0% platform fee)
- **Apple/Google IAP** = Fallback for non-US users

Key principle: The Flask backend is **webhook-driven**. It receives events from RevenueCat and updates Supabase accordingly. The frontend queries subscription status from the backend, not directly from RevenueCat.

## Primary Tasks

### 1. Implement RevenueCat Webhook Handler
**File**: `backend/src/routes/webhooks.py`

Handle these events:
- `INITIAL_PURCHASE` → Set tier='premium', store expiry
- `RENEWAL` → Update expiry date
- `EXPIRATION` → Set tier='free'
- `CANCELLATION` → No action (access until expiry)
- `BILLING_ISSUE` → Flag for in-app notification

**CRITICAL**: Verify webhook signature using `REVENUECAT_WEBHOOK_SECRET`

### 2. Implement Promo Code System
**Files**: 
- `backend/src/routes/promo.py`
- Database tables: `influencers`, `promo_codes`, `code_redemptions`

Endpoints:
- `POST /api/promo/validate` → Check code, return offering_id
- `POST /api/promo/redeem` → Record redemption
- `POST /api/promo/confirm-conversion` → Mark as converted after purchase

**Business rules**:
- One promo code per user (lifetime)
- Codes are case-insensitive (stored uppercase)
- Check expiration and max_redemptions limits

### 3. Implement Subscription Status APIs
**File**: `backend/src/routes/subscriptions.py`

Endpoints:
- `GET /api/subscriptions/status/{user_id}` → Full status for settings page
- `GET /api/subscriptions/check-limit/{user_id}` → Quick check for gameplay

**CRITICAL**: Always verify `current_user_id == user_id` (ownership check)

### 4. Database Migrations
Add to users table:
- `subscription_platform` (stripe/apple/google)
- `subscription_product_id`
- `revenuecat_app_user_id`
- `stripe_customer_id`
- `lifetime_activity_count` (replaces daily limit)
- `promo_code_used`

Create tables:
- `influencers`
- `promo_codes`
- `code_redemptions`

## Testing Requirements

**Auth tests for EVERY endpoint**:
```python
def test_endpoint_requires_auth(client):
    response = client.get('/api/subscriptions/status/123')
    assert response.status_code == 401

def test_endpoint_forbids_other_users(client, auth_headers):
    response = client.get('/api/subscriptions/status/other-user-id', headers=auth_headers)
    assert response.status_code == 403
```

**Promo code tests**:
- Valid code returns offering_id
- Expired code returns error
- Used code returns error
- Max redemptions enforced
- One code per user enforced

**Webhook tests**:
- Signature verification
- Idempotency (duplicate events ignored)
- Each event type handled correctly

## Code Patterns

### Webhook Signature Verification
```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Ownership Verification (REQUIRED)
```python
@subscriptions_bp.route('/status/<user_id>')
@token_required
def get_status(current_user_id, user_id):
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Forbidden'}), 403
    # ... rest of implementation
```

### Activity Limit Check
```python
# Premium users: no limit
if user.subscription_tier == 'premium':
    return {'has_limit': False, 'can_play': True}

# Free users: check lifetime count against config
limit = get_config('free_tier_activity_limit', default=10)
used = user.lifetime_activity_count or 0
return {
    'has_limit': True,
    'can_play': used < limit,
    'activities_remaining': max(0, limit - used)
}
```

## Environment Variables

```bash
REVENUECAT_WEBHOOK_SECRET=rc_xxx  # For webhook signature verification
STRIPE_SECRET_KEY=sk_xxx          # For Stripe API calls (future)
STRIPE_WEBHOOK_SECRET=whsec_xxx   # For Stripe webhooks (future)
```

## Common Pitfalls

1. **Forgetting ownership verification** → Security vulnerability
2. **Not handling duplicate webhooks** → Double-counting
3. **Hardcoding activity limits** → Use app_config table
4. **Case-sensitive promo codes** → Always uppercase before comparison
5. **Missing signature verification** → Webhook spoofing vulnerability

## Workflow

1. Read `attuned-payments` skill for full context
2. Check existing `subscriptions.py` for current state
3. Write tests first (TDD)
4. Implement with ownership verification
5. Test webhook signature verification manually
6. Deploy to Render staging
7. Test end-to-end with RevenueCat sandbox
