# Survey Question Phrasing Consistency Fix

**Date:** 2026-01-28
**Branch:** `fix/survey-question-phrasing-consistency`
**Status:** Complete

## Overview

Several survey questions with a/b variants (receive/give pairs) have inconsistent phrasing patterns. This plan standardizes the wording for clarity and consistency.

## Baseline Test Results (Pre-Change)

| Metric | Value |
|--------|-------|
| Tests Collected | 343 |
| Passed | 338 |
| Failed | 1 (unrelated: `test_update_user_can_update_both_flags`) |
| Skipped | 4 |

## Files to Modify

### Primary (Source of Truth)
1. **`frontend/src/data/questions.csv`** - Main question bank used by React frontend

### Secondary (Must be re-synced after CSV update)
2. **Database `survey_questions` table** - Populated via import script
   - Run: `python backend/scripts/import_survey_questions.py --clear --version 0.4`

### Not Affected
- `backend/src/scoring/display_names.py` - Uses separate "(Receiving)/(Giving)" display format for profile UI (already consistent)
- `data/intimacai_v04/` - Reference/archive files, not production

## Changes Summary

| Question | Current Text | New Text |
|----------|-------------|----------|
| **B4b** | "Spanking - moderate (I deliver)." | "Spanking - moderate (I do)." |
| **B5b** | "Using hands/fingers on partner's genitals (I do)." | "Using hands/fingers on genitals (I do)." |
| **B6b** | "Spanking - hard (I deliver)." | "Spanking - hard (I do)." |
| **B7b** | "Slapping (face or body) (I deliver)." | "Slapping (face or body) (I do)." |
| **B12b** | "Oral stimulation on other body parts (I do)." | "Oral stimulation on other body parts - chest, neck, ears, inner thighs, etc. (I do)." |
| **B15b** | "Restraining partner (I do)." | "Restraining partner (hands held, ties, cuffs, rope) (I do)." |
| **B22a** | "Receiving/following commands during intimate play (I follow)." | "Following commands during intimate play (I follow)." |
| **B23a** | "Begging or pleading - me doing the begging (I beg)." | "Begging or pleading (me doing the begging)." |
| **B23b** | "Begging or pleading - hearing my partner beg (I hear/enjoy)." | "Begging or pleading (hearing my partner beg)." |
| **B24a** | "Stripping or undressing slowly (me performing)." | "Stripping or undressing slowly (I perform)." |
| **B25a** | "Being watched during solo pleasure (me)." | "Being watched during solo pleasure (I perform)." |

### No Changes Needed
- **B16b** - Already says "(I do)"
- **B17b** - "(I control)" is acceptable for this specific activity

---

## Implementation Steps

### Phase 1: Create Test Infrastructure (BEFORE any changes)

**Gap Analysis:** Currently NO tests exist for:
- CSV parsing
- SurveyQuestion model
- Import script (`import_survey_questions.py`)
- Question text validation

**New Test Files to Create:**

#### 1. `backend/tests/test_survey_questions_csv.py`
Tests CSV structure, comma handling, and parsing:
- `test_csv_file_exists`
- `test_csv_has_required_columns`
- `test_csv_question_count` (76 questions)
- `test_all_questions_have_ids`
- `test_question_with_commas_parsed_correctly`
- `test_parentheticals_preserved`

#### 2. `backend/tests/test_import_survey_questions.py`
Tests import script functionality:
- `test_parse_valid_json`
- `test_parse_complex_json`
- `test_parse_empty_string`
- `test_parse_invalid_json`
- `test_import_creates_question_records`
- `test_imported_text_matches_csv`

#### 3. `backend/tests/test_survey_question_text.py`
Regression tests for specific question text (will fail initially, pass after changes):
- `test_b4b_text` - expects "(I do)"
- `test_b5b_text` - expects "on genitals"
- `test_b6b_text` - expects "(I do)"
- `test_b7b_text` - expects "(I do)"
- `test_b12b_text` - expects examples
- `test_b15b_text` - expects examples
- `test_b22a_text` - expects "Following"
- `test_b23a_text` - simplified format
- `test_b23b_text` - simplified format
- `test_b24a_text` - expects "(I perform)"
- `test_b25a_text` - expects "(I perform)"

### Phase 2: Run Baseline Tests

```bash
cd backend
source venv/bin/activate

# Run full test suite (baseline)
python -m pytest tests/ -v > ../test_results_baseline.txt 2>&1

# Run new tests (expect text regression tests to fail with old values)
python -m pytest tests/test_survey_questions_csv.py -v
python -m pytest tests/test_import_survey_questions.py -v
```

### Phase 3: Update CSV

Edit `frontend/src/data/questions.csv` with the 11 changes listed above.

**CSV Escaping Note:** Questions with commas in the text must be properly quoted. The CSV already uses this pattern correctly.

### Phase 4: Verify Frontend Loads Correctly

```bash
cd frontend
pnpm run dev
# Navigate to survey and verify questions display correctly
```

### Phase 5: Re-import to Database

```bash
cd backend
source venv/bin/activate
python scripts/import_survey_questions.py --clear --version 0.4
```

### Phase 6: Run Full Test Suite (Post-Change)

```bash
cd backend
python -m pytest tests/ -v > ../test_results_after.txt 2>&1

# Compare results
diff ../test_results_baseline.txt ../test_results_after.txt
```

**Expected:** Same pass/fail count as baseline (338 pass, 1 unrelated fail, 4 skipped)

### Phase 7: Verify Database Sync

```bash
cd backend
python -c "
from src.main import app
from src.models.survey import SurveyQuestion

with app.app_context():
    for qid in ['B4b', 'B5b', 'B6b', 'B7b', 'B12b', 'B15b', 'B22a', 'B23a', 'B23b', 'B24a', 'B25a']:
        q = SurveyQuestion.query.filter_by(question_id=qid, survey_version='0.4').first()
        print(f'{qid}: {q.prompt if q else \"NOT FOUND\"}')"
```

### Phase 8: Manual QA Verification

- [ ] Start a new survey in React frontend - verify all modified questions display correctly
- [ ] Check that B12b shows the examples (chest, neck, ears, inner thighs, etc.)
- [ ] Check that B15b shows the examples (hands held, ties, cuffs, rope)
- [ ] Verify no broken CSV parsing (quotes, commas properly escaped)
- [ ] Submit a test survey and verify profile calculation still works
- [ ] Verify database table has updated text for all 11 questions

---

## Risks

### Low Risk
- **Text-only changes** - No changes to question IDs, scoring logic, or activity keys
- **No schema changes** - Same database structure
- **No version bump needed** - Cosmetic/editorial changes

### Potential Issues
- CSV parsing with added commas in B12b/B15b - must be properly quoted
- Database import script must handle the longer text fields

---

## Rollback Plan

If issues occur:
```bash
git checkout develop -- frontend/src/data/questions.csv
cd backend && python scripts/import_survey_questions.py --clear --version 0.4
```

---

## Acceptance Criteria

1. [ ] New test files created and passing (CSV structure, import script)
2. [ ] All 11 questions updated with new phrasing in CSV
3. [ ] Frontend survey displays questions correctly
4. [ ] Database import succeeds without errors
5. [ ] Database content matches CSV for all changed questions
6. [ ] All existing tests pass (same baseline: 338 pass)
7. [ ] Manual QA checklist completed
