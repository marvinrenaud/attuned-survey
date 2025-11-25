# Boundary to Activity Mappings

**Last Updated:** November 2025  
**Version:** v0.5  
**Status:** Active

---

## Overview

This document defines the mapping between hard boundary keys and the activity preference keys that fall under each boundary category. These mappings are used in the compatibility calculator to detect boundary conflicts between players.

**Key Concept:** A boundary conflict occurs when:
- Player A has a hard boundary (e.g., `hardBoundaryAnal`)
- AND Player B wants activities that fall under that boundary (e.g., `anal_fingers_toys_give`)

---

## The 8-Key Boundary Taxonomy

The system uses 8 standardized boundary keys:

1. `hardBoundaryImpact` - Impact play
2. `hardBoundaryRestrain` - Bondage and restraints
3. `hardBoundaryBreath` - Breath play / Choking
4. `hardBoundaryDegrade` - Degradation / Humiliation
5. `hardBoundaryPublic` - Public play
6. `hardBoundaryRecord` - Recording (photos, videos)
7. `hardBoundaryAnal` - Anal activities
8. `hardBoundaryWatersports` - Watersports / Scat play

---

## Complete Boundary-to-Activity Mappings

### 1. hardBoundaryImpact

**Description:** Impact play activities involving hitting, slapping, or biting.

**Mapped Activities:**
- `spanking_moderate_give`
- `spanking_moderate_receive`
- `spanking_hard_give`
- `spanking_hard_receive`
- `slapping_give`
- `slapping_receive`
- `biting_moderate_give`
- `biting_moderate_receive`

**Example Conflict:**
- Player A has `hardBoundaryImpact` as a hard limit
- Player B wants `spanking_moderate_give: 1.0`
- **Result:** Boundary conflict detected

---

### 2. hardBoundaryRestrain

**Description:** Bondage, restraints, and blindfolding activities.

**Mapped Activities:**
- `restraints_give`
- `restraints_receive`
- `blindfold_give`
- `blindfold_receive`

**Example Conflict:**
- Player A has `hardBoundaryRestrain` as a hard limit
- Player B wants `restraints_give: 1.0`
- **Result:** Boundary conflict detected

---

### 3. hardBoundaryBreath

**Description:** Breath play and choking activities.

**Mapped Activities:**
- `choking_give`
- `choking_receive`

**Example Conflict:**
- Player A has `hardBoundaryBreath` as a hard limit
- Player B wants `choking_give: 1.0`
- **Result:** Boundary conflict detected

---

### 4. hardBoundaryDegrade

**Description:** Degradation and humiliation activities.

**Mapped Activities:**
- `degradation_give`
- `degradation_receive`
- `humiliation_give`
- `humiliation_receive`

**Note:** These activity keys may not be present in all survey versions. The boundary is still valid even if the specific activities aren't in a player's profile.

**Example Conflict:**
- Player A has `hardBoundaryDegrade` as a hard limit
- Player B wants `degradation_give: 1.0`
- **Result:** Boundary conflict detected

---

### 5. hardBoundaryPublic

**Description:** Public play, exhibitionism, and voyeurism activities.

**Mapped Activities:**
- `exhibitionism`
- `voyeurism`
- `public_play`

**Note:** These activity keys may not be present in all survey versions. The boundary is still valid even if the specific activities aren't in a player's profile.

**Example Conflict:**
- Player A has `hardBoundaryPublic` as a hard limit
- Player B wants `exhibitionism: 1.0`
- **Result:** Boundary conflict detected

---

### 6. hardBoundaryRecord

**Description:** Recording activities (photos, videos).

**Mapped Activities:**
- `recording`
- `photos`
- `videos`

**Note:** These activity keys may not be present in all survey versions. The boundary is still valid even if the specific activities aren't in a player's profile.

**Example Conflict:**
- Player A has `hardBoundaryRecord` as a hard limit
- Player B wants `recording: 1.0`
- **Result:** Boundary conflict detected

---

### 7. hardBoundaryAnal

**Description:** Anal activities including penetration and rimming.

**Mapped Activities:**
- `anal_fingers_toys_give`
- `anal_fingers_toys_receive`
- `rimming_give`
- `rimming_receive`

**Example Conflict:**
- Player A has `hardBoundaryAnal` as a hard limit
- Player B wants `anal_fingers_toys_give: 1.0` OR `rimming_give: 1.0`
- **Result:** Boundary conflict detected

---

### 8. hardBoundaryWatersports

**Description:** Watersports and scat play activities.

**Mapped Activities:**
- `watersports_give`
- `watersports_receive`
- `scat_play`

**Note:** `scat_play` may not be present in all survey versions.

**Example Conflict:**
- Player A has `hardBoundaryWatersports` as a hard limit
- Player B wants `watersports_give: 1.0` OR `watersports_receive: 0.5`
- **Result:** Boundary conflict detected

---

## Implementation Details

### Code Locations

**Primary Implementation:**
- **File:** `frontend/src/lib/matching/compatibilityMapper.js`
- **Function:** `checkBoundaryConflicts()`
- **Lines:** 331-364
- **Object:** `boundaryMap`

**Backend Model:**
- **File:** `backend/src/models/activity.py`
- **Constant:** `ALLOWED_BOUNDARIES` (lines 7-11)
- **Note:** Defines the 8 boundary keys but not the activity mappings

### How It Works

1. **Conflict Detection:**
   - For each hard boundary in Player A's profile
   - Check if Player B wants any activities mapped to that boundary
   - Activity preference >= 0.5 triggers a conflict

2. **Penalty Calculation:**
   - Each boundary conflict reduces compatibility score by 0.2 (20 percentage points)
   - Formula: `boundaryPenalty = boundaryConflicts * 0.2`
   - Final score: `score = max(0, score - boundaryPenalty)`

3. **Deduplication:**
   - Only one conflict is counted per boundary type
   - If multiple activities in the same boundary category conflict, it's still counted as 1 conflict

### Example Calculation

**Scenario:**
- Player A has: `hardBoundaryAnal`, `hardBoundaryWatersports`
- Player B wants: `anal_fingers_toys_give: 1.0`, `rimming_give: 1.0`, `watersports_give: 1.0`

**Result:**
- 2 boundary conflicts detected (Anal and Watersports)
- Penalty: 2 × 0.2 = 0.4 (40 percentage points)
- If base compatibility was 80%, final score = 40%

---

## Activity Key Naming Conventions

### Directional Activities

Many activities have `_give` and `_receive` variants:
- `spanking_moderate_give` - Player wants to give spanking
- `spanking_moderate_receive` - Player wants to receive spanking

**Both variants are checked** when detecting conflicts.

### Non-Directional Activities

Some activities don't have give/receive variants:
- `exhibitionism`
- `voyeurism`
- `public_play`
- `recording`
- `photos`
- `videos`
- `scat_play`

---

## Survey Version Compatibility

**Note:** Not all activity keys are present in all survey versions:
- v0.4 survey may have different activity keys
- Some boundaries (Public, Degrade, Record) may map to activities not in the current survey
- The boundary system still works - if a player has a boundary but the other player doesn't want those activities, no conflict occurs

---

## Maintenance

### Adding New Activities

If new activities are added that should map to boundaries:

1. **Update the mapping** in `frontend/src/lib/matching/compatibilityMapper.js`
2. **Update this documentation**
3. **Test boundary conflict detection** with the new activities

### Adding New Boundaries

If new boundary types are added:

1. **Add to `ALLOWED_BOUNDARIES`** in `backend/src/models/activity.py`
2. **Add to boundary map** in `frontend/src/lib/matching/compatibilityMapper.js`
3. **Add to survey options** in `frontend/src/pages/Survey.jsx`
4. **Update this documentation**

---

## Related Documentation

- **8-Key Taxonomy:** `docs/archive/ACTIVITY_REBASELINE_SUMMARY.md` (lines 155-163)
- **Boundary Migration:** `backend/scripts/migrate_boundary_taxonomy.py`
- **Compatibility Algorithm:** `data/intimacai_v04/CursorFiles2/CURSOR_AI_INSTRUCTIONS_v0_5.md`

---

## Quick Reference Table

| Boundary Key | Activity Count | Key Activities |
|-------------|----------------|----------------|
| `hardBoundaryImpact` | 8 | spanking, slapping, biting |
| `hardBoundaryRestrain` | 4 | restraints, blindfold |
| `hardBoundaryBreath` | 2 | choking |
| `hardBoundaryDegrade` | 4 | degradation, humiliation |
| `hardBoundaryPublic` | 3 | exhibitionism, voyeurism, public_play |
| `hardBoundaryRecord` | 3 | recording, photos, videos |
| `hardBoundaryAnal` | 4 | anal_fingers_toys, rimming |
| `hardBoundaryWatersports` | 3 | watersports, scat_play |

**Total Mapped Activities:** 31 unique activity keys

---

## Questions or Issues?

If you find discrepancies between this documentation and the code:
1. Check the primary source: `frontend/src/lib/matching/compatibilityMapper.js`
2. The code implementation is the source of truth
3. Update this documentation if the code changes

