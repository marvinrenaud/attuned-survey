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

### Users Table Updates

```sql
-- Add to existing users table
ALTER TABLE users ADD COLUMN subscription_platform TEXT; -- 'stripe' | 'apple' | 'google'
ALTER TABLE users ADD COLUMN subscription_product_id TEXT;
ALTER TABLE users ADD COLUMN revenuecat_app_user_id TEXT;
ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN lifetime_activity_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN promo_code_used TEXT;
```

### App Config Updates

```sql
INSERT INTO app_config (key, value) VALUES
  ('free_tier_activity_limit', '10'),
  ('monthly_price_usd', '4.99'),
  ('annual_price_usd', '29.99'),
  ('promo_discount_percent', '20');
```

### Promo Code Tables

```sql
-- Influencers table
CREATE TABLE influencers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  platform TEXT,  -- 'tiktok', 'instagram', 'podcast', 'youtube'
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'inactive')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Promo codes table
CREATE TABLE promo_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  influencer_id UUID REFERENCES influencers(id) ON DELETE CASCADE,
  code TEXT UNIQUE NOT NULL,  -- 'VANESSA', 'TODDBARATZ', 'FOREPLAY'
  discount_percent INTEGER DEFAULT 20,
  offering_id TEXT NOT NULL,  -- RevenueCat offering identifier
  is_active BOOLEAN DEFAULT true,
  max_redemptions INTEGER,  -- NULL = unlimited
  current_redemptions INTEGER DEFAULT 0,
  expires_at TIMESTAMPTZ,  -- NULL = never expires
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_promo_codes_lookup ON promo_codes(UPPER(code)) WHERE is_active = true;

-- Code redemptions table
CREATE TABLE code_redemptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  promo_code_id UUID REFERENCES promo_codes(id),
  user_id UUID NOT NULL,
  revenuecat_app_user_id TEXT,
  device_platform TEXT,  -- 'ios' or 'android'
  redeemed_at TIMESTAMPTZ DEFAULT NOW(),
  converted_at TIMESTAMPTZ,  -- Set when subscription purchase confirmed
  UNIQUE(user_id)  -- One promo code per user ever
);

-- Helper function
CREATE OR REPLACE FUNCTION increment_promo_usage(code_id UUID)
RETURNS void AS $$
BEGIN
  UPDATE promo_codes 
  SET current_redemptions = current_redemptions + 1, updated_at = NOW()
  WHERE id = code_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Flask Backend Routes

### File: `backend/src/routes/promo.py`

```python
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from ..extensions import db
from ..middleware.auth import token_required

promo_bp = Blueprint('promo', __name__, url_prefix='/api/promo')

@promo_bp.route('/validate', methods=['POST'])
@token_required
def validate_promo(current_user_id):
    """
    POST /api/promo/validate
    Body: { "code": "VANESSA" }
    Returns: { "valid": true, "offering_id": "discounted_20_percent", ... }
    """
    data = request.get_json()
    code = data.get('code', '').upper().strip()
    
    if not code:
        return jsonify({'valid': False, 'error': 'No code provided'}), 400
    
    # Check if user already redeemed any code
    existing = db.session.execute(
        "SELECT id FROM code_redemptions WHERE user_id = :user_id",
        {'user_id': str(current_user_id)}
    ).fetchone()
    
    if existing:
        return jsonify({'valid': False, 'error': 'You have already used a promo code'})
    
    # Look up promo code with influencer info
    result = db.session.execute("""
        SELECT pc.id, pc.code, pc.discount_percent, pc.offering_id,
               pc.max_redemptions, pc.current_redemptions, pc.expires_at,
               i.name as influencer_name
        FROM promo_codes pc
        JOIN influencers i ON pc.influencer_id = i.id
        WHERE UPPER(pc.code) = :code AND pc.is_active = true AND i.status = 'active'
    """, {'code': code}).fetchone()
    
    if not result:
        return jsonify({'valid': False, 'error': 'Invalid promo code'})
    
    # Check expiration
    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        return jsonify({'valid': False, 'error': 'This code has expired'})
    
    # Check usage limits
    if result.max_redemptions and result.current_redemptions >= result.max_redemptions:
        return jsonify({'valid': False, 'error': 'This code has reached its redemption limit'})
    
    return jsonify({
        'valid': True,
        'offering_id': result.offering_id,
        'discount_percent': result.discount_percent,
        'influencer_name': result.influencer_name,
        'promo_code_id': str(result.id)
    })

@promo_bp.route('/redeem', methods=['POST'])
@token_required
def record_redemption(current_user_id):
    """
    POST /api/promo/redeem
    Body: { "promo_code_id": "uuid", "revenuecat_app_user_id": "rc_id", "platform": "ios" }
    """
    data = request.get_json()
    promo_code_id = data.get('promo_code_id')
    rc_user_id = data.get('revenuecat_app_user_id')
    platform = data.get('platform', 'unknown')
    
    if not promo_code_id:
        return jsonify({'success': False, 'error': 'Missing promo_code_id'}), 400
    
    try:
        result = db.session.execute("""
            INSERT INTO code_redemptions (promo_code_id, user_id, revenuecat_app_user_id, device_platform)
            VALUES (:promo_code_id, :user_id, :rc_user_id, :platform)
            RETURNING id
        """, {
            'promo_code_id': promo_code_id,
            'user_id': str(current_user_id),
            'rc_user_id': rc_user_id,
            'platform': platform
        })
        redemption_id = result.fetchone()[0]
        
        db.session.execute("SELECT increment_promo_usage(:code_id)", {'code_id': promo_code_id})
        db.session.commit()
        
        return jsonify({'success': True, 'redemption_id': str(redemption_id)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Could not record redemption'}), 400

@promo_bp.route('/confirm-conversion', methods=['POST'])
@token_required
def confirm_conversion(current_user_id):
    """
    POST /api/promo/confirm-conversion
    Body: { "redemption_id": "uuid" }
    """
    data = request.get_json()
    redemption_id = data.get('redemption_id')
    
    if not redemption_id:
        return jsonify({'success': False, 'error': 'Missing redemption_id'}), 400
    
    db.session.execute("""
        UPDATE code_redemptions SET converted_at = NOW()
        WHERE id = :redemption_id AND user_id = :user_id AND converted_at IS NULL
    """, {'redemption_id': redemption_id, 'user_id': str(current_user_id)})
    db.session.commit()
    
    return jsonify({'success': True})
```

### File: `backend/src/routes/subscriptions.py`

```python
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..middleware.auth import token_required
import hmac
import hashlib

subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')

@subscriptions_bp.route('/status/<user_id>', methods=['GET'])
@token_required
def get_status(current_user_id, user_id):
    """
    GET /api/subscriptions/status/{user_id}
    Returns subscription state for the app
    """
    # Verify ownership
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    user = db.session.execute("""
        SELECT subscription_tier, subscription_expires_at, lifetime_activity_count
        FROM users WHERE id = :user_id
    """, {'user_id': user_id}).fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get activity limit from config
    config = db.session.execute(
        "SELECT value FROM app_config WHERE key = 'free_tier_activity_limit'"
    ).fetchone()
    limit = int(config.value) if config else 10
    
    return jsonify({
        'subscription_tier': user.subscription_tier or 'free',
        'expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        'activities_used': user.lifetime_activity_count or 0,
        'activities_limit': limit if user.subscription_tier != 'premium' else None,
        'activities_remaining': max(0, limit - (user.lifetime_activity_count or 0)) if user.subscription_tier != 'premium' else None
    })

@subscriptions_bp.route('/check-limit/<user_id>', methods=['GET'])
@token_required
def check_limit(current_user_id, user_id):
    """
    GET /api/subscriptions/check-limit/{user_id}
    Check if free user has activities remaining
    """
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    user = db.session.execute("""
        SELECT subscription_tier, lifetime_activity_count FROM users WHERE id = :user_id
    """, {'user_id': user_id}).fetchone()
    
    if user.subscription_tier == 'premium':
        return jsonify({'has_limit': False, 'can_play': True})
    
    config = db.session.execute(
        "SELECT value FROM app_config WHERE key = 'free_tier_activity_limit'"
    ).fetchone()
    limit = int(config.value) if config else 10
    used = user.lifetime_activity_count or 0
    
    return jsonify({
        'has_limit': True,
        'can_play': used < limit,
        'activities_used': used,
        'activities_limit': limit,
        'activities_remaining': max(0, limit - used)
    })
```

### File: `backend/src/routes/webhooks.py`

```python
from flask import Blueprint, request, jsonify
from ..extensions import db
import hmac
import hashlib
import os

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

REVENUECAT_WEBHOOK_SECRET = os.getenv('REVENUECAT_WEBHOOK_SECRET')

def verify_revenuecat_signature(payload, signature):
    """Verify RevenueCat webhook signature"""
    expected = hmac.new(
        REVENUECAT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@webhooks_bp.route('/revenuecat', methods=['POST'])
def revenuecat_webhook():
    """
    POST /api/webhooks/revenuecat
    Handles subscription lifecycle events from RevenueCat
    
    Events:
    - INITIAL_PURCHASE: New subscription created
    - RENEWAL: Subscription renewed successfully
    - CANCELLATION: User cancelled (access until period end)
    - EXPIRATION: Subscription ended, revoke access
    - BILLING_ISSUE: Payment failed, send in-app notification
    - PRODUCT_CHANGE: User upgraded/downgraded plan
    """
    # Verify signature
    signature = request.headers.get('X-RevenueCat-Signature', '')
    if REVENUECAT_WEBHOOK_SECRET and not verify_revenuecat_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    data = request.get_json()
    event_type = data.get('event', {}).get('type')
    app_user_id = data.get('event', {}).get('app_user_id')
    product_id = data.get('event', {}).get('product_id')
    expiration = data.get('event', {}).get('expiration_at_ms')
    
    if not app_user_id:
        return jsonify({'error': 'Missing app_user_id'}), 400
    
    # Map RevenueCat events to actions
    if event_type == 'INITIAL_PURCHASE':
        db.session.execute("""
            UPDATE users SET 
                subscription_tier = 'premium',
                subscription_product_id = :product_id,
                subscription_expires_at = to_timestamp(:expiration / 1000.0)
            WHERE revenuecat_app_user_id = :rc_id OR id::text = :rc_id
        """, {'product_id': product_id, 'expiration': expiration, 'rc_id': app_user_id})
        
    elif event_type == 'RENEWAL':
        db.session.execute("""
            UPDATE users SET subscription_expires_at = to_timestamp(:expiration / 1000.0)
            WHERE revenuecat_app_user_id = :rc_id OR id::text = :rc_id
        """, {'expiration': expiration, 'rc_id': app_user_id})
        
    elif event_type == 'EXPIRATION':
        db.session.execute("""
            UPDATE users SET subscription_tier = 'free'
            WHERE revenuecat_app_user_id = :rc_id OR id::text = :rc_id
        """, {'rc_id': app_user_id})
        
    elif event_type == 'CANCELLATION':
        # User cancelled but still has access until expiration
        pass  # No action needed, will expire naturally
        
    elif event_type == 'BILLING_ISSUE':
        # TODO: Send in-app notification about payment issue
        pass
    
    db.session.commit()
    return jsonify({'success': True})
```

## RevenueCat Configuration

### Offerings Setup

| Offering ID | Products | Use Case |
|-------------|----------|----------|
| `default` | attuned_monthly ($4.99), attuned_annual ($29.99) | Standard pricing |
| `discounted_20_percent` | attuned_monthly_discounted ($3.99), attuned_annual_discounted ($23.99) | Promo code users |

### Subscriber Attributes for Attribution

```dart
await Purchases.setAttributes({
  'promo_code': 'VANESSA',
  'influencer': 'Vanessa Marin',
  '\$mediaSource': 'influencer_promo',
  '\$campaign': 'Vanessa Marin',
});
```

## FlutterFlow Custom Actions

### 1. validatePromoCode

```dart
Future<PromoValidationResult> validatePromoCode(String code) async {
  final response = await http.post(
    Uri.parse('https://attuned-backend.onrender.com/api/promo/validate'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $currentJwtToken',
    },
    body: jsonEncode({'code': code}),
  );
  final data = jsonDecode(response.body);
  return PromoValidationResult(
    valid: data['valid'] ?? false,
    error: data['error'],
    offeringId: data['offering_id'],
    discountPercent: data['discount_percent'],
    influencerName: data['influencer_name'],
    promoCodeId: data['promo_code_id'],
  );
}
```

### 2. detectUserRegion

```dart
Future<bool> isUSUser() async {
  // iOS: SKStorefront.countryCode
  // Android: BillingClient country
  // Returns true for US users (external payments)
  // Returns false for non-US (use IAP)
}
```

### 3. setPromoAttribution

```dart
Future<void> setPromoAttribution(String promoCode, String influencerName) async {
  await Purchases.setAttributes({
    'promo_code': promoCode,
    'influencer': influencerName,
    '\$mediaSource': 'influencer_promo',
    '\$campaign': influencerName,
  });
}
```

## Vendor Account Setup Checklist

### RevenueCat
1. Create account at revenuecat.com
2. Create project 'Attuned'
3. Add iOS app (bundle ID + App Store Connect)
4. Add Android app (package name + Play Console)
5. Connect Stripe account
6. Create Entitlement: `premium_access`
7. Create Products: `attuned_monthly`, `attuned_annual`, `attuned_monthly_discounted`, `attuned_annual_discounted`
8. Create Offerings: `default`, `discounted_20_percent`
9. Configure webhook URL: `https://attuned-backend.onrender.com/api/webhooks/revenuecat`
10. Save webhook signing secret to Render env

### Stripe
1. Create/access Stripe account
2. Complete business verification
3. Create Products and Prices (standard + discounted)
4. Enable Apple Pay and Google Pay
5. Configure Customer Portal
6. Connect to RevenueCat

### Apple App Store Connect
1. Create Subscription Group: 'Attuned Premium'
2. Create subscriptions: `attuned_monthly_499`, `attuned_annual_2999`
3. Create discounted: `attuned_monthly_399`, `attuned_annual_2399`
4. **CRITICAL**: Apply for External Purchase Link Entitlement (US)
   - URL: developer.apple.com/contact/request/storekit-external-entitlement-us
   - Takes 1-2 weeks for approval

### Google Play Console
1. Create subscriptions with base plans
2. Create license testers for sandbox
3. Generate service account credentials for RevenueCat

## Influencer Performance Query

```sql
SELECT 
  i.name AS influencer,
  i.platform,
  pc.code,
  COUNT(cr.id) AS total_redemptions,
  COUNT(cr.converted_at) AS conversions,
  ROUND(100.0 * COUNT(cr.converted_at) / NULLIF(COUNT(cr.id), 0), 1) AS conversion_rate_percent
FROM influencers i
JOIN promo_codes pc ON i.id = pc.influencer_id
LEFT JOIN code_redemptions cr ON pc.id = cr.promo_code_id
GROUP BY i.id, i.name, i.platform, pc.code
ORDER BY conversions DESC;
```

## Testing Checklist

- [ ] US user subscribes monthly with card
- [ ] US user subscribes annual with Apple Pay
- [ ] US user subscribes with promo code
- [ ] Non-US user subscribes via Apple IAP
- [ ] Non-US user subscribes via Google Play
- [ ] User upgrades monthly to annual
- [ ] User cancels subscription (verify access until expiry)
- [ ] User with expired card gets billing issue notification
- [ ] User reinstalls app and subscription restores
- [ ] Free user hits activity limit
- [ ] Promo code validation errors (expired, invalid, used)
- [ ] Webhook retry after temporary backend failure

## Environment Variables

```bash
# Render (Flask backend)
REVENUECAT_WEBHOOK_SECRET=rc_webhook_secret_here
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# FlutterFlow
REVENUECAT_IOS_API_KEY=appl_xxx
REVENUECAT_ANDROID_API_KEY=goog_xxx
```

## Implementation Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| 1. Foundation | Vendor accounts, DB migrations, deploy webhooks | Days 1-2 |
| 2. Backend | Webhook handlers, promo endpoints, status APIs | Days 3-4 |
| 3. Frontend | RevenueCat SDK, custom actions, payment UI | Days 5-7 |
| 4. Testing | All platforms, promo codes, edge cases | Days 8-9 |
| 5. Launch | Live mode, TestFlight, App Store submission | Day 10 |

**Total: 35-50 hours (~5-7 working days)**

Note: Apple External Payment Entitlement approval is outside your control (1-2 weeks). Develop with IAP as fallback.
