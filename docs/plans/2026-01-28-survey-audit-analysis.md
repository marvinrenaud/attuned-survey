# Survey System Comprehensive Audit

> **For Claude:** This is a RESEARCH AND ANALYSIS plan, not an implementation plan. Execute each phase systematically, documenting findings.

**Goal:** Audit the survey system end-to-end: scientific foundation, question usage, profile creation, compatibility scoring, and activity selection - to identify refinement opportunities.

**Scope:** Questions CSV → Scoring modules → Profile creation → Compatibility algorithm → Activity recommender

---

## Phase 1: Scientific Foundation Research

### Task 1.1: Research SES/SIS Scales
- Review original Bancroft & Janssen Dual Control Model
- Compare Attuned's A1-A12 implementation to validated SES/SIS-2 scales
- Document any adaptations and assess validity

### Task 1.2: Research Erotic Preference Instruments
- Review Wilson Sex Fantasy Questionnaire methodology
- Assess how B-section questions map to validated instruments
- Identify any gaps in coverage

### Task 1.3: Power Dynamics Framework
- Review literature on D/s dynamics measurement
- Assess A13-A16 power orientation questions
- Evaluate confidence calculation methodology

---

## Phase 2: Codebase Audit - Question Flow

### Task 2.1: Map Question → Scoring Module Usage
For each question (A1-A16, B1-B36, C1):
- Which scoring module consumes it
- How it's normalized/transformed
- What profile component it feeds

### Task 2.2: Identify Unused or Underutilized Questions
- Questions that feed only one component
- Questions with redundant coverage
- Questions not used in compatibility or activity selection

### Task 2.3: Document Scoring Module Dependencies
```
questions.csv → scoring/*.py → profile.data → compatibility → recommender
```

---

## Phase 3: Profile Creation Analysis

### Task 3.1: Arousal Propensity (SE/SIS)
- Trace A1-A12 through arousal.py
- Verify normalization matches documented 0-1 scale
- Check interpretation band assignments

### Task 3.2: Power Dynamic
- Trace A13-A16 through power.py
- Verify THETA_FLOOR and DELTA_BAND thresholds
- Validate confidence calculation formula

### Task 3.3: Domain Scores
- Trace B-section questions through domains.py
- Verify domain composition matches documentation
- Check for overlap/redundancy across domains

### Task 3.4: Activity Mapping
- Trace B-section through activities.py
- Verify give/receive directionality
- Check threshold application (Yes/Maybe/No)

---

## Phase 4: Compatibility Algorithm Analysis

### Task 4.1: Power Complement Scoring
- Review calculator.py power complement logic
- Verify pairing scores match documentation
- Assess intensity alignment handling

### Task 4.2: Domain Similarity
- Review domain comparison logic
- Verify Top/Bottom threshold approach
- Check same-pole distance calculation

### Task 4.3: Activity Overlap (Asymmetric Jaccard)
- Review directional matching logic
- Verify 80/20 primary/secondary weighting
- Check same-pole Jaccard implementation

### Task 4.4: Truth Overlap & Boundaries
- Review truth topic matching
- Verify boundary conflict detection
- Check penalty application

---

## Phase 5: Activity Selection Impact

### Task 5.1: Recommender Input Analysis
- What profile components feed the recommender
- How compatibility scores influence selection
- Role of boundaries in filtering

### Task 5.2: Truth vs Dare Selection
- How activity type is determined
- Role of user preferences in type selection
- Intensity progression logic

### Task 5.3: Personalization Depth
- Which profile components affect activity text
- How power dynamic influences selection
- Domain score impact on recommendations

---

## Phase 6: Gap Analysis & Recommendations

### Task 6.1: Scientific Validity Assessment
- Alignment with validated instruments
- Areas needing additional validation
- Potential publication/credibility concerns

### Task 6.2: Question Efficiency
- Redundant questions that could be removed
- Missing dimensions that should be added
- Question phrasing improvements

### Task 6.3: Algorithm Improvements
- Weighting adjustments
- Edge case handling
- Same-pole pairing enhancements

### Task 6.4: Activity Selection Optimization
- Better profile utilization
- Enhanced personalization opportunities
- Type balance improvements

---

## Deliverable

Final report with:
1. Current state documentation
2. Scientific alignment assessment
3. Specific refinement recommendations
4. Priority ranking (high/medium/low impact)
