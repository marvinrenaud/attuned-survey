-- Migration 027: Subscription Enhancements for RevenueCat Integration
-- Adds influencers, promo_codes, promo_redemptions tables
-- Adds subscription tracking columns to users table

-- ============================================
-- 1. Users Table: Add subscription tracking columns
-- ============================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_platform TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_product_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS revenuecat_app_user_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS lifetime_activity_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_promo_code TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS promo_code_used TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_cancelled_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_issue_detected_at TIMESTAMPTZ;

-- Zero out existing free users for fresh start with lifetime model
UPDATE users SET lifetime_activity_count = 0 WHERE subscription_tier = 'free';

-- ============================================
-- 2. Influencers Table (NEW)
-- ============================================
CREATE TABLE IF NOT EXISTS influencers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    platform TEXT,  -- 'tiktok', 'instagram', 'podcast', 'youtube'
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'inactive')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: service role only (no client access)
ALTER TABLE influencers ENABLE ROW LEVEL SECURITY;
-- No policies - service role bypasses RLS automatically

-- ============================================
-- 3. Promo Codes Table (NEW)
-- ============================================
CREATE TABLE IF NOT EXISTS promo_codes (
    id SERIAL PRIMARY KEY,
    influencer_id INTEGER REFERENCES influencers(id) ON DELETE SET NULL,
    code TEXT UNIQUE NOT NULL,
    discount_percent INTEGER DEFAULT 20,
    stripe_coupon_id TEXT,
    revenuecat_offering_id TEXT DEFAULT 'discounted_20_percent',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ,
    max_redemptions INTEGER,
    redemption_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promo_codes_code ON promo_codes(UPPER(code));
CREATE INDEX IF NOT EXISTS idx_promo_codes_active ON promo_codes(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_promo_codes_influencer ON promo_codes(influencer_id);

-- RLS: service role only (no client access)
ALTER TABLE promo_codes ENABLE ROW LEVEL SECURITY;
-- No policies - service role bypasses RLS automatically

-- ============================================
-- 4. Promo Redemptions Table (NEW)
-- ============================================
CREATE TABLE IF NOT EXISTS promo_redemptions (
    id SERIAL PRIMARY KEY,
    promo_code_id INTEGER REFERENCES promo_codes(id),
    user_id UUID REFERENCES users(id),
    subscription_product TEXT,
    original_price DECIMAL(10,2),
    discounted_price DECIMAL(10,2),
    redeemed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_promo_redemptions_user ON promo_redemptions(user_id);
CREATE INDEX IF NOT EXISTS idx_promo_redemptions_code ON promo_redemptions(promo_code_id);

-- RLS: users read their own only, service role writes
ALTER TABLE promo_redemptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY promo_redemptions_select_own ON promo_redemptions
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

-- ============================================
-- 5. App Config: Seed subscription settings
-- ============================================
INSERT INTO app_config (key, value, description) VALUES
    ('free_tier_activity_limit', '10', 'Lifetime activities for free users before subscription required')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_config (key, value, description) VALUES
    ('monthly_price_usd', '4.99', 'Monthly subscription price in USD')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_config (key, value, description) VALUES
    ('annual_price_usd', '29.99', 'Annual subscription price in USD')
ON CONFLICT (key) DO NOTHING;
