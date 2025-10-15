# Technical Implementation Notes (v0.4/v0.5)

**Last Updated**: October 15, 2025  
**Survey Version**: v0.4  
**Compatibility Version**: v0.5

---

## System Architecture

### Frontend Stack
- **React 19** with hooks
- **Vite 6** for build tooling
- **React Router v7** for routing
- **Tailwind CSS 4** for styling
- **shadcn/ui** component library
- **Lucide React** for icons

### Backend Stack
- **Flask 3.1** (Python API)
- **Supabase PostgreSQL** (database)
- **Render.com** (hosting)
- **SQLAlchemy** (ORM)
- **Flask-CORS** (cross-origin support)

### Data Flow
```
User → Survey → Frontend Calculation → API → Database → Results Display
                     ↓
              Profile Calculator (v0.4)
                     ↓
        [Arousal, Power, Domains, Activities, Truth, Boundaries]
                     ↓
              Compatibility Mapper (v0.5)
                     ↓
        [Asymmetric/Same-Pole/Standard Jaccard Selection]
```

---

## Survey Structure (v0.4)

### Section A: Arousal & Power (16 Likert Questions)

**A1-A4: Sexual Excitation (SE)**
```javascript
// Measures propensity for arousal
// Scale: 1 (Strongly Disagree) to 7 (Strongly Agree)
// Normalization: (value - 1) / 6 → 0-1 scale
// Example: Response of 7 → 1.0 (High SE)
```

**A5-A8: Sexual Inhibition - Performance (SIS-P)**
```javascript
// Measures performance-related arousal inhibition
// Higher scores = more inhibition
// Normalized to 0-1 scale
```

**A9-A12: Sexual Inhibition - Consequence (SIS-C)**
```javascript
// Measures consequence-related arousal inhibition
// Covers privacy, safety, judgment concerns
// Normalized to 0-1 scale
```

**A13-A16: Power Dynamics**
```javascript
// A13, A15: Top orientation (giving direction, dominance)
// A14, A16: Bottom orientation (following direction, submission)
// Determines: Top, Bottom, Switch, or Versatile/Undefined
```

### Section B: Activities & Topics (36 Y/M/N Questions)

**Response Conversion**:
- Y (Yes) → 1.0
- M (Maybe) → 0.5
- N (No) → 0.0

**Categories**:
1. **Physical Touch (B1-B10)**: 20 items, intensity progressive
2. **Oral (B11-B12)**: 4 items, genital vs. body
3. **Anal (B13-B14)**: 4 items, including rimming
4. **Power Exchange (B15-B18)**: 8 items, restraints/control
5. **Verbal & Roleplay (B19-B23)**: 5 items, non-directional
6. **Display & Performance (B24-B28)**: 7 items, mixed directional
7. **Truth Topics (B29-B36)**: 8 items, conversation preferences

### Section C: Boundaries (2 Questions)

**C1: Hard Limits Checklist**
```javascript
// Array of selected boundaries
// Options: [
//   'impact_play', 'restraints_bondage', 'breath_play',
//   'degradation_humiliation', 'public_activities', 'recording',
//   'roleplay', 'multi_partner', 'toys_props',
//   'anal_activities', 'watersports', 'other'
// ]
```

**C2: Additional Notes**
```javascript
// Free text field for specific concerns
// Stored as string
```

---

## Calculation Engine (v0.4)

### 1. Arousal Propensity Calculator

**File**: `frontend/src/lib/scoring/arousalCalculator.js`

**Formula**:
```javascript
SE = mean([A1, A2, A3, A4]) normalized
SIS_P = mean([A5, A6, A7, A8]) normalized  
SIS_C = mean([A9, A10, A11, A12]) normalized

// Normalization: (likertValue - 1) / 6
// Result: 0-1 scale

Interpretation bands:
  0-0.30: Low
  0.30-0.55: Moderate-Low
  0.55-0.75: Moderate-High
  0.75-1.0: High
```

**Output**:
```javascript
{
  sexual_excitation: 0.96,
  inhibition_performance: 0.17,
  inhibition_consequence: 0.04,
  interpretation: {
    se: "High",
    sis_p: "Low",
    sis_c: "Low"
  }
}
```

### 2. Power Dynamic Calculator

**File**: `frontend/src/lib/scoring/powerCalculator.js`

**Formula**:
```javascript
top_score = mean([A13, A15]) × 100
bottom_score = mean([A14, A16]) × 100

// Thresholds
THETA_FLOOR = 30  // Minimum for engagement
DELTA_BAND = 15   // Band for Switch determination

// Orientation Logic:
if (both < 30):
  orientation = "Versatile/Undefined"
  confidence = max(top, bottom) / 100

else if (|top - bottom| <= 15 AND min >= 30):
  orientation = "Switch"
  confidence = min(top, bottom) / 100

else if (top > bottom):
  orientation = "Top"
  confidence = (top/100) × (1 - 0.3 × bottom/100)

else:
  orientation = "Bottom"
  confidence = (bottom/100) × (1 - 0.3 × top/100)
```

**Output**:
```javascript
{
  orientation: "Top",
  top_score: 100,
  bottom_score: 0,
  confidence: 1.0,
  interpretation: "Very high confidence Top"
}
```

### 3. Domain Score Calculator

**File**: `frontend/src/lib/scoring/domainCalculator.js`

**Domains** (all 0-100 scale):

**Sensation**: Physical intensity
```javascript
mean([
  biting_moderate_receive, biting_moderate_give,
  spanking_moderate_receive, spanking_moderate_give,
  spanking_hard_receive, spanking_hard_give,
  slapping_receive, slapping_give,
  choking_receive, choking_give,
  spitting_receive, spitting_give,
  watersports_receive, watersports_give
]) × 100
```

**Connection**: Emotional intimacy
```javascript
mean([
  massage_receive, massage_give,
  oral_body_receive, oral_body_give,
  moaning, posing, revealing_clothing,
  fantasies, insecurities, future_fantasies, feeling_desired
]) × 100
```

**Power**: Control and structure
```javascript
mean([
  restraints_receive, restraints_give,
  blindfold_receive, blindfold_give,
  orgasm_control_receive, orgasm_control_give,
  protocols_follow, protocols_give,
  commands, begging
]) × 100
```

**Exploration**: Novelty and risk
```javascript
mean([
  roleplay, stripping_me, watching_strip,
  watched_solo_pleasure, watching_solo_pleasure, dancing,
  spitting_receive, spitting_give,
  watersports_receive, watersports_give
]) × 100
```

**Verbal**: Communication
```javascript
mean([
  dirty_talk, moaning, roleplay, commands, begging
]) × 100
```

### 4. Activity Converter

**File**: `frontend/src/lib/scoring/activityConverter.js`

**Process**:
1. Read Y/M/N responses from survey answers
2. Convert to numeric: Y=1.0, M=0.5, N=0.0
3. Organize by category (6 categories)
4. Map to specific activity keys (e.g., 'B1a' → 'massage_receive')

**Output Structure**:
```javascript
{
  physical_touch: { massage_receive: 1.0, massage_give: 1.0, ... },
  oral: { oral_sex_receive: 1.0, ... },
  anal: { anal_fingers_toys_receive: 0.0, ... },
  power_exchange: { restraints_receive: 0.0, ... },
  verbal_roleplay: { dirty_talk: 1.0, ... },
  display_performance: { stripping_me: 0.0, ... }
}
```

### 5. Truth Topics Calculator

**File**: `frontend/src/lib/scoring/truthTopicsCalculator.js`

**Process**:
```javascript
// Convert B29-B36 responses
topicMap = {
  'B29': 'past_experiences',
  'B30': 'fantasies',
  'B31': 'turn_ons',
  'B32': 'turn_offs',
  'B33': 'insecurities',
  'B34': 'boundaries',
  'B35': 'future_fantasies',
  'B36': 'feeling_desired'
}

// Calculate openness
openness_score = mean(all_values) × 100
```

### 6. Profile Calculator (Orchestrator)

**File**: `frontend/src/lib/scoring/profileCalculator.js`

**Main Function**:
```javascript
calculateProfile(userId, answers) {
  1. arousalPropensity = calculateArousalPropensity(answers)
  2. powerDynamic = calculatePowerDynamic(answers)
  3. activities = convertActivities(answers)
  4. truthTopics = convertTruthTopics(answers)
  5. domainScores = calculateDomainScores(activities, truthTopics)
  6. boundaries = extractBoundaries(answers)
  7. activityTags = generateActivityTags(activities, boundaries)
  
  return {
    user_id, profile_version: "0.4", timestamp,
    arousal_propensity, power_dynamic, domain_scores,
    activities, truth_topics, boundaries, activity_tags
  }
}
```

---

## Compatibility Algorithm (v0.5)

### Three Matching Algorithms

#### Algorithm 1: Asymmetric Directional Jaccard

**File**: `frontend/src/lib/matching/compatibilityMapper.js`

**When**: Top/Bottom pairs

**Logic**:
```javascript
PRIMARY AXIS (80% weight):
  For each _give activity:
    If Top wants to GIVE AND Bottom wants to RECEIVE:
      primaryMatches++
    If Top wants to give OR Bottom wants to receive:
      primaryPotential++

SECONDARY AXIS (20% weight):
  For each _give activity:
    If Bottom wants to GIVE AND Top wants to RECEIVE:
      secondaryMatches++
    Else if Bottom wants to GIVE but Top doesn't RECEIVE:
      secondaryMatches += 0.5  // Partial credit

NON-DIRECTIONAL:
  Standard matching (both interested)

SCORE:
  (primaryMatches × 0.8 + secondaryMatches × 0.2 + nonDirectional) 
  / (primaryPotential × 0.8 + secondaryPotential × 0.2 + nonDirectionalPotential)
```

**Example**:
```
Hair Pulling:
  Top: give=1, receive=0
  Bottom: give=0, receive=1

Primary: Top gives (1) × Bottom receives (1) = MATCH ✓
Secondary: Bottom gives (0) × Top receives (0) = Both not interested ✓
Score: (1 × 0.8 + 1 × 0.2) / (1 × 0.8 + 1 × 0.2) = 1.0 (100%)
```

#### Algorithm 2: Same-Pole Jaccard

**When**: Top/Top or Bottom/Bottom pairs

**Logic**:
```javascript
DIRECTIONAL ACTIVITIES:
  For each _give activity:
    If both want to give but not receive:
      compatibleInteractions += 0  // Incompatible
    If one versatile (give AND receive), other not:
      compatibleInteractions += 0.1  // Minimal credit
    If both versatile (both give AND receive):
      compatibleInteractions += 0.2  // Slight credit

NON-DIRECTIONAL ACTIVITIES:
  If both interested:
    compatibleInteractions += 0.3  // Reduced credit (not 1.0)

SCORE:
  compatibleInteractions / totalPossibleInteractions
```

**Example**:
```
Hair Pulling (Top/Top):
  Top #1: give=1, receive=0
  Top #2: give=1, receive=0

Both want to give, neither wants to receive
Score: 0.0 (incompatible)

Dirty Talk (Top/Top):
  Top #1: 1 (interested)
  Top #2: 1 (interested)

Non-directional match, but reduced credit
Score: 0.3 (some compatibility, but power issue remains)
```

#### Algorithm 3: Standard Jaccard

**When**: Switch/Switch or non-directional categories

**Logic**:
```javascript
mutualYes = count(both >= 0.5)
atLeastOneYes = count(at least one >= 0.5)

score = mutualYes / atLeastOneYes
```

### Domain Similarity Calculation

**Power-Aware Logic**:

```javascript
calculateDomainSimilarity(domainsA, domainsB, powerA, powerB) {
  
  if (Top + Bottom pair):
    // Complementary logic
    sensation = standard distance
    connection = standard distance
    power = standard distance
    exploration = min >= 50 ? 1.0 : min/50  // Threshold approach
    verbal = min >= 50 ? 1.0 : min/50
    return average
  
  else if (Same-pole pair):
    // Penalty for similarity
    avgSimilarity = standard distance for all 5 domains
    return avgSimilarity × 0.5  // Half credit
  
  else:
    // Switch/Switch - standard
    return standard distance for all 5 domains
}
```

**Why This Works**:
- **Top/Bottom**: Different exploration scores (60 vs 95) = good (both >50)
- **Same-pole**: Same exploration scores (95 vs 95) = less compatible (×0.5 penalty)
- **Switch**: Different scores = less compatible (standard distance)

### Compatibility Calculation

**File**: `frontend/src/lib/matching/compatibilityMapper.js`

**Main Formula**:
```javascript
calculateCompatibilityDetailed(
  powerA, powerB,
  domainsA, domainsB,
  activitiesA, activitiesB,
  truthTopicsA, truthTopicsB,
  boundariesA, boundariesB,
  weights = { power: 0.20, domain: 0.25, activity: 0.45, truth: 0.10 }
) {
  
  // 1. Power Complement (0-1)
  powerComp = calculatePowerComplement(powerA, powerB)
  
  // 2. Domain Similarity (0-1) - Power-aware
  domainSim = calculateDomainSimilarity(domainsA, domainsB, powerA, powerB)
  
  // 3. Activity Overlap (0-1) - Three algorithms
  activityOverlap = calculateActivityOverlap(activitiesA, activitiesB, powerA, powerB)
  
  // 4. Truth Overlap (0-1)
  truthOverlap = calculateTruthOverlap(truthTopicsA, truthTopicsB)
  
  // Same-pole penalty on truth
  if (same-pole pair):
    adjustedTruthOverlap = truthOverlap × 0.5
  else:
    adjustedTruthOverlap = truthOverlap
  
  // 5. Weighted Score
  score = (
    weights.power × powerComp +
    weights.domain × domainSim +
    weights.activity × activityOverlap +
    weights.truth × adjustedTruthOverlap
  )
  
  // 6. Boundary Penalty
  score -= (boundaryConflicts × 0.2)
  
  return score × 100
}
```

**Weights Explained**:
- **Power (20%)**: Foundation - wrong power dynamic kills compatibility
- **Activity (45%)**: Most important - can they actually do things together?
- **Domain (25%)**: Preference alignment matters
- **Truth (10%)**: Communication valuable but not enough alone

---

## Power Complement Algorithm

**File**: `frontend/src/lib/scoring/powerCalculator.js`

**Logic**:
```javascript
calculatePowerComplement(powerA, powerB) {
  
  if (Switch + Switch):
    return 0.90
  
  if (Top + Bottom):
    avgConfidence = (powerA.confidence + powerB.confidence) / 2
    return 0.85 + (0.15 × avgConfidence)  // 0.85-1.0
  
  if (Switch + (Top OR Bottom)):
    return 0.70
  
  if (Same-pole OR both Versatile):
    return 0.40
}
```

**Why These Values**:
- **Top + Bottom**: 85-100% (perfect complement, scaled by confidence)
- **Switch + Switch**: 90% (both versatile)
- **Switch + Top/Bottom**: 70% (flexible but not ideal)
- **Same-pole**: 40% (incompatible power dynamic)

---

## Key Algorithms Deep Dive

### Asymmetric Directional Jaccard

**Problem It Solves**:
Traditional Jaccard sees Top(give=1, receive=0) + Bottom(give=0, receive=1) as mismatch because they differ on both questions.

**Solution**:
Compare **Top's give with Bottom's receive** (not Top's give with Bottom's give).

**Implementation**:
```javascript
keys.forEach(key => {
  if (key.endsWith('_give')) {
    receiveKey = key.replace('_give', '_receive')
    
    // PRIMARY: Top gives → Bottom receives?
    if (top[key] >= 0.5 AND bottom[receiveKey] >= 0.5):
      primaryMatches++
    
    // SECONDARY: Bottom gives → Top receives?
    if (bottom[key] >= 0.5 AND top[receiveKey] >= 0.5):
      secondaryMatches++
    else if (bottom[key] >= 0.5 AND top[receiveKey] < 0.5):
      secondaryMatches += 0.5  // Willing but not needed
  }
})

score = (primaryMatches × 0.8 + secondaryMatches × 0.2) / 
        (primaryPotential × 0.8 + secondaryPotential × 0.2)
```

**Result**: Top/Bottom pairs with high directional compatibility score ~75-85%

### Same-Pole Jaccard

**Problem It Solves**:
Standard Jaccard sees Top#1(give=1) + Top#2(give=1) as perfect match when they're incompatible (both want to give, no one receives).

**Solution**:
Recognize that matching on give/receive = incompatible for same-pole pairs.

**Implementation**:
```javascript
keys.forEach(key => {
  if (key.endsWith('_give')) {
    receiveKey = key.replace('_give', '_receive')
    
    // Check versatility
    if (A gives AND receives AND B gives but not receives):
      compatibleInteractions += 0.1  // A can adapt
    else if (both give AND receive):
      compatibleInteractions += 0.2  // Both can adapt
    else:
      compatibleInteractions += 0  // Incompatible
  }
  else:
    // Non-directional
    if (both interested):
      compatibleInteractions += 0.3  // Reduced credit
})
```

**Result**: Same-pole pairs score ~20-30% on directional activities

### Complementary Domain Similarity

**Problem It Solves**:
Traditional distance penalizes Bottom(exploration=95) + Top(exploration=60) as mismatch when it's actually ideal.

**Solution**:
For Top/Bottom pairs, use minimum threshold for exploration/verbal instead of distance.

**Implementation**:
```javascript
if (Top + Bottom pair):
  sensation/connection/power = standard distance
  
  // Exploration and verbal use minimum threshold
  minExploration = min(60, 95) = 60
  if (minExploration >= 50):
    explorationScore = 1.0  // No penalty!
  else:
    explorationScore = minExploration / 50
```

**Result**: Bottom being more adventurous than Top is recognized as beneficial, not penalized.

---

## Data Structures

### Profile Object (v0.4)

```javascript
{
  user_id: "1760537681785-vio2041ue",
  profile_version: "0.4",
  timestamp: "2025-10-15T14:14:41.787Z",
  
  arousal_propensity: {
    sexual_excitation: 0.96,
    inhibition_performance: 0.17,
    inhibition_consequence: 0.04,
    interpretation: { se: "High", sis_p: "Low", sis_c: "Low" }
  },
  
  power_dynamic: {
    orientation: "Top",
    top_score: 100,
    bottom_score: 0,
    confidence: 1.0,
    interpretation: "Very high confidence Top"
  },
  
  domain_scores: {
    sensation: 61,
    connection: 82,
    power: 60,
    exploration: 60,
    verbal: 70
  },
  
  activities: {
    physical_touch: { massage_receive: 1, massage_give: 1, ... },
    oral: { ... },
    anal: { ... },
    power_exchange: { ... },
    verbal_roleplay: { ... },
    display_performance: { ... }
  },
  
  truth_topics: {
    past_experiences: 1,
    fantasies: 1,
    // ... 6 more
    openness_score: 100
  },
  
  boundaries: {
    hard_limits: ["degradation_humiliation"],
    additional_notes: ""
  },
  
  activity_tags: {
    open_to_gentle: true,
    open_to_moderate: true,
    // ... 8 more boolean flags
  }
}
```

### Compatibility Result Object

```javascript
{
  players: ["user1_id", "user2_id"],
  compatibility_version: "0.5",
  timestamp: "2025-10-15T...",
  
  overall_compatibility: {
    score: 89,
    interpretation: "Exceptional compatibility"
  },
  
  breakdown: {
    power_complement: 100,
    domain_similarity: 94,
    activity_overlap: 79,
    truth_overlap: 100,
    boundary_conflicts: []
  },
  
  mutual_activities: {
    physical_touch: ["massage_receive", "massage_give", ...],
    oral: [...],
    // ... other categories
  },
  
  growth_opportunities: [
    { activity: "physical_touch.spanking_moderate", playerA: "maybe", playerB: "yes" }
  ],
  
  mutual_truth_topics: ["fantasies", "turn_ons", ...],
  
  blocked_activities: {
    reason: "hard_boundaries",
    activities: ["degradation_humiliation"]
  }
}
```

---

## Performance Optimizations

### Frontend
- **Lazy loading**: Routes code-split
- **Memoization**: Calculation results cached
- **Session persistence**: Reduces backend calls
- **Debounced validation**: Reduces re-renders

### Backend
- **Connection pooling**: Supabase managed
- **Query optimization**: Indexed by submission_id
- **JSON storage**: Full profiles stored as JSONB
- **Response compression**: Gzip enabled

### API
- **Timeouts**: 15s limit prevents hanging
- **Retry logic**: 3 attempts with exponential backoff
- **Error handling**: Graceful degradation
- **Caching**: Static assets cached

---

## Testing Infrastructure

### Test Files

**Test Profiles**: `frontend/src/lib/matching/__tests__/testProfiles.js`
- Real user data (BBH, Quick Check)
- Edge case profiles (Switch, Top/Top, Bottom/Bottom)

**Test Runner**: `frontend/src/lib/matching/__tests__/compatibilityTest.js`
- Automated test suite
- Browser console integration
- Expected vs actual validation

**Test Page**: `/test-compatibility` route
- Visual test interface
- Real-time test execution
- Detailed console output

### Test Coverage

**Unit Tests**:
- ✅ Arousal propensity calculation
- ✅ Power dynamic determination
- ✅ Domain score calculation
- ✅ Activity conversion
- ✅ Truth topics processing

**Integration Tests**:
- ✅ Complete profile generation
- ✅ Compatibility matching (all pair types)
- ✅ Boundary conflict detection
- ✅ Edge cases (all orientations)

**Real Data Validation**:
- ✅ BBH (Top) vs Quick Check (Bottom): 89%
- ✅ Top vs Top: 38%
- ✅ Bottom vs Bottom: 41%

---

## Error Handling

### API Timeouts

**Configuration**: 15 seconds for all requests

```javascript
// AbortController pattern
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 15000);

fetch(url, { signal: controller.signal })
  .then(response => {
    clearTimeout(timeoutId);
    return response.json();
  })
  .catch(error => {
    if (error.name === 'AbortError') {
      // Handle timeout
    }
  });
```

### Retry Mechanisms

**Admin Panel**:
- Shows error message when backend fails
- "Retry Loading" button to reload data
- "Refresh Page" button for hard reset

**Results Page**:
- 3 automatic retries with exponential backoff
- Manual retry button on error
- Clear error messages (timeout vs 500 vs 404)

### Graceful Degradation

**When Backend Slow**:
- Loading state shown (not hung)
- Timeout after 15s
- Error message with retry option

**When Backend Down**:
- Clear error message
- Links to home or admin panel
- No data loss (session persisted)

---

## Security Considerations

### Current Implementation

**Admin Authentication**:
- Password: Hardcoded in frontend (admin panel)
- **Warning**: Not secure for production with sensitive data
- **Recommendation**: Move to backend JWT authentication

**Data Storage**:
- All data stored in Supabase PostgreSQL
- No encryption at rest (Supabase default)
- **Recommendation**: Enable RLS (Row Level Security)

**API**:
- CORS enabled for frontend domain
- No rate limiting
- **Recommendation**: Add rate limiting for production

### Recommended Improvements

1. **Authentication**: Implement proper user auth (JWT, OAuth)
2. **Encryption**: Encrypt sensitive profile data at rest
3. **Rate Limiting**: Prevent abuse (e.g., 100 requests/minute)
4. **Input Validation**: Backend validation of all inputs
5. **HTTPS Only**: Enforce secure connections
6. **CSP Headers**: Content Security Policy

---

## Database Schema

### Supabase Tables

**survey_submissions**:
```sql
CREATE TABLE survey_submissions (
  id SERIAL PRIMARY KEY,
  submission_id VARCHAR(128) UNIQUE NOT NULL,
  respondent_id VARCHAR(128),
  name VARCHAR(256),
  sex VARCHAR(32),
  sexual_orientation VARCHAR(64),
  version VARCHAR(16),
  payload_json JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_submission_id ON survey_submissions(submission_id);
CREATE INDEX idx_created_at ON survey_submissions(created_at DESC);
```

**survey_baseline**:
```sql
CREATE TABLE survey_baseline (
  id SERIAL PRIMARY KEY,
  submission_id VARCHAR(128),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**payload_json Structure** (v0.4):
```json
{
  "id": "submission_id",
  "name": "User Name",
  "sex": "male",
  "sexualOrientation": "heterosexual",
  "version": "0.4",
  "createdAt": "ISO8601",
  "answers": { "A1": 7, "A2": 6, ... },
  "derived": {
    "profile_version": "0.4",
    "arousal_propensity": { ... },
    "power_dynamic": { ... },
    "domain_scores": { ... },
    "activities": { ... },
    "truth_topics": { ... },
    "boundaries": { ... },
    "activity_tags": { ... }
  }
}
```

---

## API Endpoints

### Survey Endpoints

**GET /api/survey/submissions**
```
Response: {
  submissions: Array<Submission>,
  baseline: string | null
}
```

**POST /api/survey/submissions**
```
Request: Submission object
Response: Saved submission with ID
```

**GET /api/survey/submissions/:id**
```
Response: Submission object
```

**GET /api/survey/baseline**
```
Response: { baseline: string | null }
```

**POST /api/survey/baseline**
```
Request: { id: string }
Response: { baseline: string }
```

**DELETE /api/survey/baseline**
```
Response: { baseline: null }
```

**GET /api/survey/export**
```
Response: {
  exportedAt: ISO8601,
  baseline: string | null,
  submissions: Array<Submission>
}
```

---

## Frontend Components

### Page Components

**Survey.jsx**:
- Multi-chapter survey flow
- Question rendering (likert7, chooseYMN, checklist, text)
- Real-time validation
- Session persistence
- Profile calculation on submit

**Result.jsx**:
- Arousal profile display
- Power dynamic visualization
- Domain scores (bar charts)
- Activity summary by category
- Compatibility breakdown (if baseline set)

**Admin.jsx**:
- Password authentication (frontend)
- Submission table display
- Baseline management
- Data export (CSV/JSON)
- Version detection (v0.3.1 vs v0.4)

**TestCompatibility.jsx**:
- Test page for algorithm validation
- Real user profile testing
- Edge case scenarios
- Console debug output

### Calculation Modules

**Calculators** (`frontend/src/lib/scoring/`):
- `arousalCalculator.js` - SE, SIS-P, SIS-C
- `powerCalculator.js` - Power orientation
- `domainCalculator.js` - 5 domains + similarity
- `activityConverter.js` - Y/M/N conversion
- `truthTopicsCalculator.js` - Conversation preferences
- `activityTags.js` - Boolean flags
- `profileCalculator.js` - Main orchestrator

**Matching** (`frontend/src/lib/matching/`):
- `compatibilityMapper.js` - Three Jaccard algorithms
- `categoryMap.js` - Question → category mapping
- `overlapHelper.js` - Helper functions

---

## Version History

### v0.5 (Oct 15, 2025) - Same-Pole Fix
**Changes**:
- Added `calculateSamePoleJaccard()`
- Domain similarity penalty (×0.5) for same-pole
- Truth overlap penalty (×0.5) for same-pole
- Reduced versatility credits (0.5→0.2, 0.3→0.1)
- Reduced non-directional credits (1.0→0.3) for same-pole
- Updated weights (power 20%, activity 45%, truth 10%)

**Impact**:
- Same-pole pairs: 75% → 38-41% ✅

### v0.4 (Oct 14, 2025) - Survey Refactor
**Changes**:
- Survey: 71 → 54 questions
- Added explicit power section (A13-A16)
- New profile structure (arousal, power, domains)
- Asymmetric directional Jaccard
- Complementary domain logic
- Results redesigned

**Impact**:
- Top/Bottom pairs: 60% → 89% ✅

### v0.3.1 (Oct 11, 2025)
- Removed ipsative questions
- Minor refinements

### v1.0.0 (Oct 10, 2025)
- Initial production release
- Supabase integration
- API-based persistence

---

## Known Limitations

### Current System
- **Identical profiles score higher than expected** (50% vs 38%) - By design, truly identical users will have some compatibility
- **Backend dependency**: Frontend requires backend for data
- **No offline mode**: Requires internet connection
- **Single baseline**: Can only compare to one profile at a time

### Future Enhancements
- Multi-baseline comparison
- Activity recommendations
- Profile evolution tracking
- Offline support with sync
- Real-time updates (WebSocket)

---

## Deployment Notes

### Production Environment
- **Frontend**: Built and deployed
- **Backend**: Render.com auto-deploy from GitHub
- **Database**: Supabase PostgreSQL (managed)
- **Domain**: Custom domain configured

### Environment Variables
```bash
# Frontend (.env.local if needed)
VITE_API_URL=https://attuned-backend.onrender.com

# Backend (Render.com)
DATABASE_URL=postgresql://... (Supabase connection string)
FLASK_ENV=production
SECRET_KEY=... (for sessions)
```

### Build Process
```bash
# Frontend
cd frontend
pnpm install
pnpm run build
# Output: dist/

# Backend auto-deploys via Render.com GitHub integration
```

---

## Troubleshooting

### Common Issues

**Admin shows "No submissions"**:
- Check: Backend connection (500 errors?)
- Fix: Wait for Supabase, use retry button
- Verify: Backend logs on Render.com

**Results page stuck loading**:
- Check: Console for timeout errors
- Fix: Retry loading button
- Verify: Submission exists in database

**Power visualizer wrong position**:
- Check: Profile version (must be v0.4)
- Fix: Should auto-fix with v0.4 profiles
- Code: Line 317 in Result.jsx

**Compatibility score unexpected**:
- Check: Both profiles v0.4 (version check in code)
- Check: Power orientations correct
- Debug: Use `/test-compatibility` page
- Console: Shows detailed breakdown

---

## References

### Survey Methodology
- **SES/SIS Model**: Janssen & Bancroft (2007)
- **Erotic Preferences**: Wilson et al. (2017)
- **IntimacAI v0.4**: October 2025 revision

### Implementation Guides
- v0.4: `/data/intimacai_v04/attuned_implementation_guide_v0.4 (1).ts`
- v0.5: `/data/intimacai_v04/CursorFiles2/intimacai_compatibility_FINAL_v0_5.ts`

### Documentation
- Executive Summary: `/EXECUTIVE_SUMMARY.md`
- README: `/README.md`
- Algorithm Fixes: `/COMPATIBILITY_ALGORITHM_FIX.md`, `/SAME_POLE_FIX_v0.5.md`

---

**For questions or clarifications, see EXECUTIVE_SUMMARY.md or contact the development team.**

*Last updated: October 15, 2025*
