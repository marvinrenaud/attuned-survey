# Compatibility Algorithm Bug Report & Fix Specification

**Date**: November 10, 2025  
**Analysis**: Manelz (Bottom) + Big Black Haiti (Top)  
**Current Score**: 87%  
**Expected Score After Fixes**: 92-93%  

---

## Executive Summary

Three bugs in the compatibility algorithm are creating **false negative mismatches** for perfectly complementary Top/Bottom pairs:

1. **Display/Performance Activities Bug** (-4.6 points overall): Non-directional scoring treats complementary performer/watcher preferences as mismatches
2. **Protocols Naming Inconsistency Bug** (-0.7 points overall): `protocols_follow` vs `protocols_give` breaks directional matching
3. **Begging Survey Design Bug** (-1.5 points overall): Single Y/M/N question creates false mismatch for directional activity

**Total Impact**: -6.8 points (87% → 93-94% after fixes)

---

## Bug #1: Display/Performance Activities - False Negative Mismatches

### Current Behavior

**Category Score**: 28.6% (should be ~90%)

All display_performance activities are treated as **non-directional** because they don't follow the `_give/_receive` naming pattern. This causes the algorithm to flag perfect complementary matches as mismatches.

### False Mismatches Identified

| Activity | Manelz (Bottom) | BBH (Top) | Reality | Algorithm Sees |
|----------|-----------------|-----------|---------|----------------|
| `stripping_me` | 1 | 0 | Manelz strips | Only Manelz wants it |
| `watching_strip` | 0 | 1 | BBH watches | Only BBH wants it |
| **Combined Reality** | — | — | **Perfect complementary match** ✓ | **Two separate mismatches** ✗ |
| `posing` | 1 | 0 | Manelz poses for BBH | Only Manelz wants it ✗ |
| `dancing` | 1 | 0 | Manelz dances for BBH | Only BBH wants it ✗ |
| `revealing_clothing` | 1 | 0 | Manelz wears for BBH | Only Manelz wants it ✗ |

### Root Cause

**File**: `frontend/src/lib/matching/compatibilityMapper.js`  
**Function**: `calculateAsymmetricDirectionalJaccard()`

```javascript
// Lines 97-105
else if (!key.endsWith('_receive')) {
  // Non-directional activities (e.g., dirty_talk, moaning, roleplay)
  if (topVal >= 0.5 && bottomVal >= 0.5) {
    nonDirectionalMatches++;
  }
  if (topVal >= 0.5 || bottomVal >= 0.5) {
    nonDirectionalPotential++;
  }
}
```

**Problem**: Display activities like `stripping_me`, `watching_strip`, `posing`, `dancing`, `revealing_clothing` are performer/watcher pairs that need directional matching, but they don't have `_give/_receive` suffixes so they fall into non-directional logic.

### Proposed Fix Approach

**Option 1: Rename Activities (RECOMMENDED)**

Change display_performance activity keys to follow directional pattern:

**Survey Questions (no change needed - already directional)**:
- B24a: Stripping or undressing slowly (me performing)
- B24b: Watching partner strip (I watch)
- B25a: Being watched during solo pleasure (me)
- B25b: Watching partner during solo pleasure (I watch)

**Derived Activity Keys (CHANGE THESE)**:

Current → New:
```
stripping_me              → stripping_perform
watching_strip            → stripping_watch
watched_solo_pleasure     → solo_pleasure_perform  
watching_solo_pleasure    → solo_pleasure_watch
posing                    → posing_perform
dancing                   → dancing_perform
revealing_clothing        → revealing_clothing_wear
```

**Add corresponding "watch" keys**:
```
posing_watch              → (implicit in watching behavior)
dancing_watch             → (implicit in watching behavior)
revealing_clothing_watch  → (implicit in watching behavior)
```

Then update matching logic to recognize `_perform/_watch` pairs:

```javascript
// In calculateAsymmetricDirectionalJaccard()
if (key.endsWith('_perform')) {
  const watchKey = key.replace('_perform', '_watch');
  const bottomWatchVal = bottomCategory[watchKey] || 0;
  
  // PRIMARY: Top watches what Bottom performs
  if (topVal >= 0.5 || bottomWatchVal >= 0.5) {
    primaryPotential++;
    if (topVal >= 0.5 && bottomWatchVal >= 0.5) {
      primaryMatches++;
    }
  }
}
```

**Option 2: Special Case Display Activities**

Add explicit handling for display_performance category:

```javascript
// In calculateAsymmetricDirectionalJaccard()
const displayPerformPairs = {
  'stripping_me': 'watching_strip',
  'watched_solo_pleasure': 'watching_solo_pleasure',
  'posing': 'watching', // Needs "watching" key added
  'dancing': 'watching',
  'revealing_clothing': 'watching'
};

if (key in displayPerformPairs) {
  const watchKey = displayPerformPairs[key];
  const bottomPerformVal = bottomCategory[key] || 0;
  const topWatchVal = topCategory[watchKey] || 0;
  
  // PRIMARY: Bottom performs, Top watches
  if (bottomPerformVal >= 0.5 || topWatchVal >= 0.5) {
    primaryPotential++;
    if (bottomPerformVal >= 0.5 && topWatchVal >= 0.5) {
      primaryMatches++;
    }
  }
}
```

**RECOMMENDATION**: Use Option 1 (rename to `_perform/_watch` pattern) for consistency with existing directional naming conventions.

### Expected Impact

- display_performance: 28.6% → ~90% (+61.4 points)
- Activity overlap weight: 45%
- Category weight within activity: 1/6 = 16.67%
- **Overall score impact**: +61.4 × 16.67% × 45% = **+4.6 points**

---

## Bug #2: Protocols Naming Inconsistency

### Current Behavior

**Impact on power_exchange category**: Reduces score from ~75% to 58.3%

The protocols activity has inconsistent naming that breaks directional matching:

**Survey Questions**:
- B18a: Following strict commands or protocols during intimate play **(I follow)**
- B18b: Giving strict commands or protocols during intimate play **(I give)**

**Derived Activity Keys** (INCONSISTENT):
- `protocols_follow` (from B18a)
- `protocols_give` (from B18b)

**Problem**: The asymmetric Jaccard expects `_give/_receive` pairs, not `_follow/_give` pairs.

### Current Scoring Behavior

```
Manelz: protocols_follow = 1
BBH: protocols_give = 1

Algorithm processes:
1. "protocols_give" → looks for "protocols_receive" (doesn't exist) → PRIMARY MISS
2. "protocols_follow" → not "_give" or "_receive" → NON-DIRECTIONAL
3. Scores as: "Only one wants it (Top=0, Bottom=1)" → MISS
```

**Reality**: Perfect complementary match (Bottom follows, Top gives)

### Proposed Fix

**Option 1: Rename to Standard Pattern (RECOMMENDED)**

Change derived keys:
```
protocols_follow → protocols_receive
protocols_give   → protocols_give (no change)
```

Update scoring logic in `frontend/src/lib/scoring/activityMapper.js` (or wherever B18a/B18b get mapped):

```javascript
// B18a mapping
if (answers.B18a === 'Y') {
  activities.power_exchange.protocols_receive = 1;
} else if (answers.B18a === 'M') {
  activities.power_exchange.protocols_receive = 0.5;
} else {
  activities.power_exchange.protocols_receive = 0;
}
```

**Option 2: Add Special Case Handling**

In `calculateAsymmetricDirectionalJaccard()`, add:

```javascript
// Special case: protocols_follow pairs with protocols_give
if (key === 'protocols_give') {
  const followKey = 'protocols_follow';
  const bottomFollowVal = bottomCategory[followKey] || 0;
  
  // PRIMARY: Top gives protocols, Bottom follows
  if (topVal >= 0.5 || bottomFollowVal >= 0.5) {
    primaryPotential++;
    if (topVal >= 0.5 && bottomFollowVal >= 0.5) {
      primaryMatches++;
    }
  }
}
```

**RECOMMENDATION**: Use Option 1 (rename to `protocols_receive`) for consistency.

### Expected Impact

- power_exchange: 58.3% → ~75% (+16.7 points)
- Activity overlap weight: 45%
- Category weight within activity: 1/6 = 16.67%
- **Overall score impact**: +16.7 × 16.67% × 45% = **+0.7 points**

---

## Bug #3: Begging Survey Design Flaw

### Current Behavior

**Impact on verbal_roleplay category**: Reduces score from 100% to 80%

**Survey Question B23**: "Begging or pleading (in play)" - Y/M/N (single question)

**Problem**: This is a **directional activity** (one person begs, other person hears/enjoys the begging) but it's asked as a single non-directional question.

### Interpretation Ambiguity

**BBH (Top) answered N**:
- Likely interpretation: "I don't want to beg" (correct Top behavior)
- Missing data: Does BBH enjoy hearing their partner beg? (Unknown)

**Manelz (Bottom) answered Y**:
- Likely interpretation: "I want to beg" (correct Bottom behavior)

**Current Scoring**:
```
BBH: begging = 0
Manelz: begging = 1

Algorithm: Non-directional mismatch → MISS
Reality: BBH doesn't beg + Manelz begs = Likely compatible
```

### Proposed Fix

**Step 1: Update Survey (IntimacAI_Full_Survey_UserFacing_v0_4.md)**

Change B23 from single question to directional pair:

**BEFORE**:
```
**B23.** Begging or pleading (in play)
```

**AFTER**:
```
**B23a.** Begging or pleading - me doing the begging (I beg)  
**B23b.** Begging or pleading - hearing my partner beg (I hear/enjoy)
```

**Rationale**: This matches the pattern of all other power exchange activities (B15a/b, B16a/b, B17a/b, B18a/b) and clarifies who is in which role.

**Step 2: Update Activity Mapping**

In scoring logic (e.g., `frontend/src/lib/scoring/activityMapper.js`):

**BEFORE**:
```javascript
// B23 - single question
if (answers.B23 === 'Y') {
  activities.verbal_roleplay.begging = 1;
} else if (answers.B23 === 'M') {
  activities.verbal_roleplay.begging = 0.5;
} else {
  activities.verbal_roleplay.begging = 0;
}
```

**AFTER**:
```javascript
// B23a - doing the begging (receive role - being the beggar)
if (answers.B23a === 'Y') {
  activities.verbal_roleplay.begging_receive = 1;
} else if (answers.B23a === 'M') {
  activities.verbal_roleplay.begging_receive = 0.5;
} else {
  activities.verbal_roleplay.begging_receive = 0;
}

// B23b - hearing partner beg (give role - making partner beg / enjoying hearing it)
if (answers.B23b === 'Y') {
  activities.verbal_roleplay.begging_give = 1;
} else if (answers.B23b === 'M') {
  activities.verbal_roleplay.begging_give = 0.5;
} else {
  activities.verbal_roleplay.begging_give = 0;
}
```

**Alternative naming**: Could use `begging_do` / `begging_hear` if `_give/_receive` feels awkward for verbal activities.

**Step 3: Update Compatibility Algorithm**

Once renamed to `begging_give/begging_receive`, the asymmetric directional Jaccard will automatically handle it correctly:

```javascript
// In calculateAsymmetricDirectionalJaccard()
// Will now process:
if (key === 'begging_give') {
  const receiveKey = 'begging_receive';
  const bottomReceiveVal = bottomCategory[receiveKey] || 0;
  
  // PRIMARY: Top makes/enjoys Bottom begging → Bottom begs
  if (topVal >= 0.5 || bottomReceiveVal >= 0.5) {
    primaryPotential++;
    if (topVal >= 0.5 && bottomReceiveVal >= 0.5) {
      primaryMatches++;
    }
  }
}
```

### Migration Note

**Existing survey responses**: Need to migrate old B23 responses. Suggested logic:

```javascript
// Migration for existing responses with old B23 format
if (profile.answers.B23 !== undefined && !profile.answers.B23a) {
  const b23Value = profile.answers.B23;
  
  // If Bottom orientation, assume B23=Y means "I want to beg"
  if (profile.power_dynamic.orientation === 'Bottom') {
    profile.answers.B23a = b23Value; // I beg
    profile.answers.B23b = 'M'; // Assume maybe on hearing partner
  }
  // If Top orientation, assume B23=N means "I don't beg" but might enjoy hearing
  else if (profile.power_dynamic.orientation === 'Top') {
    profile.answers.B23a = 'N'; // I don't beg
    profile.answers.B23b = b23Value === 'N' ? 'M' : b23Value; // Conservative: assume Maybe if they said No
  }
  // If Switch, split equally
  else {
    profile.answers.B23a = b23Value;
    profile.answers.B23b = b23Value;
  }
}
```

### Expected Impact

- verbal_roleplay: 80% → 100% (+20 points)
- Activity overlap weight: 45%
- Category weight within activity: 1/6 = 16.67%
- **Overall score impact**: +20 × 16.67% × 45% = **+1.5 points**

---

## Additional Survey Improvement Recommendation

### B22: Commands

**Current**: "Giving or receiving commands" (single question)

**Issue**: Similar ambiguity to begging - one person gives commands, another receives/follows them.

**Suggested Split**:
```
**B22a.** Following commands during intimate play (I follow)
**B22b.** Giving commands during intimate play (I give)
```

**Impact**: Currently scored as non-directional. Should be directional for Top/Bottom pairs.

---

## Summary of Expected Score Improvements

| Bug | Current | After Fix | Category Impact | Overall Impact |
|-----|---------|-----------|-----------------|----------------|
| Display/Performance | 28.6% | ~90% | +61.4 pts | +4.6% |
| Protocols | 58.3% | ~75% | +16.7 pts | +0.7% |
| Begging | 80% | 100% | +20 pts | +1.5% |
| **TOTAL** | **87%** | **93-94%** | — | **+6.8%** |

### Score Breakdown After Fixes

```
Component Scores:
  Power Complement:  100.0% × 0.20 = 20.0
  Domain Similarity:  90.2% × 0.25 = 22.6
  Activity Overlap:   83.4% × 0.45 = 37.5  (up from 76.6%)
  Truth Overlap:     100.0% × 0.10 = 10.0
  
  TOTAL: 90.1 points
  
  Boundary Conflicts: 0
  Boundary Penalty: 0
  
  FINAL: 90% (conservative estimate)
```

**Expected range**: 90-94% depending on exact implementations

---

## Implementation Checklist

### Phase 1: Survey Updates
- [ ] Update survey markdown (IntimacAI_Full_Survey_UserFacing_v0_4.md)
  - [ ] Split B23 into B23a/B23b
  - [ ] Consider splitting B22 into B22a/B22b
  - [ ] Rename display questions to clarify perform/watch roles

### Phase 2: Activity Mapping
- [ ] Update activity key names in scoring logic
  - [ ] `protocols_follow` → `protocols_receive`
  - [ ] `begging` → `begging_give` / `begging_receive`
  - [ ] Display activities → `*_perform` / `*_watch` pattern
- [ ] Add migration logic for existing survey responses

### Phase 3: Compatibility Algorithm
- [ ] Update `calculateAsymmetricDirectionalJaccard()` if using special case handling
- [ ] Add recognition for `_perform/_watch` pairs (if using Option 2 for display)
- [ ] Test with BBH + Manelz profiles
- [ ] Test with other pair types (Top/Top, Bottom/Bottom, Switch/Switch)

### Phase 4: Validation
- [ ] Run test suite with fixed algorithm
- [ ] Verify BBH + Manelz score: expect 90-94%
- [ ] Verify no regression on other test cases
- [ ] Update compatibility_version to 0.6

---

## Test Case: Expected Results After Fixes

### Manelz + BBH

**Input**:
- Manelz: Bottom (100/17), exploration=65, verbal=90
- BBH: Top (100/0), exploration=60, verbal=70

**Expected Activity Scores by Category**:
- physical_touch: 97.8% (unchanged - already working)
- oral: 100.0% (unchanged - already working)
- anal: 95.0% (unchanged - already working)
- power_exchange: ~75% (up from 58.3% - protocols fix)
- verbal_roleplay: 100% (up from 80% - begging fix)
- display_performance: ~90% (up from 28.6% - display fix)

**Expected Overall Score**: 90-94%

**Interpretation**: "Exceptional compatibility" (≥85%)

---

## Files to Modify

1. **Survey Document**: `IntimacAI_Full_Survey_UserFacing_v0_4.md`
2. **Activity Mapping**: `frontend/src/lib/scoring/activityMapper.js` (or equivalent)
3. **Compatibility Mapper**: `frontend/src/lib/matching/compatibilityMapper.js`
4. **Test Data**: `frontend/src/lib/matching/__tests__/testProfiles.js`
5. **Python Calculator**: `backend/src/compatibility/calculator.py` (for consistency)

---

## Notes

- All three bugs create **false negative mismatches** - they underestimate compatibility
- No false positives identified - algorithm doesn't overestimate incompatible pairs
- Fixes improve accuracy for Top/Bottom pairs without affecting Switch/Switch or same-pole pairs
- After fixes, the 6-7 point gap from 100% reflects legitimate minor preference differences

---

**End of Bug Report**
