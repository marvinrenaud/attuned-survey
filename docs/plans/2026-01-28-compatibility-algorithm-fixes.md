# Compatibility Algorithm Fixes - Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix three critical bugs in the compatibility algorithm so that truly compatible couples score close to 100%

**Architecture:** Modify `backend/src/compatibility/calculator.py` with surgical fixes to three functions

**Tech Stack:** Python, pytest

---

## Bugs to Fix

### Bug 1: Mutual Disinterest Returns 0% Instead of Agreement

**Current behavior:** When both profiles have 0.0 (No) for an activity like anal, the Jaccard algorithms skip it entirely because neither has interest >= 0.5. This means mutual agreement on what they DON'T want isn't counted.

**Desired behavior:** Agreement is agreement. Both saying "yes" OR both saying "no" should count as a match.

**Impact:** Perfect Match pair scores 83% activity overlap instead of ~95%

**Fix location:** Three Jaccard functions need updating:
- `calculate_asymmetric_directional_jaccard()`
- `calculate_same_pole_jaccard()`
- Standard Jaccard in `calculate_activity_overlap()`

**Fix approach - Agreement-Based Jaccard:**
```python
# OLD: Only count if either interested
if va >= 0.5 or vb >= 0.5:
    potential += 1
    if va >= 0.5 and vb >= 0.5:
        mutual += 1

# NEW: Count agreement (both yes OR both no)
# Both interested = agreement
if va >= 0.5 and vb >= 0.5:
    agreement += 1
    total += 1
# Both NOT interested = also agreement (mutual disinterest)
elif va < 0.5 and vb < 0.5:
    agreement += 1
    total += 1
# Mismatch (one interested, one not)
else:
    total += 1
    # No agreement added

score = agreement / total if total > 0 else 0.5
```

---

### Bug 2: Same-Pole Domain Similarity Penalty Not Implemented

**Current behavior:** `calculate_domain_similarity()` returns 97% for Top+Top pairs

**Desired behavior:** Per TECHNICAL_NOTES.md lines 470-477, same-pole pairs should have `avgSimilarity × 0.5`

**Impact:** Top+Top scores 57% instead of 35-45%

**Fix location:** `calculate_domain_similarity()` lines 118-170

**Fix approach:**
```python
def calculate_domain_similarity(domains_a, domains_b, power_a, power_b):
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')

    is_complementary = (orientation_a == 'Top' and orientation_b == 'Bottom') or \
                      (orientation_a == 'Bottom' and orientation_b == 'Top')

    is_same_pole = (orientation_a == 'Top' and orientation_b == 'Top') or \
                   (orientation_a == 'Bottom' and orientation_b == 'Bottom')

    # ... calculate base similarity ...

    if is_complementary:
        return similarity  # No penalty
    elif is_same_pole:
        return similarity * 0.5  # 50% penalty per TECHNICAL_NOTES.md
    else:
        return similarity  # Switch/Switch or mixed
```

---

### Bug 3: Versatile/Versatile Power Complement Returns 50%

**Current behavior:** `calculate_power_complement()` returns 0.50 for Versatile/Versatile, same as same-pole conflicts

**Desired behavior:** Versatile/Versatile couples are both flexible and can adapt - should score higher (0.70-0.80)

**Impact:** Conservative Match pair scores 72% instead of 85-95%

**Fix location:** `calculate_power_complement()` lines 88-115

**Fix approach:**
```python
def calculate_power_complement(power_a, power_b):
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')

    # Perfect complement: Top + Bottom
    if (orientation_a == 'Top' and orientation_b == 'Bottom') or \
       (orientation_a == 'Bottom' and orientation_b == 'Top'):
        intensity_alignment = 1.0 - abs(intensity_a - intensity_b) * 0.3
        return min(1.0, intensity_alignment)

    # Both Switch: Good compatibility
    if orientation_a == 'Switch' and orientation_b == 'Switch':
        return 0.85

    # NEW: Both Versatile/Undefined - flexible, can adapt
    if orientation_a in ('Versatile', 'Versatile/Undefined') and \
       orientation_b in ('Versatile', 'Versatile/Undefined'):
        return 0.75  # NEW: Higher than same-pole (0.50)

    # One Switch: Moderate compatibility
    if orientation_a == 'Switch' or orientation_b == 'Switch':
        return 0.75

    # One Versatile with Top/Bottom - somewhat flexible
    if orientation_a in ('Versatile', 'Versatile/Undefined') or \
       orientation_b in ('Versatile', 'Versatile/Undefined'):
        return 0.60  # NEW: Between same-pole and Switch

    # Same pole (both Top or both Bottom): Lower but not zero
    return 0.50
```

---

## Implementation Tasks

### Task 1: Add Agreement-Based Jaccard Test

**Files:**
- Create test: `tests/test_compatibility_agreement_jaccard.py`

**Step 1: Write failing test**
```python
def test_mutual_disinterest_counts_as_agreement():
    """Both saying 'no' to anal should be agreement, not 0%."""
    from src.compatibility.calculator import calculate_activity_overlap

    # Both have 0.0 for anal activities
    activities_a = {
        'anal': {'anal_fingers_toys_receive': 0.0, 'anal_fingers_toys_give': 0.0}
    }
    activities_b = {
        'anal': {'anal_fingers_toys_receive': 0.0, 'anal_fingers_toys_give': 0.0}
    }
    power_switch = {'orientation': 'Switch', 'intensity': 0.5}

    overlap = calculate_activity_overlap(activities_a, activities_b, power_switch, power_switch)

    # Mutual disinterest should score high (agreement), not 0.5 (default) or 0.0
    assert overlap >= 0.9, f"Mutual disinterest should be agreement, got {overlap}"
```

**Step 2: Run test to verify it fails**
```bash
pytest tests/test_compatibility_agreement_jaccard.py::test_mutual_disinterest_counts_as_agreement -v
```
Expected: FAIL (currently returns 0.5 default)

---

### Task 2: Implement Agreement-Based Standard Jaccard

**Files:**
- Modify: `src/compatibility/calculator.py` lines 417-427

**Step 1: Update standard Jaccard logic**
```python
# In calculate_activity_overlap(), the else branch (standard Jaccard):
else:
    # Agreement-based Jaccard: both yes OR both no = agreement
    keys = set(list(cat_a.keys()) + list(cat_b.keys()))
    agreement = 0
    total = 0
    for k in keys:
        va = cat_a.get(k, 0)
        vb = cat_b.get(k, 0)
        total += 1
        # Both interested = agreement
        if va >= 0.5 and vb >= 0.5:
            agreement += 1
        # Both NOT interested = also agreement
        elif va < 0.5 and vb < 0.5:
            agreement += 1
        # Mismatch = no agreement added

    score = agreement / total if total > 0 else 0.5
```

**Step 2: Run test to verify it passes**
```bash
pytest tests/test_compatibility_agreement_jaccard.py::test_mutual_disinterest_counts_as_agreement -v
```

**Step 3: Run full test suite**
```bash
pytest tests/ -v
```

---

### Task 3: Add Same-Pole Domain Penalty Test

**Files:**
- Add to: `tests/test_compatibility_agreement_jaccard.py`

**Step 1: Write failing test**
```python
def test_same_pole_domain_similarity_penalty():
    """Top+Top domain similarity should be halved per TECHNICAL_NOTES.md."""
    from src.compatibility.calculator import calculate_domain_similarity

    domains = {'sensation': 70, 'connection': 80, 'power': 60, 'exploration': 75, 'verbal': 70}
    power_top = {'orientation': 'Top', 'intensity': 0.8}

    # Same domains for both = 100% raw similarity
    similarity = calculate_domain_similarity(domains, domains, power_top, power_top)

    # Same-pole should apply 0.5 penalty: 100% * 0.5 = 50%
    assert similarity <= 0.55, f"Same-pole domain similarity should be ~50%, got {similarity}"
```

**Step 2: Run test to verify it fails**
Expected: FAIL (currently returns ~0.97)

---

### Task 4: Implement Same-Pole Domain Penalty

**Files:**
- Modify: `src/compatibility/calculator.py` function `calculate_domain_similarity()`

**Step 1: Add same-pole detection and penalty**
```python
def calculate_domain_similarity(domains_a, domains_b, power_a, power_b):
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')

    is_complementary = (orientation_a == 'Top' and orientation_b == 'Bottom') or \
                      (orientation_a == 'Bottom' and orientation_b == 'Top')

    is_same_pole = (orientation_a == 'Top' and orientation_b == 'Top') or \
                   (orientation_a == 'Bottom' and orientation_b == 'Bottom')

    # ... existing calculation logic ...

    # Calculate base similarity
    if is_complementary:
        # existing complementary logic
        base_similarity = (sensation_dist + connection_dist + power_dist + exploration_score + verbal_score) / 5.0
        return base_similarity
    else:
        # Standard distance for all 5 domains
        exploration_dist = 1.0 - abs(norm(domains_a.get('exploration', 0)) - norm(domains_b.get('exploration', 0)))
        verbal_dist = 1.0 - abs(norm(domains_a.get('verbal', 0)) - norm(domains_b.get('verbal', 0)))
        base_similarity = (sensation_dist + connection_dist + power_dist + exploration_dist + verbal_dist) / 5.0

        # Apply same-pole penalty per TECHNICAL_NOTES.md
        if is_same_pole:
            return base_similarity * 0.5

        return base_similarity
```

**Step 2: Run test to verify it passes**

---

### Task 5: Add Versatile Power Complement Test

**Files:**
- Add to: `tests/test_compatibility_agreement_jaccard.py`

**Step 1: Write failing test**
```python
def test_versatile_versatile_power_complement():
    """Versatile+Versatile should score higher than same-pole conflicts."""
    from src.compatibility.calculator import calculate_power_complement

    power_versatile = {'orientation': 'Versatile', 'intensity': 0.3}
    power_top = {'orientation': 'Top', 'intensity': 0.8}

    versatile_score = calculate_power_complement(power_versatile, power_versatile)
    same_pole_score = calculate_power_complement(power_top, power_top)

    # Versatile/Versatile should be higher than same-pole (0.50)
    assert versatile_score > same_pole_score, \
        f"Versatile/Versatile ({versatile_score}) should be > same-pole ({same_pole_score})"
    assert versatile_score >= 0.70, f"Versatile/Versatile should be >= 0.70, got {versatile_score}"
```

**Step 2: Run test to verify it fails**
Expected: FAIL (currently both return 0.50)

---

### Task 6: Implement Versatile Power Complement Fix

**Files:**
- Modify: `src/compatibility/calculator.py` function `calculate_power_complement()`

**Step 1: Add Versatile handling before same-pole fallback**
```python
def calculate_power_complement(power_a, power_b):
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')
    intensity_a = power_a.get('intensity', 0.5)
    intensity_b = power_b.get('intensity', 0.5)

    # Perfect complement: Top + Bottom
    if (orientation_a == 'Top' and orientation_b == 'Bottom') or \
       (orientation_a == 'Bottom' and orientation_b == 'Top'):
        intensity_alignment = 1.0 - abs(intensity_a - intensity_b) * 0.3
        return min(1.0, intensity_alignment)

    # Both Switch: Good compatibility
    if orientation_a == 'Switch' and orientation_b == 'Switch':
        return 0.85

    # NEW: Both Versatile - flexible, can adapt to each other
    versatile_values = ('Versatile', 'Versatile/Undefined')
    if orientation_a in versatile_values and orientation_b in versatile_values:
        return 0.75

    # One Switch: Moderate compatibility
    if orientation_a == 'Switch' or orientation_b == 'Switch':
        return 0.75

    # NEW: One Versatile with defined orientation - somewhat adaptable
    if orientation_a in versatile_values or orientation_b in versatile_values:
        return 0.60

    # Same pole (both Top or both Bottom): Lower but not zero
    return 0.50
```

**Step 2: Run tests to verify**

---

### Task 7: Update Directional Jaccards for Agreement

**Files:**
- Modify: `src/compatibility/calculator.py`

Update `calculate_asymmetric_directional_jaccard()` and `calculate_same_pole_jaccard()` to handle mutual disinterest as agreement in non-directional activities.

**Note:** Directional activities (_give/_receive) are more complex - mutual disinterest on directional pairs (both don't want to give AND both don't want to receive) should count as agreement.

---

### Task 8: Run Full Regression Test

**Step 1: Run diverse pair tests**
```bash
pytest tests/test_compatibility_diverse_pairs.py -v
```

**Step 2: Run full test suite**
```bash
pytest tests/ -v
```

**Step 3: Verify expected outcomes**
- Perfect Match: 95-100% (was 89%)
- Vanilla Couple: 90-95% (was 84%)
- Top+Top Conflict: 35-45% (was 57%)
- Bottom+Bottom Conflict: 35-45% (was 58%)
- Conservative Match: 85-95% (was 72%)

---

## Validation Criteria

After implementation, these assertions should pass:

| Pair | Before | After | Expected Range |
|------|--------|-------|----------------|
| Perfect Match | 89% | TBD | 95-100% |
| Vanilla Couple | 84% | TBD | 90-95% |
| Top+Top Conflict | 57% | TBD | 35-45% |
| Bottom+Bottom | 58% | TBD | 35-45% |
| Conservative Match | 72% | TBD | 85-95% |
| Curious Vanilla | 89% | TBD | 85-90% (should stay) |

---

## Risks and Mitigations

1. **Risk:** Agreement-based Jaccard could inflate scores for mismatched couples
   **Mitigation:** Only applies to activities where both have same disposition; mismatches still penalized

2. **Risk:** Same-pole penalty might be too harsh
   **Mitigation:** 0.5 multiplier is documented in TECHNICAL_NOTES.md and was intended from v0.5

3. **Risk:** Existing tests may break
   **Mitigation:** Run full test suite after each change; update baselines if intentional
