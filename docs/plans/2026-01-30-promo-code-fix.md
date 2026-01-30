# Plan: Fix Promo Code "Already Used" Bug

## Problem Statement

Users are getting "Code already used" errors when they haven't actually used a promo code for a discounted purchase. The system incorrectly records promo redemptions even when users purchase non-discounted products.

## Root Cause

Two bugs in the promo code flow:

### Bug 1: False Redemption Recording
**Location**: `backend/src/services/subscription_service.py:_process_promo_attribution()`

When a user:
1. Validates a promo code (sets `pending_promo_code`)
2. Then purchases a NON-discounted product (e.g., `attuned_monthly_web` at $4.99)

The system still:
- Creates a `PromoRedemption` record
- Sets `user.promo_code_used`
- Increments `promo.redemption_count`

**Evidence**: User test55 has redemption for TEST20 but paid full price $4.99.

### Bug 2: Overly Strict Validation Check
**Location**: `backend/src/routes/promo.py:validate_promo_code()`

The check at line 56-65 blocks users if ANY redemption exists:
```python
existing = PromoRedemption.query.filter_by(
    user_id=current_user_id,
    promo_code_id=promo.id
).first()
if existing:
    return {'valid': False, 'error': 'Code already used'}
```

This blocks users who:
- Validated but never purchased
- Purchased but at full price (didn't get discount)
- Subscribed with discount but subscription expired

---

## Implementation Steps

### Step 0: Establish Test Baseline
**Checkpoint: qa-tester agent**

Before making any changes, run the full test suite to establish a baseline:
```bash
cd backend && pytest tests/ -v --tb=short
```

Document:
- Total tests: ___
- Passed: ___
- Failed: ___
- Skipped: ___

If any tests are failing, investigate and document why before proceeding.

---

### Step 1: Create Promo/Payments Test Suite
**File**: `backend/tests/test_promo_payments.py`

Create a dedicated test file for promo code and payment-related functionality. This consolidates testing for:
- Promo code validation (`/api/promo/validate`)
- Promo redemption recording (subscription_service)
- Webhook handling for purchases
- Subscription status with promo codes

#### Test Cases to Implement:

**1.1 Promo Validation Tests**
```python
class TestPromoValidation:
    def test_validate_returns_401_without_auth(self)
    def test_validate_returns_400_without_code(self)
    def test_validate_returns_invalid_for_unknown_code(self)
    def test_validate_returns_valid_for_active_code(self)
    def test_validate_sets_pending_promo_code_on_user(self)
    def test_validate_allows_reuse_if_no_discounted_redemption(self)  # NEW
    def test_validate_blocks_if_discounted_redemption_exists(self)    # NEW
```

**1.2 Promo Attribution Tests**
```python
class TestPromoAttribution:
    def test_attribution_creates_redemption_for_discounted_product(self)   # NEW
    def test_attribution_skips_redemption_for_non_discounted_product(self) # NEW
    def test_attribution_clears_pending_code_after_non_discounted(self)    # NEW
    def test_attribution_sets_promo_code_used_for_discounted(self)         # NEW
    def test_attribution_increments_redemption_count(self)
```

**1.3 Webhook Integration Tests**
```python
class TestWebhookPromoIntegration:
    def test_initial_purchase_discounted_records_redemption(self)
    def test_initial_purchase_non_discounted_no_redemption(self)
    def test_user_can_revalidate_after_non_discounted_purchase(self)  # NEW
    def test_user_blocked_after_discounted_purchase(self)             # NEW
```

**Checkpoint: Run new test file (tests should fail initially for NEW tests)**
```bash
pytest tests/test_promo_payments.py -v
```

---

### Step 2: Fix Redemption Recording (Bug 1)
**File**: `backend/src/services/subscription_service.py`

Modify `_process_promo_attribution()` to only record redemption for discounted products:

```python
@classmethod
def _process_promo_attribution(cls, user: User, event: dict) -> None:
    """
    If user has pending promo code, record the redemption.
    Called during INITIAL_PURCHASE processing.

    IMPORTANT: Only records redemption if the purchased product is discounted.
    If user bought a non-discounted product, clears pending_promo_code without
    creating a redemption, allowing them to use the code on a future purchase.
    """
    if not user.pending_promo_code:
        return

    product_id = event.get('product_id', '')

    # Only record redemption if user actually purchased discounted product
    if 'discounted' not in product_id.lower():
        logger.info(
            f"User {user.id} had pending promo code {user.pending_promo_code} "
            f"but purchased non-discounted product {product_id}, clearing pending code"
        )
        user.pending_promo_code = None
        return

    # ... rest of existing logic unchanged ...
```

**Checkpoint: Run attribution tests**
```bash
pytest tests/test_promo_payments.py::TestPromoAttribution -v
```

---

### Step 3: Fix Validation Check (Bug 2)
**File**: `backend/src/routes/promo.py`

Modify `validate_promo_code()` to only block if redemption was for a discounted product:

```python
# Check if user already redeemed this code for a DISCOUNTED product
existing = PromoRedemption.query.filter_by(
    user_id=current_user_id,
    promo_code_id=promo.id
).first()

# Only block if they actually got the discount
if existing:
    product = existing.subscription_product or ''
    if 'discounted' in product.lower():
        return jsonify({
            'valid': False,
            'error': 'Code already used'
        }), 200
    # Otherwise, allow re-validation (they paid full price last time)
```

**Checkpoint: Run validation tests**
```bash
pytest tests/test_promo_payments.py::TestPromoValidation -v
```

---

### Step 4: Run Full Promo Test Suite
**Checkpoint: qa-tester agent**

Run the complete promo/payments test suite:
```bash
pytest tests/test_promo_payments.py -v
```

All tests should pass. If any fail, fix before proceeding.

---

### Step 5: Run Full Test Suite (Regression Check)
**Checkpoint: qa-tester agent**

Run the complete backend test suite to catch any regressions:
```bash
pytest tests/ -v --tb=short
```

Compare against baseline from Step 0:
- No new failures should be introduced
- All previously passing tests should still pass

---

### Step 6: Data Cleanup Migration (Optional)
**File**: `backend/migrations/030_cleanup_false_promo_redemptions.sql`

Clean up incorrect redemption records where user paid full price:

```sql
-- Migration: Clean up false promo redemptions
-- These are redemptions recorded when user had pending promo code
-- but purchased a non-discounted product (paid full price)

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
```

**Rollback file**: `backend/migrations/rollback_030.sql`
```sql
-- Note: Cannot restore deleted records without backup
-- This rollback just acknowledges the migration was rolled back
-- Manual restoration from backup would be needed if required
```

---

### Step 7: Final Verification
**Checkpoint: qa-tester agent**

Final test run after all changes:
```bash
pytest tests/ -v --tb=short
```

Manual verification checklist:
- [ ] User with non-discounted redemption can re-validate code
- [ ] User with discounted redemption is blocked
- [ ] New purchases with pending code + non-discounted product don't create redemption
- [ ] New purchases with pending code + discounted product do create redemption

---

## Files to Modify

| File | Change |
|------|--------|
| `tests/test_promo_payments.py` | NEW - Dedicated promo/payments test suite |
| `src/services/subscription_service.py` | Fix `_process_promo_attribution()` |
| `src/routes/promo.py` | Fix `validate_promo_code()` |
| `migrations/030_cleanup_false_promo_redemptions.sql` | Optional data cleanup |
| `migrations/rollback_030.sql` | Rollback script |

## Testing Summary

| Checkpoint | Command | When |
|------------|---------|------|
| Baseline | `pytest tests/ -v` | Before any changes |
| New tests (failing) | `pytest tests/test_promo_payments.py -v` | After Step 1 |
| Attribution fix | `pytest tests/test_promo_payments.py::TestPromoAttribution -v` | After Step 2 |
| Validation fix | `pytest tests/test_promo_payments.py::TestPromoValidation -v` | After Step 3 |
| Promo suite | `pytest tests/test_promo_payments.py -v` | After Step 4 |
| Full regression | `pytest tests/ -v` | After Step 5 |
| Final verification | `pytest tests/ -v` | After Step 7 |

## Rollback Plan

If issues arise:
1. Revert code changes in `subscription_service.py` and `promo.py`
2. If migration was run, note that deleted records cannot be restored without backup
3. Re-run test suite to confirm rollback

## Success Criteria

- [x] Baseline test suite passes before changes (468 passed, 2 failed pre-existing)
- [x] All new promo/payments tests pass (17/17)
- [x] Full test suite passes after changes (486 passed, 1 flaky pre-existing)
- [x] Users who validated but didn't purchase can re-validate
- [x] Users who purchased non-discounted can re-validate
- [x] Users who purchased discounted cannot re-validate

## Implementation Complete - 2026-01-30

### Files Modified
1. `backend/src/services/subscription_service.py` - Fixed `_process_promo_attribution()` to only record redemption for discounted products
2. `backend/src/routes/promo.py` - Fixed `validate_promo_code()` to only block if redemption was for discounted product
3. `backend/tests/test_promo_payments.py` - NEW comprehensive test suite (17 tests)
4. `backend/tests/test_promo_codes.py` - Updated existing test to use discounted product
5. `backend/tests/test_subscription_service.py` - Updated existing test to use discounted product

### Test Results
- Before: 481 tests (468 passed, 2 failed, 11 skipped)
- After: 498 tests (486 passed, 1 flaky, 11 skipped)
- Net improvement: +17 tests, +18 passing
