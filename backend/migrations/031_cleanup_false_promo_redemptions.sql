-- Migration: Clean up false promo redemptions
-- These are redemptions recorded when user had pending promo code
-- but purchased a non-discounted product (paid full price)
--
-- Issue: Users were blocked from re-using promo codes even though
-- they never actually received the discount.

BEGIN;

-- First, clear promo_code_used for affected users
UPDATE users
SET promo_code_used = NULL
WHERE id IN (
    SELECT DISTINCT user_id
    FROM promo_redemptions
    WHERE subscription_product IS NOT NULL
    AND subscription_product NOT LIKE '%discounted%'
);

-- Then delete the false redemption records
DELETE FROM promo_redemptions
WHERE subscription_product IS NOT NULL
AND subscription_product NOT LIKE '%discounted%';

-- Update redemption counts on promo_codes to be accurate
UPDATE promo_codes pc
SET redemption_count = (
    SELECT COUNT(*)
    FROM promo_redemptions pr
    WHERE pr.promo_code_id = pc.id
);

COMMIT;
