---
name: attuned-ai-activities
description: Managing AI-powered activity generation via Groq/Llama integration. Use when working with LLM prompts, activity generation, activity analysis/enrichment, or troubleshooting AI responses. Covers prompt engineering for intimacy content.
---

# Attuned AI Activities Skill

## Architecture

```
backend/src/llm/
├── groq_client.py      # API wrapper with retry logic
├── generator.py        # Activity generation orchestration
├── activity_analyzer.py # Activity enrichment (18KB)
├── prompts.py          # Prompt templates
```

## Groq Configuration

```python
# Environment variables
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
GEN_TEMPERATURE=0.6

# Runtime config (app_config table)
get_config('groq_model', settings.GROQ_MODEL)
get_config_float('gen_temperature', 0.6)
```

## Activity Generation Flow

```
User Profile → Filter Bank Activities → Insufficient? → Generate via LLM
                     ↓                                        ↓
              Recommend from Bank                    Validate & Enrich
                     ↓                                        ↓
              Return Activity    ←────────────────────────────┘
```

## Prompt Templates (prompts.py)

### Generation Prompt Structure
```python
ACTIVITY_GENERATION_PROMPT = """
Generate {count} intimate activities for a couple with these profiles:

Player 1: {player1_profile}
Player 2: {player2_profile}

Requirements:
- Rating: {rating} (PG-13, R, or NC-17)
- Activity type: {activity_type} (truth or dare)
- Must respect boundaries: {boundaries}
- Focus on mutual interests: {mutual_activities}

Output JSON array with fields:
- title: Short activity name
- description: 2-3 sentence instructions
- intensity_level: 1-5
- requires_anatomy: [list of required anatomy]
- tags: [activity tags]
"""
```

### Enrichment Prompt (activity_analyzer.py)
```python
ENRICHMENT_PROMPT = """
Analyze this activity and add metadata:

Activity: {activity_text}

Return JSON:
- intensity_level: 1-5
- requires_anatomy: ["penis", "vagina", "breasts"] or []
- activity_type: "truth" or "dare"
- domain_tags: ["sensation", "connection", "power", "exploration", "verbal"]
- give_receive_role: "give", "receive", "mutual", or null
"""
```

## Groq Client Pattern

```python
from ..llm.groq_client import GroqClient

client = GroqClient()

# With retry logic built-in
response = client.generate(
    prompt=prompt,
    max_tokens=2000,
    temperature=get_config_float('gen_temperature', 0.6)
)

# Parse JSON response
try:
    activities = json.loads(response)
except json.JSONDecodeError:
    # Fallback to bank activities
    pass
```

## Content Guidelines

### Rating Levels
- **PG-13**: Flirty, romantic, no explicit content
- **R**: Sensual, suggestive, mild explicit
- **NC-17**: Explicit sexual content

### Anatomy Awareness
Activities must check anatomy compatibility:
```python
def activity_matches_anatomy(activity, player_anatomy):
    required = activity.get('requires_anatomy', [])
    if not required:
        return True
    return all(a in player_anatomy for a in required)
```

### Boundary Respect
```python
# Hard limits from profile
hard_limits = profile['boundaries']['hard_limits']

# Filter activities that violate limits
HARD_LIMIT_MAP = {
    'no_anal': ['anal_give', 'anal_receive', 'rimming'],
    'no_bondage': ['restraint', 'tying', 'handcuffs'],
    # ... see calculator.py for full map
}
```

## Troubleshooting

### Rate Limits
Groq has rate limits - implement exponential backoff:
```python
for attempt in range(3):
    try:
        return client.generate(prompt)
    except RateLimitError:
        time.sleep(2 ** attempt)
```

### Invalid JSON Response
LLMs sometimes return malformed JSON:
```python
# Strip markdown code fences
response = response.replace('```json', '').replace('```', '')
# Try parsing
try:
    data = json.loads(response)
except:
    # Log and fallback to bank
    logger.warning(f"Invalid JSON from LLM: {response[:200]}")
```

### Content Safety
All generated content passes through validation before storage:
- Check for prohibited terms
- Verify anatomy requirements are reasonable
- Ensure boundaries are respected
