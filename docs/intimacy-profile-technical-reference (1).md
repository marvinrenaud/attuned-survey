# Attuned Intimacy Profile: Technical Reference

**Version**: 0.4/0.5  
**Last Updated**: January 2026  
**Audience**: Internal team, technical collaborators

---

## 1. Scientific Foundation

### Sexual Excitation/Inhibition Model (SES/SIS)

The Dual Control Model, developed by Bancroft & Janssen at the Kinsey Institute, proposes that sexual response results from the balance between excitatory and inhibitory processes. Attuned implements an adapted version of the validated SES/SIS-2 scales.

**Three Subscales Measured:**

| Subscale | Code | Items | What It Captures |
|----------|------|-------|------------------|
| Sexual Excitation (SE) | A1–A4 | 4 | Responsiveness to sexual cues |
| Sexual Inhibition – Performance (SIS-P) | A5–A8 | 4 | Inhibition due to performance concerns |
| Sexual Inhibition – Consequence (SIS-C) | A9–A12 | 4 | Inhibition due to potential consequences |

**Scoring**: 7-point Likert scale (1–7) → normalized to 0–1.

**Interpretation Bands**:
- ≤0.30: Low
- 0.31–0.55: Moderate-Low
- 0.56–0.75: Moderate-High
- >0.75: High

### Erotic Preferences Inventories

Drawing from instruments including the Wilson Sex Fantasy Questionnaire and Carnal Calibration frameworks, Attuned maps specific activity interests using a graduated interest scale. Each activity is rated on comfort/interest level and normalized to 0–1.

**Thresholds**:
- ≥0.7: Yes (wants this)
- 0.3–0.69: Maybe (open/curious)
- <0.3: No (not interested)

---

## 2. Profile Components

### 2.1 Arousal Propensity

**Source**: Questions A1–A12

**Output**:
```json
{
  "sexual_excitation": 0.72,
  "inhibition_performance": 0.45,
  "inhibition_consequence": 0.33,
  "interpretation": {
    "se": "Moderate-High",
    "sis_p": "Moderate-Low",
    "sis_c": "Moderate-Low"
  }
}
```

### 2.2 Power Dynamic

**Source**: Questions A13–A16  
- Top items: A13, A15  
- Bottom items: A14, A16

**Algorithm**:
1. Calculate Top score and Bottom score (0–100 scale)
2. Apply thresholds:
   - `THETA_FLOOR = 30` (minimum engagement threshold)
   - `DELTA_BAND = 15` (Switch determination band)

**Orientation Logic**:

| Condition | Orientation |
|-----------|-------------|
| Both scores < 30 | Versatile/Undefined |
| \|Top − Bottom\| ≤ 15 AND both ≥ 30 | Switch |
| Top > Bottom | Top |
| Bottom > Top | Bottom |

**Confidence Calculation**:
- Top: `(top_score/100) × (1 − 0.3 × bottom_score/100)`
- Bottom: `(bottom_score/100) × (1 − 0.3 × top_score/100)`
- Switch: `min(top_score, bottom_score) / 100`

**Output**:
```json
{
  "orientation": "Top",
  "top_score": 78,
  "bottom_score": 42,
  "confidence": 0.68,
  "interpretation": "Moderate confidence Top"
}
```

### 2.3 Domain Scores

Five domains calculated from activity preferences (0–100 scale):

| Domain | Activities Included |
|--------|---------------------|
| **Sensation** | Biting, spanking (moderate/hard), slapping, choking, spitting, watersports |
| **Connection** | Massage, oral body, moaning, posing, revealing clothing, truth topics (fantasies, insecurities, future fantasies, feeling desired) |
| **Power** | Restraints, blindfold, orgasm control, protocols, commands, begging |
| **Exploration** | Roleplay, stripping, watching strip, solo pleasure (self/watching), dancing, spitting, watersports |
| **Verbal** | Dirty talk, moaning, roleplay, commands, begging |

**Calculation**: Mean of included activity scores × 100, rounded to integer.

### 2.4 Activities

Structured by category with give/receive or self/watching directionality:

**Categories**:
- `physical_touch`: massage, biting, spanking, slapping, choking, spitting, watersports
- `oral`: oral_body, oral_genital
- `power_exchange`: restraints, blindfold, orgasm_control, protocols
- `verbal_roleplay`: dirty_talk, moaning, roleplay, commands, begging
- `display_performance`: posing, revealing_clothing, stripping, solo_pleasure, dancing, watching variants

### 2.5 Truth Topics

Conversation comfort levels (0–1 scale):
- past_experiences
- fantasies
- turn_ons
- turn_offs
- insecurities
- boundaries
- future_fantasies
- feeling_desired

### 2.6 Boundaries

**Source**: Question C1

Hard limits stored as array of category identifiers. Maps to restricted activities:

| Boundary ID | Restricted Activities |
|-------------|----------------------|
| impact_play | spanking, slapping, biting |
| restraints_bondage | restraints, blindfold |
| breath_play | choking |
| degradation_humiliation | degradation, humiliation |
| public_activities | exhibitionism, voyeurism, public_play |
| recording | recording, photos, videos |
| anal_activities | anal, rimming |
| watersports | watersports, scat |

### 2.7 Anatomy

**Source**: Questions D1, D2

- `anatomy_self`: What the user has (penis, vagina, breasts)
- `anatomy_preference`: What the user enjoys in partners (same options, or any/all)

---

## 3. Compatibility Algorithm

### Weighted Components

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Power Complement | 15% | How orientations work together |
| Domain Similarity | 25% | Alignment in domain scores |
| Activity Overlap | 40% | Shared and complementary interests |
| Truth Overlap | 20% | Mutual conversation comfort |

### 3.1 Power Complement (0–1)

| Pairing | Score |
|---------|-------|
| Top + Bottom | ~1.0 (adjusted by intensity alignment) |
| Switch + Switch | 0.85 |
| One Switch | 0.75 |
| Same pole (Top/Top or Bottom/Bottom) | 0.50 |

### 3.2 Domain Similarity (0–1)

**For Top/Bottom pairs**: Uses minimum threshold approach for Exploration and Verbal domains (divergence is acceptable if both exceed 50).

**For Switch/Switch or same-pole**: Standard distance calculation across all five domains.

Formula: `1 − |score_a − score_b|` averaged across domains.

### 3.3 Activity Overlap (0–1)

**Asymmetric Directional Jaccard** (Top/Bottom pairs):

Recognizes complementary pairings:
- `_give` ↔ `_receive` (e.g., spanking_give matches spanking_receive)
- `_self` ↔ `_watching` (e.g., stripping_self matches watching_strip)

**Weighting**:
- Primary axis (80%): Does Top want to GIVE what Bottom wants to RECEIVE?
- Secondary axis (20%): Does Bottom want to GIVE what Top wants to RECEIVE?

**Same-Pole Jaccard** (Top/Top or Bottom/Bottom pairs):

Both wanting the same role is incompatible. Partial credit given for versatility (comfortable in both roles for an activity).

**Switch/Switch pairs**: Standard Jaccard coefficient.

### 3.4 Truth Overlap (0–1)

| Condition | Score |
|-----------|-------|
| Both ≥ 0.5 | min(score_a, score_b) |
| Both < 0.5 | 0.5 (neutral) |
| Mismatch | 0.3 |

**Same-pole penalty**: Truth overlap multiplied by 0.5 for Top/Top or Bottom/Bottom pairs.

### 3.5 Boundary Conflict Detection

Cross-checks each player's high-interest activities (≥0.7) against partner's hard limits. Each conflict applies a **20% penalty** to overall score.

### 3.6 Final Score

```
overall_score = (0.15 × power_complement) 
              + (0.25 × domain_similarity) 
              + (0.40 × activity_overlap) 
              + (0.20 × truth_overlap) 
              − (0.20 × boundary_conflict_count)
```

**Interpretation Bands**:
- ≥85%: Exceptional compatibility
- 70–84%: High compatibility
- 55–69%: Moderate compatibility
- 40–54%: Lower compatibility
- <40%: Challenging compatibility

---

## 4. Output Artifacts

### Mutual Activities
Activities where both partners score ≥0.7.

### Growth Opportunities
Activities where one partner scores ≥0.7 and the other is 0.3–0.69 (curious but not certain).

### Mutual Truth Topics
Topics where both partners score ≥0.5.

### Blocked Activities
Combined hard limits from both partners—never recommended.

### Boundary Conflicts
Explicit listing when one partner's strong interest conflicts with the other's hard limit.

---

## 5. Question ID Reference

| ID Range | Component |
|----------|-----------|
| A1–A4 | Sexual Excitation (SE) |
| A5–A8 | Sexual Inhibition – Performance (SIS-P) |
| A9–A12 | Sexual Inhibition – Consequence (SIS-C) |
| A13, A15 | Top orientation |
| A14, A16 | Bottom orientation |
| B* | Activity preferences |
| C1 | Hard limits |
| D1 | Anatomy self |
| D2 | Anatomy preference |
| T* | Truth topic comfort |

---

## 6. Version History

| Version | Changes |
|---------|---------|
| 0.4 | Initial production release with SES/SIS, power dynamic, 5 domains |
| 0.5 | Asymmetric directional Jaccard, same-pole handling, boundary conflict detection |

---

*Document maintained by Attuned engineering team.*
