# Power Orientation Display Label Changes - COMPLETED

**Goal:** Change the frontend display labels for power orientation from "Top"/"Bottom" to "Leans Dom"/"Leans Sub" while preserving internal compatibility logic.

**Status:** COMPLETED

## Summary of Changes

### Files Modified

1. **`backend/src/scoring/display_names.py`**
   - Added `POWER_ORIENTATION_DISPLAY_NAMES` mapping

2. **`backend/src/routes/profile_ui.py`**
   - Import `POWER_ORIENTATION_DISPLAY_NAMES`
   - Use mapping for `power_ui["label"]`

3. **`backend/src/routes/compatibility.py`**
   - Import `POWER_ORIENTATION_DISPLAY_NAMES`
   - Use mapping for `power_overlap["user_label"]` and `power_overlap["partner_label"]`
   - Use mapping for `power_ui["label"]` in `_transform_profile_for_ui()`

4. **`backend/tests/test_profile_ui.py`**
   - Added 7 new tests for power orientation display labels

5. **`backend/tests/test_compatibility_ui.py`**
   - Added 2 new tests for compatibility UI power labels

### Label Mapping

| Internal Value | Display Label |
|----------------|---------------|
| `Top` | `Leans Dom` |
| `Bottom` | `Leans Sub` |
| `Switch` | `Switch` (unchanged) |
| `Versatile/Undefined` | `Versatile/Undefined` (unchanged) |

### Test Coverage

- Top → Leans Dom
- Bottom → Leans Sub
- Switch unchanged
- Versatile/Undefined unchanged
- Unknown orientation falls back to raw value
- Missing orientation defaults to Switch
- Empty power_dynamic defaults to Switch
- Compatibility UI power_overlap labels
- Compatibility UI partner_profile power label

### Test Results

- Before: 485 passed, 2 failed (pre-existing), 11 skipped
- After: 494 passed, 2 failed (same pre-existing), 11 skipped
- New tests: 9 (all passing)
- Regressions: None
