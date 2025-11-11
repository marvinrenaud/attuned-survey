# Local Testing Instructions

## What We've Changed

### Bug Fixes Implemented:
1. **Display Activities** - Renamed to `_self/_watching` pattern
   - `stripping_me` → `stripping_self`
   - `watched_solo_pleasure` → `solo_pleasure_self`
   - `posing` → `posing_self`
   - Added matching logic for `_self/_watching` pairs

2. **Protocols** - Fixed naming inconsistency
   - `protocols_follow` → `protocols_receive`

3. **Verbal Activities** - Split into directional pairs
   - `commands` → `commands_give` / `commands_receive`
   - `begging` → `begging_give` / `begging_receive`

### Expected Improvements:
- display_performance category: 28.6% → ~90%
- power_exchange category: 58.3% → ~75%
- verbal_roleplay category: 80% → 100%
- **Overall BBH+Manelz score: 87% → 90-94%**

---

## Quick Validation Tests

### Test 1: Check Key Naming
```bash
# Verify old keys are gone from code
grep -r "stripping_me\|watched_solo_pleasure\|protocols_follow" frontend/src/lib backend/src --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=__pycache__

# Expected: No matches (or only in test files/comments)
```

### Test 2: Verify Database Migration
```bash
cd backend
python3 -c "
import json
with open('enriched_activities_v2.json') as f:
    data = json.load(f)
old_keys = []
for aid, act in data.items():
    keys = act.get('preference_keys', [])
    if any(k in keys for k in ['posing', 'dancing', 'commands', 'begging']):
        old_keys.append(aid)
print(f'Activities with old keys: {len(old_keys)}')
print('Expected: 0')
"
```

### Test 3: Frontend Build
```bash
cd frontend
npm run build
# Should complete without errors
```

### Test 4: Backend Tests (if available)
```bash
cd backend
python3 scripts/test_compatibility.py
# Run any existing compatibility tests
```

### Test 5: Manual Integration Test
1. Start the frontend dev server: `cd frontend && npm run dev`
2. Start the backend: `cd backend && python3 run_backend.py`
3. Create two test profiles:
   - Profile A (Top): Commands give=Y, Begging hear=Y, Stripping watch=Y
   - Profile B (Bottom): Commands receive=Y, Begging do=Y, Stripping perform=Y
4. Calculate compatibility - should show high score (90%+)

---

## Files Changed

### Frontend:
- `frontend/src/lib/scoring/activityConverter.js` - Key mappings
- `frontend/src/lib/matching/compatibilityMapper.js` - Matching logic
- `frontend/src/lib/matching/categoryMap.js` - Display names
- `frontend/src/lib/scoring/domainCalculator.js` - Domain calculations
- `frontend/src/lib/scoring/activityTags.js` - Activity tags
- `frontend/src/lib/matching/__tests__/testProfiles.js` - Test data

### Backend:
- `backend/src/compatibility/calculator.py` - Python matching logic
- `backend/src/llm/activity_analyzer.py` - AI enrichment keys
- `backend/enriched_activities_v2.json` - Migrated activity database
- `backend/scripts/migrate_activity_preference_keys.py` - Migration script

### Documentation:
- `data/intimacai_v04/IntimacAI_Full_Survey_UserFacing_v0_4.md` - Survey questions

---

## If You Find Issues

### Rollback Database:
```bash
cd backend
cp enriched_activities_v2.json.backup enriched_activities_v2.json
```

### Rollback Code:
```bash
git checkout main -- [file_path]
```

### Full Branch Reset:
```bash
git checkout main
git branch -D compatibility_algo_fixes
```

---

## Next Steps After Testing

1. If all tests pass:
   - Review the changes one more time
   - Create summary documentation
   - Push to remote: `git push -u origin compatibility_algo_fixes`
   - Create PR for review

2. If tests fail:
   - Document the failure
   - Debug and fix
   - Re-test
   - Commit fixes to the branch

---

## Test with Existing Users (NEW!)

### List Available Profiles
```bash
cd backend
python3 scripts/test_existing_users_compatibility.py --list
```

This will show all profiles in your database with their IDs and orientations.

### Test Two Specific Users

**By User ID (e.g., "bbh", "manelz"):**
```bash
python3 scripts/test_existing_users_compatibility.py --user-a USER_ID_1 --user-b USER_ID_2
```

**By Profile ID (e.g., 1, 2):**
```bash
python3 scripts/test_existing_users_compatibility.py --id-a 1 --id-b 2
```

### Example Output
```
======================================================================
COMPATIBILITY TEST
======================================================================

👤 Profile A: manelz
   Power: Bottom (1.0)

👤 Profile B: bbh  
   Power: Top (1.0)

======================================================================
RESULTS
======================================================================

🎯 Overall Compatibility: 92%
   Exceptional compatibility

📊 Breakdown:
   Power Complement:  100%
   Domain Similarity: 90%
   Activity Overlap:  85%
   Truth Overlap:     100%

🎭 Key Activities (Profile A vs Profile B):
   Display/Performance:
     stripping_self       : 1.0 vs 0.0
     watching_strip       : 0.0 vs 1.0
     posing_self          : 1.0 vs 0.0
   
   Power Exchange:
     protocols_receive    : 1.0 vs 0.0
     protocols_give       : 0.0 vs 1.0
   
   Verbal/Roleplay:
     commands_receive     : 1.0 vs 0.0
     commands_give        : 0.0 vs 1.0
     begging_receive      : 1.0 vs 0.0
     begging_give         : 0.0 vs 1.0
```

### Get JSON Output
```bash
python3 scripts/test_existing_users_compatibility.py --user-a USER1 --user-b USER2 --json
```

This outputs raw JSON for programmatic use or comparison.

