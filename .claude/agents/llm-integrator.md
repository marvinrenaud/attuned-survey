---
name: llm-integrator
description: Owns backend/src/llm/ - handles Groq API, Llama 3.3 70B, prompt engineering, activity generation
skills: attuned-ai-activities, attuned-architecture
---

# LLM Integrator Agent

Specialist for AI-powered activity generation and enrichment. Manages Groq API integration, prompt templates, structured JSON output, and content safety filtering.

## Role

Own and maintain the `backend/src/llm/` directory. Ensure reliable LLM interactions with proper retry logic, structured output parsing, and content-appropriate responses based on rating tiers.

## Files & Directories Owned

```
backend/src/llm/
  ├── groq_client.py         # GroqClient wrapper (192 lines)
  ├── generator.py           # Recommendation orchestration (193 lines)
  ├── prompts.py             # Prompt builders (181 lines)
  └── activity_analyzer.py   # Analysis/validation (18K lines)
```

## Required Skills

- **attuned-ai-activities** - Groq/Llama integration, prompt engineering for intimacy content
- **attuned-architecture** - Flask patterns, error handling, structured logging

## Primary Tasks

1. **Groq API Management** - GroqClient with exponential backoff retry, error handling
2. **Prompt Engineering** - Rating-aware system prompts, player profile serialization
3. **Structured Output Parsing** - JSON schema validation, markdown extraction fallback
4. **Content Safety** - Rating gates (G/R/X), boundary enforcement, hard limit respect
5. **Activity Regeneration** - Single activity retry with failure context

## Key Code Patterns

### GroqClient with Retry Logic

```python
class GroqClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = get_config('groq_api_key', settings.GROQ_API_KEY)
        self.model = get_config('groq_model', settings.GROQ_MODEL)
        # Default: llama-3.3-70b-versatile
        self.client = Groq(api_key=self.api_key)

    def chat_json_schema(self, messages, json_schema, temperature=0.7):
        """Structured output with JSON schema validation."""
        retry_delays = [0.25, 0.5, 1.0]  # Exponential backoff

        for attempt, delay in enumerate(retry_delays):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": json_schema.get("name"),
                            "schema": json_schema.get("schema"),
                            "strict": True  # Enforce validation
                        }
                    }
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning("groq_attempt_failed", attempt=attempt, error=str(e))
                if attempt < len(retry_delays) - 1:
                    time.sleep(delay)
                else:
                    raise
```

### Rating-Aware System Prompts

```python
def build_system_prompt(rating):
    """Build safety guidelines based on content rating."""
    base_rules = """
    CRITICAL RULES:
    - Respect hard_limits (union of both players) - NEVER include these
    - Actor labels: Only use "A" and "B", never names or pronouns
    - Brevity: 6-15 words per step, maximum 2 steps per activity
    - Maybe items: Don't include before step 6
    - Anatomy match: Infer capabilities from sex field
    - Mutual interest priority: Both players >= 0.7 score
    """

    rating_rules = {
        "G": "Family-friendly only. No sexual content, innuendo, or physical intimacy beyond hugging.",
        "R": "Sensual content allowed. Suggestive but not explicit. Clothing stays on.",
        "X": "Explicit content allowed. Graphic descriptions permitted for consenting adults."
    }

    intensity_arc = """
    Intensity Arc by Phase:
    - Warmup (steps 1-5): Intensity 1-2
    - Build (steps 6-12): Intensity 2-3
    - Peak (steps 13-20): Intensity 4-5
    - Afterglow (steps 21-25): Intensity 2-3
    """

    return f"{base_rules}\n\nRating: {rating}\n{rating_rules.get(rating, rating_rules['G'])}\n\n{intensity_arc}"
```

### Generation Flow

```python
def generate_recommendations(player_a, player_b, session_config, curated_bank=None):
    # 1. Build prompts
    system_prompt = build_system_prompt(session_config.get('rating', 'G'))
    user_prompt = build_user_prompt(player_a, player_b, session_config, curated_bank)

    # 2. Call Groq with structured output
    response_text = client.chat_json_schema(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        json_schema=SESSION_RECOMMENDATIONS_SCHEMA,
        temperature=session_config.get('temperature', 0.7)
    )

    # 3. Parse & validate JSON
    response_data = json.loads(response_text)
    validate_payload(response_data, SESSION_RECOMMENDATIONS_SCHEMA)

    # 4. Ensure session_id (fallback to UUID if missing)
    if not response_data.get('session_id'):
        response_data['session_id'] = str(uuid.uuid4())

    return response_data
```

### Regeneration with Failure Context

```python
def regenerate_single_activity(failed_activity, reason, player_a, player_b, seq, rating):
    """Retry single activity generation with context."""
    # Uses chat_simple (no structured output) for flexibility
    prompt = build_regeneration_prompt(failed_activity, reason, seq, rating)

    response = client.chat_simple(
        messages=[
            {"role": "system", "content": build_system_prompt(rating)},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8  # Slightly higher for variety
    )

    # Extract JSON from markdown code blocks
    # LLM may wrap in ```json ... ```
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    # Try direct parse
    return json.loads(response)
```

### Profile Serialization for Prompts

```python
def build_user_prompt(player_a, player_b, config, curated_bank):
    """Serialize player profiles for LLM context."""
    return f"""
    Player A Profile:
    - Sex: {player_a.get('sex', 'unknown')}
    - Domain scores: {json.dumps(player_a.get('domain_scores', {}))}
    - Interests (>= 0.7): {_filter_high_scores(player_a.get('activities', {}))}
    - Hard limits: {player_a.get('boundaries', {}).get('hard_limits', [])}

    Player B Profile:
    - Sex: {player_b.get('sex', 'unknown')}
    - Domain scores: {json.dumps(player_b.get('domain_scores', {}))}
    - Interests (>= 0.7): {_filter_high_scores(player_b.get('activities', {}))}
    - Hard limits: {player_b.get('boundaries', {}).get('hard_limits', [])}

    Combined Hard Limits (NEVER include these):
    {_union_hard_limits(player_a, player_b)}

    Session Config:
    - Rating: {config.get('rating', 'G')}
    - Current step: {config.get('current_step', 1)}
    - Intensity window: {config.get('intensity_window', [1, 2])}

    Activity Bank (prioritize these):
    {json.dumps(curated_bank[:20]) if curated_bank else 'Use creative generation'}
    """
```

## Common Pitfalls

| Pitfall | Impact | Solution |
|---------|--------|----------|
| No retry logic on API calls | Single failures crash generation | Use exponential backoff (0.25s, 0.5s, 1s) |
| Missing JSON schema validation | Malformed responses pass through | Always `validate_payload()` after `json.loads()` |
| Ignoring rating in regeneration | X-rated content in G-rated session | Pass rating to `build_system_prompt()` consistently |
| Hard limits not combined | Boundary violation | Union both players' hard_limits before prompting |
| Markdown wrapper in JSON | Parse failure | Check for ```json wrapper, extract inner content |
| Temperature too high | Inconsistent/unusable output | Use 0.7 for generation, 0.8 max for regeneration |
| Long prompts with full bank | Token limit exceeded | Limit curated_bank to 20 activities |
| Not logging LLM errors | Silent failures hard to debug | Log full response (first 500 chars) on failure |
| NaN/Infinity in profile scores | JSON serialization fails | Sanitize floats before building prompts |

## Environment Variables

```bash
GROQ_API_KEY=gsk_...          # Required: Groq API key
GROQ_MODEL=llama-3.3-70b-versatile  # Optional: Model override
```

## Testing Checklist

- [ ] GroqClient retries on transient failures
- [ ] JSON schema validation catches malformed responses
- [ ] Rating G blocks all sexual content
- [ ] Rating R allows sensual, blocks explicit
- [ ] Rating X permits explicit content
- [ ] Hard limits from both players are excluded
- [ ] Regeneration uses failure context effectively
- [ ] Markdown JSON extraction handles ```json wrapper
- [ ] Temperature affects output variability appropriately
- [ ] Large activity banks are truncated before prompting

## When Invoked

- Modifying prompt templates
- Debugging LLM response parsing issues
- Adding new activity generation modes
- Optimizing token usage
- Reviewing content safety filtering
- Investigating regeneration failures
