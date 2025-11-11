# Quick Test Guide - Existing Users

## Test Compatibility with Real Data

This will load actual profiles from your database and recalculate their compatibility with the new algorithm.

### Step 1: Activate Backend Environment
```bash
cd backend
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows
```

### Step 2: List Available Profiles
```bash
python3 scripts/test_existing_users_compatibility.py --list
```

This shows all profiles with their IDs, user_ids, and power orientations.

Example output:
```
======================================================================
AVAILABLE PROFILES
======================================================================
  ID:   1 | User: test_user_1       | Top    (0.8)
  ID:   2 | User: test_user_2       | Bottom (1.0)
  ID:   3 | User: manelz            | Bottom (1.0)
  ID:   4 | User: bbh               | Top    (1.0)
======================================================================
```

### Step 3: Test Two Users

**Option A - By User ID:**
```bash
python3 scripts/test_existing_users_compatibility.py --user-a bbh --user-b manelz
```

**Option B - By Profile ID:**
```bash
python3 scripts/test_existing_users_compatibility.py --id-a 4 --id-b 3
```

### What to Look For

The output will show:
1. **Overall Compatibility Score** - Should be 90-94% for complementary Top/Bottom pairs (up from 87%)
2. **Activity Breakdown** - You'll see the new key names in use:
   - `stripping_self` / `watching_strip` (not `stripping_me`)
   - `protocols_receive` / `protocols_give` (not `protocols_follow`)
   - `commands_receive` / `commands_give` (split from `commands`)
   - `begging_receive` / `begging_give` (split from `begging`)
3. **Category Scores**:
   - display_performance should be much higher (~90% vs 28.6%)
   - power_exchange should improve (~75% vs 58.3%)
   - verbal_roleplay should improve (100% vs 80%)

### Example Full Output
```
======================================================================
COMPATIBILITY TEST
======================================================================

👤 Profile A: bbh
   Power: Top (1.0)

👤 Profile B: manelz  
   Power: Bottom (1.0)

======================================================================
RESULTS
======================================================================

🎯 Overall Compatibility: 92%
   Exceptional compatibility

📊 Breakdown:
   Power Complement:  100%
   Domain Similarity: 90%
   Activity Overlap:  85%  ← Should be higher than before
   Truth Overlap:     100%

🎭 Key Activities (Profile A vs Profile B):
   Display/Performance:
     stripping_self           : 0.0 vs 1.0  ← Bottom performs
     watching_strip           : 1.0 vs 0.0  ← Top watches
     posing_self              : 0.0 vs 1.0
   
   Power Exchange:
     protocols_receive        : 0.0 vs 1.0  ← Bottom follows
     protocols_give           : 1.0 vs 0.0  ← Top gives
   
   Verbal/Roleplay:
     commands_receive         : 0.0 vs 1.0  ← Bottom receives
     commands_give            : 1.0 vs 0.0  ← Top gives
     begging_receive          : 0.0 vs 1.0  ← Bottom begs
     begging_give             : 1.0 vs 0.0  ← Top hears
```

### Troubleshooting

**"ModuleNotFoundError: No module named 'dotenv'"**
→ Activate the venv: `source venv/bin/activate`

**"No profiles found in database"**
→ You need to create test profiles first using the frontend

**"Profile not found"**
→ Use `--list` to see available profile IDs

**Wrong compatibility score?**
→ Check that profiles have the new activity keys. Old profiles might still have old keys and won't benefit from the fixes until they're migrated.

---

## If Profiles Have Old Keys

If your existing profiles were created before these fixes, they'll have the old key names (`stripping_me`, `protocols_follow`, etc.). You have two options:

1. **Recreate the profiles** - Have users retake the survey
2. **Migrate the profiles** - Write a migration script similar to the activities migration

Would you like me to create a profile migration script?
