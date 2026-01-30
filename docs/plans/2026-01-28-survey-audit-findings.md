# Survey System Comprehensive Audit - Findings Report

**Date:** 2026-01-28
**Auditor:** Claude Code (AI-assisted analysis)
**Scope:** Questions CSV → Scoring modules → Profile creation → Compatibility algorithm → Activity recommender

---

## Executive Summary

The Attuned survey system is a well-structured intimacy profiling tool that draws inspiration from validated psychological instruments but implements significant adaptations. Key findings:

1. **A1-A12 (Arousal Questions) are UNUSED** in compatibility or activity selection - they're purely informational
2. **D1/D2 (Anatomy Questions)** are referenced in code but missing from questions.csv
3. **Scientific credibility concerns** with the SES/SIS adaptation (12 items vs validated 45 items)
4. **Domain score overlap** exists with some questions contributing to multiple domains
5. **Strong directional matching** system for activities is well-implemented

---

## Phase 1: Scientific Foundation Assessment

### 1.1 SES/SIS Scales Analysis

**Original Validated Instrument:**
- Sexual Inhibition/Sexual Excitation Scales (SIS/SES) by Bancroft & Janssen (2007)
- Part of the Dual Control Model developed at the Kinsey Institute
- SES-2 validated version has **45 items** using 4-point Likert scale
- Three subscales: SE (excitation), SIS1 (performance inhibition), SIS2 (threat inhibition)

**Attuned Implementation (A1-A12):**
- **12 items** using 7-point Likert scale
- Mapped to three subscales:
  - SE: A1-A4 (4 items)
  - SIS-P (Performance): A5-A8 (4 items)
  - SIS-C (Consequence): A9-A12 (4 items)

**Assessment:**
| Aspect | Validated SES/SIS-2 | Attuned A1-A12 |
|--------|---------------------|----------------|
| Item count | 45 | 12 (27%) |
| Response format | 4-point Likert | 7-point Likert |
| Subscales | 3 | 3 |
| Validation | Peer-reviewed | Not independently validated |
| Reliability (α) | .88 / .83 / .73 | Unknown |

**Credibility Concern:** The drastic reduction from 45 to 12 items significantly impacts psychometric validity. The subscale scores may not reliably measure the same constructs as the validated instrument.

### 1.2 Erotic Preference Assessment

**Reference Instruments:**
- Wilson Sex Fantasy Questionnaire (WSFQ): 40 items, 4 subscales
- Sexual Interest Profile (SIP): Various validated versions

**Attuned Implementation (B1-B28 activities):**
- 44 activity preference items covering:
  - Physical touch (B1-B10): 20 items
  - Oral activities (B11-B12): 4 items
  - Anal activities (B13-B14): 4 items
  - Power exchange (B15-B18): 8 items
  - Verbal/Roleplay (B19-B23): 7 items
  - Display/Performance (B24-B28): 9 items

**Assessment:** The activity coverage is comprehensive and maps well to common erotic preference taxonomies. The Yes/Maybe/No (Y/M/N) format is appropriate for preference assessment.

### 1.3 Power Dynamics Framework

**Literature Review:**
- No single validated instrument for D/s orientation measurement exists
- Most research uses behavioral frequency or self-identification
- Power orientation is typically treated as a spectrum

**Attuned Implementation (A13-A16):**
- 4 items on 7-point Likert scale
- Top orientation: A13, A15
- Bottom orientation: A14, A16
- Classification algorithm uses:
  - THETA_FLOOR = 30 (minimum engagement threshold)
  - DELTA_BAND = 15 (Switch classification band)

**Assessment:** The 4-item scale is a novel construct without external validation but uses reasonable classification logic. The confidence calculation `(score/100) * (1 - 0.3 * (counter_score/100))` appropriately penalizes ambivalent responses.

---

## Phase 2: Question → Scoring Module Mapping

### 2.1 Complete Question Usage Map

| Question | Module | Output | Used In Compatibility | Used In Recommendations |
|----------|--------|--------|----------------------|------------------------|
| **A1-A4** | arousal.py | SE score (0-1) | **NO** | **NO** |
| **A5-A8** | arousal.py | SIS-P score (0-1) | **NO** | **NO** |
| **A9-A12** | arousal.py | SIS-C score (0-1) | **NO** | **NO** |
| **A13, A15** | power.py | Top score | YES (power complement) | YES (power alignment) |
| **A14, A16** | power.py | Bottom score | YES (power complement) | YES (power alignment) |
| **B1-B10** | activities.py | Physical touch prefs | YES (activity overlap) | YES (mutual interest) |
| **B11-B12** | activities.py | Oral prefs | YES (activity overlap) | YES (mutual interest) |
| **B13-B14** | activities.py | Anal prefs | YES (activity overlap) | YES (mutual interest) |
| **B15-B18** | activities.py | Power exchange prefs | YES (activity overlap) | YES (mutual interest) |
| **B19-B23** | activities.py | Verbal/roleplay prefs | YES (activity overlap) | YES (mutual interest) |
| **B24-B28** | activities.py | Display prefs | YES (activity overlap) | YES (mutual interest) |
| **B29-B36** | truth_topics.py | Truth topic prefs | YES (truth overlap) | YES (truth selection) |
| **C1** | profile.py | Hard limits list | YES (boundary conflicts) | YES (activity filtering) |
| **D1** | profile.py | Anatomy self | Not in CSV | Activity filtering |
| **D2** | profile.py | Anatomy preference | Not in CSV | Activity filtering |

### 2.2 Critical Finding: Unused Questions

**A1-A12 (Arousal Propensity) - 12 questions (16% of survey) are NOT USED:**
- Stored in `profile.arousal_propensity`
- Never consumed by `compatibility/calculator.py`
- Never consumed by `recommender/scoring.py`
- Purely informational/display purposes

**D1/D2 (Anatomy) - Referenced but Missing:**
- `profile.py:28-59` references D1/D2
- These questions do NOT exist in `questions.csv`
- Code handles them gracefully (empty arrays if missing)

### 2.3 Domain Score Question Overlap

Several questions contribute to multiple domain scores:

| Question | Domains |
|----------|---------|
| B9a/B9b (spitting) | Sensation, Exploration |
| B10a/B10b (watersports) | Sensation, Exploration |
| B20 (moaning) | Connection, Verbal |
| B21 (roleplay) | Exploration, Verbal |
| B22a/B22b (commands) | Power, Verbal |
| B23a/B23b (begging) | Power, Verbal |

---

## Phase 3: Profile Creation Analysis

### 3.1 Arousal Propensity (arousal.py)

**Implementation:**
```python
SE: mean(A1-A4) normalized to 0-1
SIS-P: mean(A5-A8) normalized to 0-1
SIS-C: mean(A9-A12) normalized to 0-1
```

**Normalization:** Likert 1-7 → 0-1 via `(value - 1) / 6`

**Interpretation Bands:**
- Low: ≤0.30
- Moderate-Low: 0.31-0.55
- Moderate-High: 0.56-0.75
- High: >0.75

**Finding:** Implementation is correct but OUTPUT IS NEVER USED downstream.

### 3.2 Power Dynamic (power.py)

**Implementation:**
```python
top_score = mean(A13, A15) * 100
bottom_score = mean(A14, A16) * 100

if both < 30: "Versatile/Undefined"
elif |diff| <= 15 and both >= 30: "Switch"
elif top > bottom: "Top"
else: "Bottom"
```

**Confidence Calculation:**
- Top: `(top/100) * (1 - 0.3 * (bottom/100))`
- Bottom: `(bottom/100) * (1 - 0.3 * (top/100))`
- Switch: `min(top, bottom) / 100`

**Finding:** Sound logic with appropriate thresholds.

### 3.3 Domain Scores (domains.py)

| Domain | Item Count | Sources |
|--------|------------|---------|
| Sensation | 14 | Physical touch (moderate/intense) |
| Connection | 11 | Massage, oral body, moaning, posing, clothing, 4 truth topics |
| Power | 12 | Restraints, blindfold, orgasm control, protocols, commands, begging |
| Exploration | 10 | Roleplay, stripping, solo pleasure, dancing, spitting, watersports |
| Verbal | 8 | Dirty talk, moaning, roleplay, commands, begging |

**Bug Found in Code Comments:** The JS implementation had a bug where `commands` and `begging` were undefined (not `commands_receive`/`commands_give`), so Verbal domain was effectively calculated from only 3 items. Python version includes all items.

### 3.4 Activity Mapping (activities.py)

**Conversion:** Y=1.0, M=0.5, N=0.0

**Categories:**
- `physical_touch`: 20 items (B1-B10 pairs)
- `oral`: 4 items (B11-B12 pairs)
- `anal`: 4 items (B13-B14 pairs)
- `power_exchange`: 8 items (B15-B18 pairs)
- `verbal_roleplay`: 7 items (B19-B23 mixed)
- `display_performance`: 9 items (B24-B28 with synthetic watching pairs)

**Synthetic Values:** `posing_watching`, `dancing_watching`, `revealing_clothing_watching` are hardcoded to 0.0 (no corresponding survey questions).

---

## Phase 4: Compatibility Algorithm Analysis

### 4.1 Weights

```python
power_complement: 15%
domain_similarity: 25%
activity_overlap: 40%
truth_overlap: 20%
```

### 4.2 Power Complement (calculator.py:15-42)

| Pairing | Score |
|---------|-------|
| Top + Bottom | 1.0 (minus intensity penalty) |
| Switch + Switch | 0.85 |
| Switch + Top/Bottom | 0.75 |
| Top + Top | 0.50 |
| Bottom + Bottom | 0.50 |

**Intensity Penalty:** `1.0 - |intensity_a - intensity_b| * 0.3`

### 4.3 Domain Similarity (calculator.py:45-98)

**For Complementary Pairs (Top/Bottom):**
- Sensation, Connection, Power: Standard distance (1 - |diff|)
- Exploration, Verbal: Minimum threshold approach (≥50 = 1.0)

**For Same-Pole or Switch Pairs:**
- All domains use standard distance

### 4.4 Activity Overlap

**Asymmetric Directional Jaccard (Top/Bottom pairs):**
- Primary axis (80%): Does Top want to GIVE what Bottom wants to RECEIVE?
- Secondary axis (20%): Does Bottom want to GIVE what Top wants to RECEIVE?

**Same-Pole Jaccard (Top/Top or Bottom/Bottom):**
- Penalizes matching on same role (both want to give = incompatible)
- Rewards versatility (can do both roles)

### 4.5 Truth Overlap

- Both high (≥0.5): Score = min(a, b)
- Both low (<0.5): Score = 0.5 (neutral)
- Mismatch: Score = 0.3

**Same-pole multiplier:** 0.5x for Top/Top or Bottom/Bottom pairs

### 4.6 Boundary Conflicts

- Each conflict applies **-20% penalty** to overall score
- Hard limit categories mapped to activity substrings for detection

---

## Phase 5: Activity Selection Impact

### 5.1 Recommender Scoring (recommender/scoring.py)

**Weights:**
```python
mutual_interest: 50%
power_alignment: 30%
domain_fit: 20%
```

**Mutual Interest:** Directional matching (give/receive, self/watching) with complementary scoring:
- ≥0.7 complementary: 1.0
- ≥0.5 complementary: 0.8
- ≥0.3 complementary: 0.6
- <0.3 complementary: 0.3

**Power Alignment:** Activity power_role vs player orientations:
- Top activity with Top+Bottom pair: 1.0
- Top activity with Top+Switch: 0.95
- Top activity with only Top: 0.8
- Top activity with only Switch: 0.6
- Top activity with only Bottoms: 0.0 (filtered out)

**Domain Fit:** Average of both players' domain scores for activity's domains.

### 5.2 What Profile Components Feed Recommendations

| Component | Used In | Impact |
|-----------|---------|--------|
| power_dynamic.orientation | Power alignment scoring | High (30% weight, can filter to 0) |
| activities.{category}.{item} | Mutual interest scoring | High (50% weight) |
| domain_scores.{domain} | Domain fit scoring | Moderate (20% weight) |
| boundaries.hard_limits | Activity filtering | Critical (removes activities) |
| anatomy.anatomy_self | Activity filtering | Critical (removes inappropriate) |
| arousal_propensity | **NOT USED** | None |
| activity_tags | Filtering | Moderate |

### 5.3 Profile Components NOT Used

1. **arousal_propensity** (SE, SIS-P, SIS-C) - 12 questions worth of data
2. **power_dynamic.intensity** - Only orientation is used in recommendations
3. **power_dynamic.confidence** - Not used in recommendations

---

## Phase 6: Gap Analysis & Recommendations

### 6.1 Scientific Validity Concerns

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| SES/SIS scale reduction (45→12 items) | HIGH | Either validate independently OR remove claims of SES/SIS basis OR add disclaimer |
| Arousal propensity unused | HIGH | Either integrate into algorithm OR remove from survey |
| Power dynamics not validated | MEDIUM | Consider adding validated measures or clearly label as proprietary |
| D1/D2 questions missing from CSV | MEDIUM | Add to CSV or remove from code |

### 6.2 Question Efficiency

**Potentially Removable (if arousal stays unused):**
- A1-A12 (12 questions, 16% of survey)
- Saves significant user effort if not providing value

**Missing Questions:**
- D1: Anatomy self (referenced in code)
- D2: Anatomy preference (referenced in code)

**Redundant Coverage:**
- moaning appears in Connection AND Verbal
- roleplay appears in Exploration AND Verbal
- commands appears in Power AND Verbal
- begging appears in Power AND Verbal
- spitting appears in Sensation AND Exploration
- watersports appears in Sensation AND Exploration

### 6.3 Algorithm Improvement Opportunities

| Improvement | Impact | Complexity |
|-------------|--------|------------|
| Use arousal_propensity in compatibility | HIGH | Medium - need to define how SE/SIS alignment matters |
| Use power intensity in recommendations | MEDIUM | Low - add intensity-based activity filtering |
| Add confidence weighting | LOW | Low - weight compatibility by confidence |
| Balance domain overlap | LOW | Medium - review which items contribute where |

### 6.4 Activity Selection Optimization

1. **Use Arousal Propensity:**
   - High SE users → prioritize more arousing activities
   - High SIS-P users → avoid performance-pressure activities
   - High SIS-C users → avoid consequence-heavy activities

2. **Use Power Intensity:**
   - High intensity Top + High intensity Bottom → more extreme power exchange
   - Low intensity → gentler activities

3. **Use Confidence:**
   - Low confidence in orientation → more neutral/exploratory activities

---

## Priority Recommendations

### HIGH Priority

1. **Decide on A1-A12 (Arousal) Usage**
   - Option A: Remove from survey (saves 12 questions, 16% shorter)
   - Option B: Integrate into compatibility/recommendations (requires algorithm work)
   - Option C: Keep for user insight display only (current state, but add value explanation)

2. **Add D1/D2 Questions to CSV**
   - Code references these for anatomy filtering
   - Currently users can't answer them

3. **Add Scientific Disclaimer**
   - If keeping A1-A12, clarify "inspired by" vs "validated implementation of" SES/SIS

### MEDIUM Priority

4. **Integrate Power Intensity**
   - Use in activity selection for intensity matching
   - Currently only orientation is used, intensity is calculated but ignored

5. **Review Domain Overlap**
   - Decide if items should contribute to multiple domains or be exclusive
   - Current overlap may dilute domain specificity

### LOW Priority

6. **Consider Adding Confidence Weighting**
   - Low confidence users might get more exploratory recommendations

7. **Independent Validation Study**
   - If claiming scientific basis, consider formal psychometric validation

---

## Appendix: Question-to-Code Traceability

### A-Section (16 questions)
```
A1-A4   → arousal.py:41 → profile.arousal_propensity.sexual_excitation
A5-A8   → arousal.py:45 → profile.arousal_propensity.inhibition_performance
A9-A12  → arousal.py:49 → profile.arousal_propensity.inhibition_consequence
A13,A15 → power.py:45   → profile.power_dynamic.top_score
A14,A16 → power.py:49   → profile.power_dynamic.bottom_score
```

### B-Section (44 questions from B1-B36)
```
B1-B28  → activities.py:14-88 → profile.activities.{category}.{item}
B29-B36 → truth_topics.py:22-48 → profile.truth_topics.{topic}
```

### C-Section (1 question)
```
C1 → profile.py:11-26 → profile.boundaries.hard_limits
```

### D-Section (referenced but missing)
```
D1 → profile.py:28-40 → profile.anatomy.anatomy_self (MISSING FROM CSV)
D2 → profile.py:42-54 → profile.anatomy.anatomy_preference (MISSING FROM CSV)
```

---

## Conclusion

The Attuned survey system has a solid foundation with comprehensive activity coverage and well-implemented directional matching. However, 16% of the survey (arousal questions A1-A12) provides no functional value beyond display, and key anatomy questions are missing from the survey. The scientific credibility claims around SES/SIS should be reviewed given the significant deviation from validated instruments.

The highest-impact changes would be:
1. Adding D1/D2 to the survey (enables anatomy filtering that's already coded)
2. Either removing or integrating A1-A12 (currently wasted user effort)
3. Clarifying scientific claims with appropriate caveats
