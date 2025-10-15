# ATTUNED INTIMACY SURVEY v0.4
## Scientifically Grounded Survey for Personalized Truth or Dare

**Total Questions: 66**  
**Scientific Foundation:** SES/SIS Dual Control Model + Erotic Preferences Inventory Methods  
**Target Completion Time:** 12-15 minutes

---

## SECTION 1: AROUSAL PROPENSITY (12 Questions)
**Purpose:** Measure sexual excitation and inhibition propensity using validated SES/SIS scales  
**Format:** 7-point Likert scale (1 = Strongly Disagree, 7 = Strongly Agree)

### Sexual Excitation (SE) — 4 items
1. I am easily aroused by sensory cues (touch, scent, visuals)
2. I quickly respond to erotic stimuli or situations  
3. Thoughts or fantasies easily turn me on
4. My partner's arousal increases my own arousal

### Sexual Inhibition - Performance (SIS-P) — 4 items
5. My arousal decreases if I'm worried about my performance
6. I lose interest if I'm uncertain what my partner wants
7. Concerns about technique affect my arousal
8. Pressure to perform reduces my desire

### Sexual Inhibition - Consequences (SIS-C) — 4 items
9. My arousal drops if I'm worried about being caught or interrupted
10. Privacy concerns affect my responsiveness
11. Fear of judgment reduces my desire
12. I feel uncomfortable if potential consequences feel risky

---

## SECTION 2: POWER DYNAMICS (4 Questions)
**Purpose:** Assess directional power dynamic preferences  
**Format:** 7-point Likert scale (1 = Strongly Disagree, 7 = Strongly Agree)

13. I enjoy **giving** clear direction or commands during intimate activities
14. I enjoy **following** direction or commands during intimate activities
15. I like being **in the dominant role** during intimate scenarios
16. I like being **in the submissive role** during intimate scenarios

---

## SECTION 3: DARE ACTIVITIES (40 Questions)
**Instructions:** "Are you currently open to exploring these activities with a partner?"  
**Format:** Y/M/N (Yes / Maybe / No) for each item  
**Note:** Directional items have (a) receiving / (b) giving variants

### 3A: PHYSICAL TOUCH & SENSATION (14 items)

#### **Gentle/Light Intensity:**
17a. Massage (receiving) / 17b. Massage (giving)
18a. Hair pulling - gentle (my hair pulled) / 18b. Hair pulling - gentle (I pull)

#### **Moderate Intensity:**
19a. Biting or scratching - moderate (on me) / 19b. Biting or scratching - moderate (I do)
20a. Spanking - moderate (on me) / 20b. Spanking - moderate (I deliver)
21a. Using hands/fingers on genitals (on me) / 21b. Using hands/fingers on partner's genitals (I do)

#### **Intense/Extreme:**
22a. Spanking - hard (on me) / 22b. Spanking - hard (I deliver)
23a. Slapping (face or body) (on me) / 23b. Slapping (face or body) (I deliver)
24a. Choking or breath play (on me) / 24b. Choking or breath play (I do)
25a. Spitting (on me) / 25b. Spitting (I do)
26a. Watersports/golden showers (on me) / 26b. Watersports/golden showers (I do)

### 3B: ORAL ACTIVITIES (4 items)

27a. Oral sex on genitals (receiving) / 27b. Oral sex on genitals (giving)
28a. Oral stimulation on other body parts - chest, neck, ears, inner thighs, etc. (on me) / 28b. Oral stimulation on other body parts (I do)

### 3C: ANAL ACTIVITIES (4 items)

29a. Anal stimulation with fingers or small toys (on me) / 29b. Anal stimulation with fingers or small toys (I do)
30a. Rimming - oral stimulation of anus (on me) / 30b. Rimming - oral stimulation of anus (I do)

### 3D: POWER EXCHANGE & CONTROL (8 items)

#### **Physical Control:**
31a. Being restrained (hands held, ties, cuffs, rope) (on me) / 31b. Restraining partner (I do)
32a. Blindfolding or sensory deprivation (on me) / 32b. Blindfolding or sensory deprivation (I do)

#### **Orgasm Control (includes edging, denial, forced):**
33a. Orgasm control - edging, denial, forced orgasm (on me) / 33b. Orgasm control - edging, denial, forced orgasm (I control)
34a. Following strict commands or protocols during intimate play (I follow) / 34b. Giving strict commands or protocols during intimate play (I give)

### 3E: VERBAL & ROLEPLAY (5 items)
*During intimate activities or moments:*

35. Dirty talk or explicit language
36. Moaning or vocal encouragement
37. Roleplay scenarios (boss/employee, strangers, teacher/student, etc.)
38. Giving or receiving commands
39. Begging or pleading (in play)

### 3F: DISPLAY & PERFORMANCE (5 items)

40a. Stripping or undressing slowly (me performing) / 40b. Watching partner strip (I watch)
41a. Being watched during solo pleasure (me) / 41b. Watching partner during solo pleasure (I watch)
42. Posing or being positioned for viewing
43. Dancing sensually
44. Wearing revealing or fantasy clothing/lingerie

---

## SECTION 4: TRUTH TOPICS (8 Questions)
**Instructions:** "What topics are you willing to discuss openly during intimate conversations?"  
**Format:** Y/M/N (Yes / Maybe / No)

45. Past sexual or romantic experiences
46. Current fantasies or desires
47. Turn-ons and attractions
48. Turn-offs and dislikes
49. Insecurities or vulnerabilities about intimacy
50. Boundaries and limits
51. Fantasies about the future with my partner
52. What makes me feel most desired or wanted

---

## SECTION 5: BOUNDARIES & SAFETY (2 Questions)

**Question 53:** Select ANY of the following that are **hard boundaries** (absolutely not interested, now or in foreseeable future):

*Check all that apply:*
- [ ] Impact play (spanking, slapping, whipping)
- [ ] Restraints or bondage (ropes, cuffs, etc.)
- [ ] Breath play or choking
- [ ] Degradation or humiliation (verbal or physical)
- [ ] Public or semi-public activities
- [ ] Recording, photos, or videos of intimate activities
- [ ] Roleplay scenarios
- [ ] Multi-partner scenarios or group activities
- [ ] Toys or props
- [ ] Anal activities
- [ ] Watersports or other bodily fluids
- [ ] Other (please specify): _______________

**Question 54:** Any other specific activities, scenarios, topics, or contexts you want to ensure are avoided? *(Open text field)*

---

# CALCULATION METHODOLOGY v0.4

## INDIVIDUAL PROFILE OUTPUT

### Profile Component 1: Arousal Propensity Scores

```javascript
// Calculate raw scores (1-7 scale responses)
SE_raw = mean([Q1, Q2, Q3, Q4])
SIS_P_raw = mean([Q5, Q6, Q7, Q8])
SIS_C_raw = mean([Q9, Q10, Q11, Q12])

// Normalize to 0-1 range
arousal_profile = {
  sexual_excitation: (SE_raw - 1) / 6,        // 0 = very low, 1 = very high
  inhibition_performance: (SIS_P_raw - 1) / 6, // 0 = very low, 1 = very high
  inhibition_consequence: (SIS_C_raw - 1) / 6  // 0 = very low, 1 = very high
}
```

**Interpretation Bands:**
- 0.00-0.30: Low
- 0.31-0.55: Moderate-Low
- 0.56-0.75: Moderate-High
- 0.76-1.00: High

---

### Profile Component 2: Power Dynamic Orientation

```javascript
// Calculate raw scores (1-7 scale)
Top_items = [Q13, Q15]  // giving direction, being dominant
Bottom_items = [Q14, Q16]  // following direction, being submissive

Top_raw = mean(Top_items)
Bottom_raw = mean(Bottom_items)

// Normalize to 0-100 scale
Top_score = ((Top_raw - 1) / 6) * 100
Bottom_score = ((Bottom_raw - 1) / 6) * 100

// Determine orientation
θ_floor = 30  // minimum score to register preference
δ_band = 15   // tie-breaker band for switch

if (Top_score < θ_floor && Bottom_score < θ_floor) {
  orientation = "Versatile/Undefined"
  confidence = max(Top_score, Bottom_score) / 100
} else if (abs(Top_score - Bottom_score) <= δ_band && 
           min(Top_score, Bottom_score) >= θ_floor) {
  orientation = "Switch"
  confidence = min(Top_score, Bottom_score) / 100
} else if (Top_score > Bottom_score) {
  orientation = "Top"
  confidence = (Top_score / 100) * (1 - 0.3 * (Bottom_score / 100))
} else {
  orientation = "Bottom"
  confidence = (Bottom_score / 100) * (1 - 0.3 * (Top_score / 100))
}

power_dynamic = {
  orientation: orientation,  // "Top", "Bottom", "Switch", "Versatile/Undefined"
  top_score: Top_score,      // 0-100
  bottom_score: Bottom_score, // 0-100
  confidence: confidence      // 0-1
}
```

**Confidence Bands:**
- 0.00-0.30: Low (exploratory/emerging)
- 0.31-0.60: Moderate (present but flexible)
- 0.61-0.85: High (clear preference)
- 0.86-1.00: Very high (primary identity)

---

### Profile Component 3: Activity Interest Map

**Response Encoding:**
- Yes (Y) = 1.0
- Maybe (M) = 0.5
- No (N) = 0.0

```javascript
activities = {
  physical_touch: {
    massage_receive: Q17a_value,      // 1.0 / 0.5 / 0.0
    massage_give: Q17b_value,
    hair_pull_gentle_receive: Q18a_value,
    hair_pull_gentle_give: Q18b_value,
    biting_moderate_receive: Q19a_value,
    biting_moderate_give: Q19b_value,
    spanking_moderate_receive: Q20a_value,
    spanking_moderate_give: Q20b_value,
    hands_genitals_receive: Q21a_value,
    hands_genitals_give: Q21b_value,
    spanking_hard_receive: Q22a_value,
    spanking_hard_give: Q22b_value,
    slapping_receive: Q23a_value,
    slapping_give: Q23b_value,
    choking_receive: Q24a_value,
    choking_give: Q24b_value,
    spitting_receive: Q25a_value,
    spitting_give: Q25b_value,
    watersports_receive: Q26a_value,
    watersports_give: Q26b_value
  },
  
  oral: {
    oral_sex_receive: Q27a_value,
    oral_sex_give: Q27b_value,
    oral_body_receive: Q28a_value,
    oral_body_give: Q28b_value
  },
  
  anal: {
    anal_fingers_toys_receive: Q29a_value,
    anal_fingers_toys_give: Q29b_value,
    rimming_receive: Q30a_value,
    rimming_give: Q30b_value
  },
  
  power_exchange: {
    restraints_receive: Q31a_value,
    restraints_give: Q31b_value,
    blindfold_receive: Q32a_value,
    blindfold_give: Q32b_value,
    orgasm_control_receive: Q33a_value,
    orgasm_control_give: Q33b_value,
    protocols_follow: Q34a_value,
    protocols_give: Q34b_value
  },
  
  verbal_roleplay: {
    dirty_talk: Q35_value,
    moaning: Q36_value,
    roleplay: Q37_value,
    commands: Q38_value,
    begging: Q39_value
  },
  
  display_performance: {
    stripping_me: Q40a_value,
    watching_strip: Q40b_value,
    watched_solo_pleasure: Q41a_value,
    watching_solo_pleasure: Q41b_value,
    posing: Q42_value,
    dancing: Q43_value,
    revealing_clothing: Q44_value
  }
}
```

---

### Profile Component 4: Aggregate Domain Scores

These aggregate scores help with high-level matching and visualization.

```javascript
// SENSATION DOMAIN: Physical intensity across touch, impact, sensation play
sensation_items = [
  Q19a, Q19b, Q20a, Q20b, Q22a, Q22b, Q23a, Q23b, 
  Q24a, Q24b, Q25a, Q25b, Q26a, Q26b  // moderate to extreme physical
]
sensation_score = mean(sensation_items) * 100  // 0-100

// CONNECTION DOMAIN: Emotional intimacy, affection, vulnerability
connection_items = [
  Q17a, Q17b,  // massage
  Q28a, Q28b,  // oral on body (intimate)
  Q36,  // moaning (connected expression)
  Q42,  // posing (vulnerability)
  Q44,  // revealing clothing (vulnerability)
  Q46,  // fantasies topic
  Q49,  // insecurities topic
  Q51,  // future fantasies topic
  Q52   // what makes you feel desired topic
]
connection_score = mean(connection_items) * 100  // 0-100

// POWER DOMAIN: Control, dominance/submission, structure
power_items = [
  Q31a, Q31b, Q32a, Q32b, Q33a, Q33b, Q34a, Q34b,  // power exchange activities
  Q38,  // commands
  Q39   // begging
]
power_score = mean(power_items) * 100  // 0-100

// EXPLORATION DOMAIN: Novelty, variety, risk-taking
exploration_items = [
  Q37,  // roleplay
  Q40a, Q40b, Q41a, Q41b,  // display/watching
  Q43,  // dancing
  Q25a, Q25b, Q26a, Q26b  // extreme/edge activities
]
exploration_score = mean(exploration_items) * 100  // 0-100

// VERBAL DOMAIN: Communication, expression, talking
verbal_score = mean([Q35, Q36, Q37, Q38, Q39]) * 100  // 0-100

domain_scores = {
  sensation: sensation_score,      // 0-100
  connection: connection_score,     // 0-100
  power: power_score,              // 0-100
  exploration: exploration_score,   // 0-100
  verbal: verbal_score             // 0-100
}
```

---

### Profile Component 5: Truth Topics Openness

```javascript
truth_topics = {
  past_experiences: Q45_value,     // 1.0 / 0.5 / 0.0
  fantasies: Q46_value,
  turn_ons: Q47_value,
  turn_offs: Q48_value,
  insecurities: Q49_value,
  boundaries: Q50_value,
  future_fantasies: Q51_value,
  feeling_desired: Q52_value
}

// Calculate aggregate openness score
truth_openness_score = mean(Object.values(truth_topics)) * 100  // 0-100
```

---

### Profile Component 6: Boundaries Map

```javascript
// Parse Q53 checkbox selections
hard_boundaries = [
  // array of selected boundary categories from Q53
  // e.g., ["impact_play", "public_activities", "recording"]
]

// Parse Q54 open text
additional_boundaries = Q54_text  // free text string

boundaries = {
  hard_limits: hard_boundaries,           // array of strings
  additional_notes: additional_boundaries  // string
}
```

---

### COMPLETE INDIVIDUAL PROFILE STRUCTURE

```json
{
  "user_id": "user_123",
  "profile_version": "0.4",
  "timestamp": "2025-10-14T20:30:00Z",
  
  "arousal_propensity": {
    "sexual_excitation": 0.72,
    "inhibition_performance": 0.31,
    "inhibition_consequence": 0.54,
    "interpretation": {
      "se": "Moderate-High",
      "sis_p": "Moderate-Low",
      "sis_c": "Moderate-High"
    }
  },
  
  "power_dynamic": {
    "orientation": "Switch",
    "top_score": 65,
    "bottom_score": 58,
    "confidence": 0.58,
    "interpretation": "Moderate confidence Switch"
  },
  
  "domain_scores": {
    "sensation": 61,
    "connection": 75,
    "power": 68,
    "exploration": 42,
    "verbal": 71
  },
  
  "activities": {
    "physical_touch": { /* detailed Y/M/N map */ },
    "oral": { /* detailed Y/M/N map */ },
    "anal": { /* detailed Y/M/N map */ },
    "power_exchange": { /* detailed Y/M/N map */ },
    "verbal_roleplay": { /* detailed Y/M/N map */ },
    "display_performance": { /* detailed Y/M/N map */ }
  },
  
  "truth_topics": {
    "past_experiences": 1.0,
    "fantasies": 0.5,
    "turn_ons": 1.0,
    "turn_offs": 1.0,
    "insecurities": 0.5,
    "boundaries": 1.0,
    "future_fantasies": 1.0,
    "feeling_desired": 1.0,
    "openness_score": 81
  },
  
  "boundaries": {
    "hard_limits": ["public_activities", "recording", "multi_partner"],
    "additional_notes": "No father/daughter roleplay scenarios"
  },
  
  "activity_tags": {
    "open_to_gentle": true,
    "open_to_moderate": true,
    "open_to_intense": false,
    "open_to_oral": true,
    "open_to_anal": false,
    "open_to_restraints": true,
    "open_to_orgasm_control": true,
    "open_to_roleplay": true,
    "open_to_display": true,
    "open_to_group": false
  }
}
```

---

## COMPATIBILITY MAPPING CALCULATION

### Purpose
Map two or more user profiles to identify:
1. **Mutual interests** (what ALL players are open to)
2. **Growth opportunities** (what some are open to, others are maybe)
3. **Power complementarity** (Top/Bottom fit)
4. **Boundary conflicts** (activities blocked by any player)
5. **Overall compatibility score** (0-100)

---

### Algorithm: Two-Player Compatibility

```javascript
function calculateCompatibility(playerA, playerB) {
  
  // STEP 1: Power Complementarity (0-1 scale)
  let power_complement = 0
  
  if (playerA.power_dynamic.orientation === "Switch" && 
      playerB.power_dynamic.orientation === "Switch") {
    // Both switches: high compatibility
    power_complement = 0.90
  } else if (
    (playerA.power_dynamic.orientation === "Top" && playerB.power_dynamic.orientation === "Bottom") ||
    (playerA.power_dynamic.orientation === "Bottom" && playerB.power_dynamic.orientation === "Top")
  ) {
    // Complementary: scale by confidence scores
    const avg_confidence = (playerA.power_dynamic.confidence + playerB.power_dynamic.confidence) / 2
    power_complement = 0.85 + (0.15 * avg_confidence)  // 0.85 to 1.0
  } else if (
    (playerA.power_dynamic.orientation === "Switch" || 
     playerA.power_dynamic.orientation === "Versatile/Undefined") &&
    (playerB.power_dynamic.orientation === "Top" || 
     playerB.power_dynamic.orientation === "Bottom")
  ) {
    // One versatile/switch: moderate compatibility
    power_complement = 0.70
  } else {
    // Both same pole or undefined: lower compatibility
    power_complement = 0.40
  }
  
  
  // STEP 2: Domain Similarity (0-1 scale)
  const sensation_dist = 1 - Math.abs(playerA.domain_scores.sensation - playerB.domain_scores.sensation) / 100
  const connection_dist = 1 - Math.abs(playerA.domain_scores.connection - playerB.domain_scores.connection) / 100
  const power_dist = 1 - Math.abs(playerA.domain_scores.power - playerB.domain_scores.power) / 100
  const exploration_dist = 1 - Math.abs(playerA.domain_scores.exploration - playerB.domain_scores.exploration) / 100
  const verbal_dist = 1 - Math.abs(playerA.domain_scores.verbal - playerB.domain_scores.verbal) / 100
  
  const domain_similarity = (sensation_dist + connection_dist + power_dist + exploration_dist + verbal_dist) / 5
  
  
  // STEP 3: Activity-Level Overlap (Jaccard-style per category)
  function calculateCategoryJaccard(activitiesA, activitiesB, categoryKey) {
    const categoryA = activitiesA[categoryKey]
    const categoryB = activitiesB[categoryKey]
    
    const keys = Object.keys(categoryA)
    let mutual_yes = 0
    let at_least_one_yes = 0
    
    keys.forEach(key => {
      const valA = categoryA[key]
      const valB = categoryB[key]
      
      // Mutual interest: both Y or both M or Y+M combination
      if (valA >= 0.5 && valB >= 0.5) {
        mutual_yes += 1
      }
      
      // At least one interested
      if (valA >= 0.5 || valB >= 0.5) {
        at_least_one_yes += 1
      }
    })
    
    if (at_least_one_yes === 0) return 0
    return mutual_yes / at_least_one_yes  // Jaccard coefficient
  }
  
  const jaccard_physical = calculateCategoryJaccard(
    playerA.activities, playerB.activities, 'physical_touch'
  )
  const jaccard_oral = calculateCategoryJaccard(
    playerA.activities, playerB.activities, 'oral'
  )
  const jaccard_anal = calculateCategoryJaccard(
    playerA.activities, playerB.activities, 'anal'
  )
  const jaccard_power = calculateCategoryJaccard(
    playerA.activities, playerB.activities, 'power_exchange'
  )
  const jaccard_verbal = calculateCategoryJaccard(
    playerA.activities, playerB.activities, 'verbal_roleplay'
  )
  const jaccard_display = calculateCategoryJaccard(
    playerA.activities, playerB.activities, 'display_performance'
  )
  
  const activity_overlap = (
    jaccard_physical + jaccard_oral + jaccard_anal + 
    jaccard_power + jaccard_verbal + jaccard_display
  ) / 6
  
  
  // STEP 4: Boundary Gate (hard veto)
  // If any hard boundary of Player A conflicts with interests of Player B (or vice versa), reduce score
  let boundary_penalty = 0
  
  // Check if any activity Player B wants to do is in Player A's hard limits
  const conflictingBoundaries = checkBoundaryConflicts(playerA, playerB)
  if (conflictingBoundaries.length > 0) {
    boundary_penalty = 0.2 * conflictingBoundaries.length  // -0.2 per conflict
  }
  
  
  // STEP 5: Truth Topics Overlap
  const truth_keys = Object.keys(playerA.truth_topics).filter(k => k !== 'openness_score')
  let mutual_truth_topics = 0
  truth_keys.forEach(key => {
    if (playerA.truth_topics[key] >= 0.5 && playerB.truth_topics[key] >= 0.5) {
      mutual_truth_topics += 1
    }
  })
  const truth_overlap = mutual_truth_topics / truth_keys.length
  
  
  // STEP 6: Weighted Final Score
  let compatibility_score = (
    0.15 * power_complement +      // 15% power fit
    0.25 * domain_similarity +     // 25% domain alignment
    0.40 * activity_overlap +      // 40% activity match (most important)
    0.20 * truth_overlap           // 20% conversational openness
  )
  
  // Apply boundary penalty
  compatibility_score = Math.max(0, compatibility_score - boundary_penalty)
  
  // Convert to 0-100 scale
  compatibility_score = Math.round(compatibility_score * 100)
  
  return {
    overall_score: compatibility_score,
    breakdown: {
      power_complement: Math.round(power_complement * 100),
      domain_similarity: Math.round(domain_similarity * 100),
      activity_overlap: Math.round(activity_overlap * 100),
      truth_overlap: Math.round(truth_overlap * 100),
      boundary_conflicts: conflictingBoundaries
    }
  }
}

function checkBoundaryConflicts(playerA, playerB) {
  // Simplified: check if hard limits of A conflict with high-interest activities of B
  const conflicts = []
  
  // Map boundary categories to activity keys
  const boundaryMap = {
    'impact_play': ['spanking_moderate_give', 'spanking_hard_give', 'slapping_give'],
    'restraints_bondage': ['restraints_give'],
    'breath_play': ['choking_give'],
    'anal_activities': ['anal_fingers_toys_give', 'rimming_give'],
    'public_activities': [],  // would need context flags
    'recording': [],  // would need context flags
    'roleplay': ['roleplay'],
    'multi_partner': [],  // would need context flags
    'toys_props': []  // would need separate toy questions
  }
  
  playerA.boundaries.hard_limits.forEach(limit => {
    const activityKeys = boundaryMap[limit] || []
    activityKeys.forEach(actKey => {
      // Check if this activity appears in any category in B's profile with high interest
      Object.values(playerB.activities).forEach(category => {
        if (category[actKey] && category[actKey] >= 0.5) {
          conflicts.push({
            player: 'A',
            boundary: limit,
            conflicting_activity: actKey
          })
        }
      })
    })
  })
  
  // Repeat for playerB boundaries vs playerA activities
  playerB.boundaries.hard_limits.forEach(limit => {
    const activityKeys = boundaryMap[limit] || []
    activityKeys.forEach(actKey => {
      Object.values(playerA.activities).forEach(category => {
        if (category[actKey] && category[actKey] >= 0.5) {
          conflicts.push({
            player: 'B',
            boundary: limit,
            conflicting_activity: actKey
          })
        }
      })
    })
  })
  
  return conflicts
}
```

---

### Compatibility Output Structure

```json
{
  "players": ["user_123", "user_456"],
  "compatibility_version": "0.4",
  "timestamp": "2025-10-14T20:35:00Z",
  
  "overall_compatibility": {
    "score": 76,
    "interpretation": "High compatibility"
  },
  
  "breakdown": {
    "power_complement": 88,
    "domain_similarity": 72,
    "activity_overlap": 79,
    "truth_overlap": 85,
    "boundary_conflicts": []
  },
  
  "mutual_activities": {
    "physical_touch": [
      "massage_receive", "massage_give", 
      "hair_pull_gentle_receive", "hair_pull_gentle_give",
      "biting_moderate_receive", "biting_moderate_give",
      "spanking_moderate_receive", "spanking_moderate_give",
      "hands_genitals_receive", "hands_genitals_give"
    ],
    "oral": [
      "oral_sex_receive", "oral_sex_give",
      "oral_body_receive", "oral_body_give"
    ],
    "anal": [],  // both marked N
    "power_exchange": [
      "restraints_receive", "restraints_give",
      "blindfold_receive", "blindfold_give",
      "orgasm_control_receive", "orgasm_control_give"
    ],
    "verbal_roleplay": [
      "dirty_talk", "moaning", "roleplay", "commands"
    ],
    "display_performance": [
      "stripping_me", "watching_strip",
      "dancing", "revealing_clothing"
    ]
  },
  
  "growth_opportunities": {
    "physical_touch": [
      {
        "activity": "spanking_hard",
        "playerA": "yes",
        "playerB": "maybe"
      }
    ],
    "exploration": [
      {
        "activity": "watched_solo_pleasure",
        "playerA": "maybe",
        "playerB": "yes"
      }
    ]
  },
  
  "mutual_truth_topics": [
    "past_experiences", "fantasies", "turn_ons", 
    "turn_offs", "boundaries", "future_fantasies", "feeling_desired"
  ],
  
  "blocked_activities": {
    "reason": "hard_boundaries",
    "activities": []  // none in this example
  }
}
```

---

## AI ENGINE INPUT FORMAT

### Purpose
Provide the AI activity generator with structured, actionable data to create personalized Truth or Dare prompts.

### Input Structure for Activity Generation

```json
{
  "session_id": "session_789",
  "players": [
    {
      "id": "user_123",
      "display_name": "Player 1",
      "arousal_profile": {
        "se": 0.72,
        "sis_p": 0.31,
        "sis_c": 0.54
      },
      "power_role": "Switch",
      "domain_preferences": {
        "sensation": 61,
        "connection": 75,
        "power": 68,
        "exploration": 42,
        "verbal": 71
      }
    },
    {
      "id": "user_456",
      "display_name": "Player 2",
      "arousal_profile": {
        "se": 0.65,
        "sis_p": 0.42,
        "sis_c": 0.38
      },
      "power_role": "Bottom",
      "domain_preferences": {
        "sensation": 58,
        "connection": 82,
        "power": 71,
        "exploration": 35,
        "verbal": 68
      }
    }
  ],
  
  "mutual_activities": {
    "allowed_dare_types": [
      "massage", "kissing", "hair_pulling_gentle", "biting_moderate",
      "spanking_moderate", "hands_genitals", "oral_sex", "oral_body",
      "restraints", "blindfold", "orgasm_control", "protocols",
      "dirty_talk", "moaning", "roleplay", "commands",
      "stripping", "watching", "dancing", "revealing_clothing"
    ],
    "allowed_truth_topics": [
      "past_experiences", "fantasies", "turn_ons", 
      "turn_offs", "boundaries", "future_fantasies", "feeling_desired"
    ]
  },
  
  "blocked_activities": [
    "anal_activities", "watersports", "public_activities", 
    "recording", "multi_partner"
  ],
  
  "intensity_level": "moderate",  // "gentle", "moderate", "intense"
  
  "context_flags": {
    "power_dynamic_active": true,
    "high_connection_preference": true,
    "exploration_cautious": true
  },
  
  "previous_activities": [
    // array of recently used activities to avoid repetition
    "massage_give", "dirty_talk", "past_experiences"
  ]
}
```

---

## INTERPRETATION GUIDE FOR PROFILES

### For Individual Users:

**Arousal Propensity Interpretation:**
- **High SE + Low SIS**: Easily aroused, less prone to inhibition → adventurous, spontaneous
- **High SE + High SIS**: Responsive but needs the right conditions → context-sensitive
- **Low SE + Low SIS**: Slower arousal but uninhibited → steady, patient buildup
- **Low SE + High SIS**: Requires intentional approach → needs safety, predictability

**Power Dynamic Interpretation:**
- **Top (High Confidence)**: Enjoys leading, structuring, directing
- **Bottom (High Confidence)**: Enjoys surrendering, following, receiving
- **Switch**: Comfortable in both roles, adaptive
- **Versatile/Undefined**: Still exploring or context-dependent

**Domain Score Interpretation:**
- High Sensation + Low Connection: Intensity-focused, physical thrill-seeker
- High Connection + Low Sensation: Emotionally-driven, gentle intimacy
- High Power + High Exploration: Adventurous with structure
- High Verbal + Low Display: Prefers talking over showing

---

### For Compatibility Mapping:

**Overall Score Bands:**
- 85-100: Exceptional compatibility - aligned preferences, mutual interests
- 70-84: High compatibility - strong foundation with some exploration areas
- 55-69: Moderate compatibility - workable with communication and compromise
- 40-54: Lower compatibility - significant differences, requires intentional navigation
- 0-39: Challenging compatibility - fundamental mismatches, proceed with caution

**Power Complement Interpretation:**
- 90-100: Perfect or near-perfect power fit
- 70-89: Good power fit, flexible
- 50-69: Workable, requires communication
- <50: Power dynamic mismatch

---

## VALIDATION & QUALITY CHECKS

### Survey Administration Checks:
1. **Completion validation**: Ensure no questions skipped (except open text in Q54)
2. **Response time check**: Flag if completed in <5 minutes (may indicate random clicking)
3. **Consistency check**: Look for contradictory patterns (e.g., all "No" in activities but high exploration score)

### Profile Quality Indicators:
1. **Balanced vs. Extreme**: Check if user has selected all extreme responses (all 1s or all 7s)
2. **Activity diversity**: Flag if >80% of activities are "No" (user may need encouragement to explore)
3. **Boundary clarity**: If hard_boundaries array is empty AND many activities are "No", prompt user to confirm

### Matching Quality Checks:
1. **Critical boundary violations**: Never suggest activities that violate hard boundaries
2. **Intensity mismatch alert**: If sensation scores differ by >30 points, flag for user awareness
3. **Power mismatch alert**: If both are high-confidence Tops or Bottoms, alert users to discuss

---

## IMPLEMENTATION NOTES

### Data Storage:
- Store individual profiles as JSON documents in Supabase
- Index by user_id for quick retrieval
- Version all profiles (profile_version field) for future updates
- Store compatibility calculations separately with timestamps

### API Endpoints:
- `POST /survey/submit` → calculate and store individual profile
- `GET /profile/:user_id` → retrieve user's intimacy profile
- `POST /compatibility/calculate` → compute compatibility between 2+ users
- `GET /compatibility/:sessionId` → retrieve stored compatibility mapping

### Privacy & Security:
- All profile data encrypted at rest
- Profiles only shared with explicitly consented partners (via session joining)
- Users can delete profiles at any time
- Activity history NOT stored in profiles (stored separately with expiration)

---

## CHANGE LOG

### v0.4 (Current)
- **Section 3A**: Reordered activities by intensity progression (gentle → moderate → intense/extreme)
- **Section 3A**: Added rimming questions (moved to Section 3C for anatomical clarity)
- **Section 3B**: Clarified "oral stimulation" as "oral sex" for genitals, "oral stimulation" for body
- **Section 3C**: Added rimming as separate item (Q30a/b)
- **Section 3D**: Consolidated orgasm control into single item (Q33) noting it includes edging, denial, forced
- **Section 3E**: Removed Q23 (compliments) as too universal to be discriminating
- **Total questions**: Maintained at 66 (same as v0.3)
- **Calculations**: No structural changes, same methodology applies

### Future Enhancements (Considered for v0.5+):
- Add specific toy preferences (vibrators, dildos, plugs, etc.)
- Add context preferences (time of day, duration, spontaneous vs planned)
- Add communication style preferences (verbal check-ins, safe words, non-verbal cues)
- Add aftercare preferences (cuddles, debrief, alone time, food, etc.)

---

*End of Survey Documentation v0.4*
