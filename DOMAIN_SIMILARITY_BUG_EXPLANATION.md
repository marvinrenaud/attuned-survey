# Domain Similarity Calculation Bug Explanation

## The Bug

The original Python implementation in `backend/src/compatibility/calculator.py` had **two critical bugs**:

### Bug #1: Wrong Domain Names
The code was looking for domains that **don't exist** in the actual profile data:

```python
# WRONG - These domains don't exist!
complementary_domains = ['dominance', 'submission', 'service']
```

**Actual domains in profiles:**
- `sensation`
- `connection`
- `power`
- `exploration`
- `verbal`

### Bug #2: Incorrect Logic for Top/Bottom Pairs
The original code used a generic loop that would:
1. Try to find 'dominance', 'submission', 'service' (which don't exist)
2. Fall back to standard distance calculation for all domains
3. **Never apply the v0.5 complementary logic** for exploration/verbal

## What Happened When Running the Calculation

When calculating compatibility between the two profiles:
- **Alexa (Bottom)**: exploration=25, verbal=62
- **Big Black Haiti (Top)**: exploration=75, verbal=100

The buggy code:
1. Looped through domains looking for 'dominance', 'submission', 'service' (not found)
2. Applied standard distance: `1 - abs(25 - 75) / 100 = 1 - 0.5 = 0.5` for exploration
3. Applied standard distance: `1 - abs(62 - 100) / 100 = 1 - 0.38 = 0.62` for verbal
4. This **penalized the difference** when it should have recognized it as beneficial

**Result:** Domain similarity calculated as **-3380%** (completely broken due to negative values from the wrong calculation)

## The Fix (v0.5 Implementation)

The corrected implementation follows the v0.5 specification:

### For Top/Bottom Pairs:
1. **Sensation, Connection, Power**: Use standard distance calculation
   ```python
   sensation_dist = 1 - abs(domains_a['sensation'] - domains_b['sensation']) / 100
   ```

2. **Exploration, Verbal**: Use **minimum threshold approach**
   ```python
   min_exploration = min(domains_a['exploration'], domains_b['exploration'])
   exploration_score = 1.0 if min_exploration >= 50 else min_exploration / 50
   ```

### Why This Matters:
For Top/Bottom pairs, **differences in exploration/verbal are actually beneficial**:
- An eager Bottom (exploration=95) + measured Top (exploration=60) = **IDEAL**
- The Bottom can explore more, while the Top maintains control
- As long as **both are above 50** (willing to explore), it's a perfect match

### Example Calculation (Fixed):

**Alexa (Bottom)**: exploration=25, verbal=62  
**Big Black Haiti (Top)**: exploration=75, verbal=100

**Exploration:**
- Minimum: min(25, 75) = 25
- Since 25 < 50: score = 25 / 50 = **0.5** (proportional penalty)

**Verbal:**
- Minimum: min(62, 100) = 62
- Since 62 >= 50: score = **1.0** (no penalty - both willing)

**Result:** Domain similarity = **73%** (correct!)

## Comparison

| Aspect | Original (Buggy) | Fixed (v0.5) |
|--------|------------------|--------------|
| Domain names | 'dominance', 'submission', 'service' ❌ | 'sensation', 'connection', 'power', 'exploration', 'verbal' ✅ |
| Top/Bottom logic | Standard distance for all ❌ | Minimum threshold for exploration/verbal ✅ |
| Result for test profiles | -3380% (broken) ❌ | 73% (correct) ✅ |

## Files Affected

- **Buggy code:** `backend/src/compatibility/calculator.py` (lines 45-83)
- **Fixed code:** `calculate_compatibility_test.py` (lines 39-80) - temporary fix
- **Reference:** `data/intimacai_v04/CursorFiles2/CURSOR_AI_INSTRUCTIONS_v0_5.md` (lines 39-88)

## Recommendation

The `backend/src/compatibility/calculator.py` file should be updated to match the v0.5 specification. The current implementation will produce incorrect results for all Top/Bottom pair calculations.

