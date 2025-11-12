# Changelog

All notable changes to the Attuned intimacy profile survey project.

---

## [v0.6] - 2025-11-12 - Compatibility Algorithm Fixes

### Fixed
- **Display/performance activities** now recognized as complementary pairs (stripping, posing, dancing)
  - Aligned frontend/backend naming: `_self/_watching` pattern
  - Added directional matching logic for display activities
  - Impact: +4.6 percentage points, display category: 28.6% → 95%

- **Protocols naming consistency**
  - Renamed `protocols_follow` → `protocols_receive` throughout codebase
  - Now properly pairs with `protocols_give` in matching algorithm
  - Impact: +0.7 percentage points

- **Commands/begging survey ambiguity**
  - Split B22 into B22a (receive commands) / B22b (give commands)
  - Split B23 into B23a (do begging) / B23b (hear begging)
  - Provides clear directional preferences for Top/Bottom pairs
  - Impact: +1.5 percentage points

- **Backend Python calculator** not matching frontend JavaScript
  - Ported full asymmetric directional Jaccard algorithm to Python
  - Backend now produces identical results to frontend
  - Fixed activity recommendation scoring for complementary pairs

### Added
- **`calculate_asymmetric_directional_jaccard()`** in Python backend
  - Recognizes _give/_receive complementary pairs
  - Recognizes _self/_watching complementary pairs
  - Special handling for watching_strip and watching_solo_pleasure
  - Primary axis (80% weight) + secondary axis (20% weight)

- **`calculate_same_pole_jaccard()`** for Top/Top and Bottom/Bottom pairs
  - Properly penalizes incompatible role preferences (both want to give = incompatible)
  - Rewards versatility (can do both give and receive)
  - Reduces non-directional activity credit for same-pole pairs

- **Complementary pair recognition** in activity recommendations
  - `score_mutual_interest()` now identifies directional pairs
  - Complementary preferences score 1.0 (not 0.1)
  - Activities properly personalized for Top/Bottom dynamics

- **Migration scripts**
  - `migrate_activity_preference_keys.py` - Update activity database (24/850 activities)
  - `update_specific_profiles.py` - Update user profiles with new keys
  - `test_existing_users_compatibility.py` - Test with real data

- **Comprehensive test suite**
  - Real user validation (Top/Bottom pairs)
  - Regression tests (Top/Top, Bottom/Bottom, Switch/Switch)
  - Activity recommendation tests
  - Cross-platform consistency tests

### Improved
- **Activity overlap accuracy**: +66 percentage points for test users (29% → 95%)
- **Overall compatibility scores**: +6-30 points for complementary Top/Bottom pairs
- **Test users**: 64% → 94% (Moderate → Exceptional compatibility)
- **Activity recommendation personalization** for directional activities

### Changed (Breaking)
- **Survey questions**: B22/B23 split into directional pairs (B22a/b, B23a/b)
  - Users must answer new split questions for proper matching
  - Old profiles need migration or re-survey

- **Activity keys renamed**:
  - `stripping_me` → `stripping_self`
  - `watched_solo_pleasure` → `solo_pleasure_self`
  - `posing` → `posing_self`
  - `dancing` → `dancing_self`
  - `revealing_clothing` → `revealing_clothing_self`
  - `protocols_follow` → `protocols_receive`
  - `commands` → `commands_give` / `commands_receive`
  - `begging` → `begging_give` / `begging_receive`

### Documentation
- Created `COMPATIBILITY_ALGORITHM_FIX_SUMMARY.md` - Complete implementation details
- Created `COMPREHENSIVE_TEST_RESULTS.md` - Full test results
- Created `READY_TO_DEPLOY.md` - Deployment checklist
- Updated README.md, backend/README.md, frontend/README.md to v0.6
- Archived 16 historical documents to `docs/archive/`

---

## [v0.5] - 2025-10-15 - Same-Pole Fix & Algorithm Enhancement

### Fixed
- Same-pole pair matching (Top/Top, Bottom/Bottom) now properly penalized
- Truth overlap multiplier for same-pole pairs (0.5x reduction)

### Added
- `calculateSamePoleJaccard()` function in frontend
- Reduced scoring for incompatible power dynamics
- Versatility recognition within activities

### Improved
- Top/Top and Bottom/Bottom pairs score more accurately (lower scores)
- Compatibility interpretations better reflect power dynamic challenges

---

## [v0.4] - 2025-10-10 - Survey Streamline & AI Enrichment

### Changed
- **Survey streamlined** from 71 to 54 questions
- Removed redundant ipsative questions
- Improved question clarity and flow

### Added
- **AI-powered activity enrichment** using Groq
  - 850 activities enriched with power roles, preference keys, domains
  - 100% coverage across all activities
  - Automated with retry logic and rate limiting

- **Activity recommendation system**
  - Preference-based scoring (mutual interest, power alignment, domain fit)
  - Bank-first approach with AI fallback
  - Intensity progression (warmup → peak → afterglow)

- **Anatomy-based filtering**
  - Penis, Vagina, Breasts preferences
  - Activities filtered by required anatomy
  - Audience scope (couples/groups/all)

### Improved
- Profile calculation accuracy
- Domain scoring based on activities
- Boundary taxonomy (8-key system)

---

## [v0.3.1] - 2025-09-XX - Initial Implementation

### Added
- React frontend with survey flow
- Flask backend API
- PostgreSQL database (Supabase)
- Basic compatibility matching
- Arousal profiling (SES/SIS)
- Power dynamics calculation
- Activity preferences (Y/M/N format)
- Truth topics assessment
- Boundary collection
- Results display
- Admin panel

### Features
- 71-question survey
- Multi-chapter navigation
- Progress tracking
- Session persistence
- Data export (CSV/JSON)
- Responsive design

---

## Version History Summary

| Version | Date | Focus | Key Changes |
|---------|------|-------|-------------|
| v0.6 | 2025-11-12 | Algorithm Fixes | Display activities, protocols, commands/begging, backend sync |
| v0.5 | 2025-10-15 | Same-Pole Fix | Top/Top and Bottom/Bottom pair penalization |
| v0.4 | 2025-10-10 | AI & Streamline | 54 questions, AI enrichment, recommendations |
| v0.3.1 | 2025-09-XX | Initial Release | Full survey and matching system |

