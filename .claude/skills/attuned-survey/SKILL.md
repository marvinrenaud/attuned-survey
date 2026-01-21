---
name: attuned-survey
description: Managing the 54-question intimacy survey - questions, submission logic, profile calculation, scoring algorithms. Use when working with survey routes, scoring modules, SES/SIS arousal model, power dynamics, or domain scores.
---

# Attuned Survey Skill

## Survey Structure

54 questions covering:
- **Arousal patterns** (SES/SIS-P/SIS-C model)
- **Power dynamics** (Top/Bottom/Switch orientation)
- **Domain preferences** (5 domains: sensation, connection, power, exploration, verbal)
- **Activity interests** (give/receive preferences)
- **Truth topic openness**
- **Boundaries** (hard/soft limits)

## Scoring Modules

```
backend/src/scoring/
├── profile.py         # Main orchestrator
├── arousal.py         # SE, SIS-P, SIS-C (0-100)
├── power.py           # Top/Bottom/Switch + intensity
├── domains.py         # 5 domain scores (0-100)
├── activities.py      # Activity preference mapping
├── truth_topics.py    # Topic openness scores
└── tags.py            # Activity tagging
```

## Profile Calculation

```python
from ..scoring.profile import calculate_profile

# Input: survey answers dict
answers = {'q1': 5, 'q2': 3, ...}  # 54 questions

# Output: complete profile
profile = calculate_profile(answers)
# {
#   'arousal': {'se': 65, 'sis_p': 45, 'sis_c': 55},
#   'power_dynamic': {'orientation': 'Switch', 'intensity': 0.5},
#   'domain_scores': {'sensation': 70, 'connection': 80, ...},
#   'activities': {'massage_give': 0.9, ...},
#   'truth_topics': {'fantasies': 0.8, ...},
#   'boundaries': {'hard_limits': [], 'soft_limits': []}
# }
```

## Arousal Model (SES/SIS)

Based on Sexual Excitation/Inhibition Model:
- **SE** (Sexual Excitation): Ease of arousal
- **SIS-P** (Inhibition - Performance): Performance anxiety
- **SIS-C** (Inhibition - Consequences): Consequence concerns

```python
# scoring/arousal.py
def calculate_arousal(answers):
    se_questions = ['q3', 'q7', 'q12', ...]  # Excitation questions
    sis_p_questions = ['q5', 'q9', ...]       # Performance anxiety
    sis_c_questions = ['q6', 'q11', ...]      # Consequence concerns
    
    se = sum(answers[q] for q in se_questions) / len(se_questions) * 20
    sis_p = sum(answers[q] for q in sis_p_questions) / len(sis_p_questions) * 20
    sis_c = sum(answers[q] for q in sis_c_questions) / len(sis_c_questions) * 20
    
    return {'se': round(se), 'sis_p': round(sis_p), 'sis_c': round(sis_c)}
```

## Power Dynamics

```python
# scoring/power.py
def calculate_power_dynamic(answers):
    # Questions measure preference for control vs submission
    control_score = sum(answers[q] for q in CONTROL_QUESTIONS)
    submit_score = sum(answers[q] for q in SUBMIT_QUESTIONS)
    
    if control_score > submit_score + THRESHOLD:
        orientation = 'Top'
    elif submit_score > control_score + THRESHOLD:
        orientation = 'Bottom'
    else:
        orientation = 'Switch'
    
    intensity = abs(control_score - submit_score) / MAX_DIFF
    return {'orientation': orientation, 'intensity': min(1.0, intensity)}
```

## Survey Submission Flow

```
POST /api/survey/submit
       ↓
Validate answers (54 required)
       ↓
Check anatomy booleans
       ↓
calculate_profile(answers)
       ↓
Store SurveySubmission
       ↓
Create/Update Profile
       ↓
Return profile_id
```

## Key Endpoints

- `POST /api/survey/submit` - Submit completed survey
- `GET /api/survey/questions` - Get question list
- `POST /api/survey/retake` - Start new survey (creates new profile)
- `GET /api/users/profile-ui` - Get profile for display

## Database Tables

```sql
-- Survey responses
survey_submissions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    answers JSONB,
    demographics JSONB,
    anatomy JSONB,
    created_at TIMESTAMP
)

-- Calculated profiles
profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    submission_id UUID REFERENCES survey_submissions(id),
    data JSONB,  -- Full profile JSON
    created_at TIMESTAMP
)
```

## Testing Survey Logic

```python
def test_arousal_calculation():
    answers = {f'q{i}': 3 for i in range(1, 55)}  # Neutral answers
    profile = calculate_profile(answers)
    assert 40 <= profile['arousal']['se'] <= 60  # Mid-range expected

def test_top_orientation():
    answers = {**neutral_answers}
    for q in CONTROL_QUESTIONS:
        answers[q] = 5  # Max control preference
    profile = calculate_profile(answers)
    assert profile['power_dynamic']['orientation'] == 'Top'
```
