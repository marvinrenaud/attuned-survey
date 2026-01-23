-- Rollback Migration 027: Subscription Enhancements
-- WARNING: This will drop tables and remove columns

-- Remove RLS policy first
DROP POLICY IF EXISTS promo_redemptions_select_own ON promo_redemptions;

-- Drop tables in reverse order (respect foreign keys)
DROP TABLE IF EXISTS promo_redemptions;
DROP TABLE IF EXISTS promo_codes;
DROP TABLE IF EXISTS influencers;

-- Remove user columns
ALTER TABLE users DROP COLUMN IF EXISTS subscription_platform;
ALTER TABLE users DROP COLUMN IF EXISTS subscription_product_id;
ALTER TABLE users DROP COLUMN IF EXISTS revenuecat_app_user_id;
ALTER TABLE users DROP COLUMN IF EXISTS stripe_customer_id;
ALTER TABLE users DROP COLUMN IF EXISTS lifetime_activity_count;
ALTER TABLE users DROP COLUMN IF EXISTS pending_promo_code;
ALTER TABLE users DROP COLUMN IF EXISTS promo_code_used;
ALTER TABLE users DROP COLUMN IF EXISTS subscription_cancelled_at;
ALTER TABLE users DROP COLUMN IF EXISTS billing_issue_detected_at;

-- Remove app_config entries
DELETE FROM app_config WHERE key IN (
    'free_tier_activity_limit',
    'monthly_price_usd',
    'annual_price_usd'
);
