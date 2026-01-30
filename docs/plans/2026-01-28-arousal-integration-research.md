# Arousal Integration Research Summary

**Date:** 2026-01-28
**Purpose:** Consolidate research findings on SES/SIS (Sexual Excitation/Inhibition Scales) to inform how Attuned can integrate arousal data into compatibility and activity recommendations.

---

## Table of Contents

1. [Background: The Dual Control Model](#background-the-dual-control-model)
2. [Current State in Attuned](#current-state-in-attuned)
3. [Research Findings by Factor](#research-findings-by-factor)
4. [How Others Use These Signals](#how-others-use-these-signals)
5. [Proposed Integration Approaches](#proposed-integration-approaches)
6. [Sources](#sources)

---

## Background: The Dual Control Model

The Sexual Inhibition/Sexual Excitation Scales (SIS/SES) were developed by **Bancroft & Janssen at the Kinsey Institute** (late 1990s-2000s) as part of the Dual Control Model of sexual response.

### Core Concept

Sexual response = balance between **excitatory** ("accelerator") and **inhibitory** ("brake") systems.

> "Every person will engage one or both pedals to a differing degree in any particular sexual situation, depending on their unique sexual physiology, history, and personality."
> — Kinsey Institute

### Three Factors

| Factor | Description | What High Scores Mean |
|--------|-------------|----------------------|
| **SE (Sexual Excitation)** | Propensity to become aroused by erotic stimuli | Easily aroused by touch, visuals, fantasy |
| **SIS-P (SIS1)** | Inhibition due to threat of performance failure | Arousal drops with performance anxiety, uncertainty |
| **SIS-C (SIS2)** | Inhibition due to threat of consequences | Arousal drops with risk concerns, fear of judgment |

### Validated Instrument

- Original SIS/SES: **45 items**, 4-point Likert scale
- Short form (SIS/SES-SF): **14 items**
- Attuned implementation: **12 items** (A1-A12), 7-point Likert scale

---

## Current State in Attuned

### Questions

| Questions | Factor | Attuned Mapping |
|-----------|--------|-----------------|
| A1-A4 | SE (Excitation) | `arousal_propensity.sexual_excitation` |
| A5-A8 | SIS-P (Performance) | `arousal_propensity.inhibition_performance` |
| A9-A12 | SIS-C (Consequence) | `arousal_propensity.inhibition_consequence` |

### Current Usage

**None.** These 12 questions are calculated and stored in the profile but:
- NOT used in compatibility scoring
- NOT used in activity recommendations
- Purely informational/display

---

## Research Findings by Factor

### SE (Sexual Excitation)

#### Finding 1: Individual High SE = Lower Satisfaction (Counterintuitive)

**Source:** Lykins, Janssen et al. 2012 - Newlywed couples study

> "Higher SES scores predicted lower sexual satisfaction for both husbands and wives."

**Mechanism:** People with high excitation may have higher expectations or be harder to satisfy.

**Implication:** High SE alone is not predictive of good outcomes.

#### Finding 2: Both High SE > Both Low SE

**Source:** Kim et al. 2021 - Response Surface Analysis (366 couples)

> "When partners are matched on their levels of sexual desire, it is better for their sexual and relationship satisfaction if partners show agreement for **higher desire compared to lower desire**."

> "Higher desire rather than matching in desire between partners predicted relationship and sexual satisfaction."

**Implication:** Overall couple arousal capacity matters more than similarity.

#### Finding 3: Similarity at High Levels Benefits Women

**Source:** Pawłowska, Janssen & Dewitte 2023 - EMA Study (94 couples)

> "Similarity at **high levels** of sexual arousal was associated with higher sexual satisfaction in women but not in men."

> "As long as sexual arousal levels within a couple are **sufficiently high**, sexual arousal similarity and discrepancy can be beneficial."

**Implication:** High + High pairing has measurable benefits, particularly for women's satisfaction.

#### SE Summary Table

| Scenario | Research Outcome | Compatibility Implication |
|----------|------------------|---------------------------|
| Both high SE (>0.65) | Best outcomes | Small positive modifier |
| High + Low mismatch | Acceptable - high level compensates | Neutral |
| Both low SE (<0.35) | Least favorable | Neutral or small negative |

---

### SIS-P (Performance Inhibition)

#### Finding 1: Similarity Can Compound Problems

**Source:** Lykins, Janssen et al. 2012

> "Greater similarity in the effects of anxiety and stress on sexuality was associated with **more** reported sexual arousal problems of wives."

**Implication:** Two people who both have performance anxiety may reinforce each other's anxiety rather than help.

#### Finding 2: Individual Factor, Not Dyadic

**Source:** Same study

> "Husbands' sexual arousal problems were related only to their own higher SIS1 scores."

**Implication:** SIS-P is primarily an individual experience. Partner's SIS-P score doesn't directly affect the other person.

#### Finding 3: Sensitive Brakes Predict Problems

**Source:** Emily Nagoski, "Come As You Are"

> "A sensitive brake is the strongest predictor of sexual problems of all kinds."

**Implication:** High SIS-P individuals need supportive contexts, not matching partners.

#### SIS-P Summary

| Aspect | Finding |
|--------|---------|
| Compatibility matching | **Not recommended** - similarity compounds problems |
| Partner awareness | Useful for understanding |
| Activity selection | **Recommended** - avoid performance-pressure activities for high SIS-P users |

---

### SIS-C (Consequence Inhibition)

#### Finding 1: Related to Risk Tolerance and Fidelity

**Source:** Kinsey Institute infidelity research

> "For every one unit increase [in SIS2], women were 13% less likely to have cheated and men were 7% less likely to have cheated."

> "Low SIS2 scores imply sexual arousal that is not inhibited by evidence of risk, compromising risk management."

**Implication:** SIS-C measures comfort with risk/exposure. High = cautious, Low = comfortable with risk.

#### Finding 2: Perceived Compatibility Matters

**Source:** Same research

> "Women who perceived **low compatibility in terms of sexual attitudes and values** were 2.9x more likely to cheat."

**Implication:** Alignment on comfort zones (which SIS-C reflects) matters for relationship stability.

#### Finding 3: Context and Safety

**Source:** Therapeutic literature

High SIS-C individuals need:
- Privacy and discretion
- Low risk of interruption/discovery
- Freedom from judgment

**Implication:** A significant mismatch (High SIS-C + Low SIS-C) could create friction around comfort zones.

#### SIS-C Summary

| Scenario | Implication |
|----------|-------------|
| Both high SIS-C | Both cautious - compatible comfort zone |
| Both low SIS-C | Both comfortable with risk - compatible |
| Both mid-range | Flexible, adaptable - positive signal |
| Significant mismatch (>0.4 delta) | Potential friction on risk tolerance |

---

## How Others Use These Signals

### Academic/Clinical Use

| Application | How It's Used |
|-------------|---------------|
| **Couples Therapy** | Communication tool - help partners understand each other's "brakes and accelerators" |
| **Sex Therapy** | Identify risk factors, tailor interventions |
| **Research** | Predict outcomes (satisfaction, dysfunction, risk behavior) |

### Dating/Matching Apps

**Finding: No one is algorithmically matching on SES/SIS.**

- No dating apps found using SES/SIS for compatibility scoring
- This would be a novel/pioneering implementation

### Existing Couples Tools

| Tool | Approach |
|------|----------|
| CouplesExplorer | Binary mutual interest matching (show overlaps only) |
| We Should Try It | Same - only show what both want |
| Quivre | Overall compatibility score from preferences |

**None use personality trait matching based on arousal patterns.**

### Validated Compatibility Instruments

**Sexual Compatibility with Spouse Questionnaire (SCSQ)** - 35 items, 4 factors:

1. Requirements of Sexual Relationship (18 items)
2. Sexual Agreement (7 items)
3. Contextual Obstacles (5 items)
4. Desirable Outcomes (5 items)

**Note:** SCSQ doesn't include SES/SIS - focuses on agreement/communication, not trait matching.

---

## Proposed Integration Approaches

### For SIS-C (Consequence Inhibition) → Compatibility

**Rationale:** Research supports that risk tolerance alignment matters for relationship outcomes.

**Proposed Logic:**

```python
def sisc_compatibility_modifier(sisc_a, sisc_b):
    delta = abs(sisc_a - sisc_b)
    both_mid = (0.35 <= sisc_a <= 0.65) and (0.35 <= sisc_b <= 0.65)

    if delta > 0.4:
        # Significant mismatch - potential friction on risk tolerance
        return -0.02  # -2% penalty

    elif both_mid:
        # Both flexible/adaptable - positive signal
        return +0.02  # +2% bonus

    else:
        # Both high or both low - aligned, neutral
        return 0.0
```

**SIS-C Modifier Table:**

| Scenario | Modifier | Rationale |
|----------|----------|-----------|
| Significant mismatch (delta > 0.4) | -2% | Risk tolerance friction |
| Both mid-range (0.35-0.65) | +2% | Flexible, adaptable |
| Both high (≥0.65) | 0% | Aligned (both cautious) |
| Both low (<0.35) | 0% | Aligned (both comfortable with risk) |

**Allocated Weight:** 2% (from Truth Overlap)

---

### For SE (Sexual Excitation) → Compatibility

**Rationale:** Research shows "both high" > "both low" for satisfaction outcomes. High-High pairs should score better than High-Avg pairs.

**Proposed Logic (Tiered):**

```python
HIGH = 0.65
LOW = 0.35

def se_compatibility_modifier(se_a, se_b):
    a_high = se_a >= HIGH
    b_high = se_b >= HIGH
    a_low = se_a < LOW
    b_low = se_b < LOW

    if a_high and b_high:
        # Both high - best outcome (mutual responsiveness)
        return 0.03  # Full 3%

    elif a_high or b_high:
        # One high - check what the other is
        other = se_b if a_high else se_a
        if other >= LOW:  # Other is mid-range
            return 0.015  # 1.5% - good but not optimal
        else:  # Other is low
            return 0.005  # 0.5% - high compensates somewhat

    elif a_low and b_low:
        # Both low - lowest arousal capacity
        return 0.0  # Neutral (no penalty, just no bonus)

    else:
        # Both mid-range or one mid + one low
        return 0.0  # Neutral
```

**SE Modifier Table:**

| Partner A | Partner B | Modifier | Rationale |
|-----------|-----------|----------|-----------|
| High (≥0.65) | High (≥0.65) | +3.0% | Best: mutual responsiveness |
| High (≥0.65) | Mid (0.35-0.65) | +1.5% | Good: one responsive, one flexible |
| High (≥0.65) | Low (<0.35) | +0.5% | Acceptable: high compensates |
| Mid | Mid | 0% | Neutral |
| Mid | Low | 0% | Neutral |
| Low | Low | 0% | Neutral (no bonus) |

**Allocated Weight:** 3% (from Truth Overlap)

---

### For SE → Activity Selection

**Rationale:** High SE users respond to variety/intensity; Low SE users benefit from buildup.

**Proposed Logic:**

- High SE couple → More variety, can handle intensity progression
- Low SE couple → Prioritize sensory buildup activities, slower pacing
- Mixed → Balance of both

**Implementation:** Inform activity sequencing and type balance, not filtering.

---

### For SIS-P (Performance Inhibition) → Activity Selection

**Rationale:** High SIS-P individuals need low-pressure contexts. This is individual, not dyadic.

**Proposed Logic:**

For users with high SIS-P (>0.65):
- Deprioritize "performance" activities (things that put someone "on the spot")
- Prioritize collaborative, low-pressure activities

**Implementation:** Activity filtering/scoring adjustment for individuals, not compatibility.

---

## Weight Considerations

### Current Compatibility Weights

| Component | Current Weight |
|-----------|---------------|
| Power Complement | 15% |
| Domain Similarity | 25% |
| Activity Overlap | 40% |
| Truth Overlap | 20% |
| **Total** | **100%** |

### Approved Rebalancing

Take **5%** from Truth Overlap:
- **3%** → SE (Sexual Excitation) Capacity
- **2%** → SIS-C (Consequence Inhibition) Alignment

### Final Weights

| Component | New Weight | Change |
|-----------|------------|--------|
| Power Complement | 15% | — |
| Domain Similarity | 25% | — |
| Activity Overlap | 40% | — |
| Truth Overlap | 15% | -5% |
| **SE Capacity** | **3%** | +3% (new) |
| **SIS-C Alignment** | **2%** | +2% (new) |
| **Total** | **100%** | — |

### Rationale for Weight Hierarchy

- **SE (3%) > SIS-C (2%)**: SE has stronger research support for affecting satisfaction outcomes
- **Both small**: Arousal factors are modifiers, not dominant signals - activity overlap (40%) remains the primary driver
- **From Truth**: Both arousal factors relate to openness/comfort, making Truth the logical source

---

## Key Takeaways

1. **SE affects compatibility via couple capacity** - High-High > High-Avg > others (3% weight)
2. **SIS-C affects compatibility via risk tolerance alignment** - significant mismatches create friction (2% weight)
3. **SIS-P should NOT be a compatibility factor** - similarity compounds problems
4. **SE informs activity selection** - pacing and intensity progression
5. **SIS-P informs activity selection** - avoid performance-pressure activities for high SIS-P users
6. **No one else is doing this** - Attuned would be pioneering SES/SIS-informed matching
7. **Light touch confirmed** - 5% total (3% SE + 2% SIS-C) from Truth Overlap

---

## Sources

### Primary Research

1. **Lykins, Janssen et al. (2012)** - "The effects of similarity in sexual excitation, inhibition, and mood on sexual arousal problems and sexual satisfaction in newlywed couples" - *Journal of Sexual Medicine*
   - https://pubmed.ncbi.nlm.nih.gov/22458268/

2. **Kim et al. (2021)** - "Are Couples More Satisfied When They Match in Sexual Desire? New Insights From Response Surface Analyses" - *Social Psychological and Personality Science*
   - https://journals.sagepub.com/doi/10.1177/1948550620926770

3. **Pawłowska, Janssen & Dewitte (2023)** - "The way you make me feel: an ecological momentary assessment study on couple similarity in sexual arousal" - *Journal of Sexual Medicine*
   - https://pubmed.ncbi.nlm.nih.gov/37344001/

4. **Bancroft & Janssen (2000/2007)** - Dual Control Model foundational papers
   - https://kinsey.indiana.edu/research/dual-control-model.html

### Applied/Clinical

5. **Emily Nagoski - "Come As You Are"** - Popular science book applying Dual Control Model
   - https://www.amazon.com/Come-You-Are-Surprising-Transform/dp/1476762090

6. **Kinsey Institute Infidelity Research**
   - https://medicalxpress.com/news/2011-06-insights-infidelity-sexual-personality-characteristics.html

### Instruments

7. **Sexual Compatibility with Spouse Questionnaire (SCSQ)**
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC7334741/

8. **SIS/SES-SF (Short Form)**
   - https://www.researchgate.net/publication/273126136

### Practical Application

9. **Couply - Brakes and Accelerators Guide**
   - https://www.couply.io/post/how-to-apply-the-sexual-brakes-and-accelerators

10. **Psychology Today - Mismatching in Sexual Desire**
    - https://www.psychologytoday.com/us/blog/dating-and-mating/202007/mismatching-in-sexual-desire-matters-less-than-you-think

---

## Decisions Made

- [x] Review research holistically
- [x] Decide on integration approach: **Both compatibility AND activity selection**
- [x] Determine specific weights: **SE 3%, SIS-C 2%** (from Truth Overlap)
- [x] Define SE tiered logic: High-High (+3%) > High-Mid (+1.5%) > High-Low (+0.5%) > others (0%)

## Next Steps

1. Create detailed implementation plan with:
   - Exact code changes to `compatibility/calculator.py`
   - Activity selection changes to `recommender/scoring.py`
   - Test cases for each scenario
2. Consider A/B testing strategy (if applicable)
3. Implement and verify with existing test suite
