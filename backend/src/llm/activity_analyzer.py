"""AI-powered activity analysis for extracting tags, power roles, and preferences."""
import json
import logging
from typing import Dict, List, Any, Optional

from .groq_client import get_groq_client

logger = logging.getLogger(__name__)


# Canonical list of preference keys that match survey responses
# Directional keys (give/receive) match survey structure for accurate matching
PREFERENCE_KEYS = [
    # Physical Touch (directional)
    'massage_give', 'massage_receive',
    'hair_pull_give', 'hair_pull_receive',
    'biting_give', 'biting_receive',
    'spanking_give', 'spanking_receive',
    'hands_on_genitals_give', 'hands_on_genitals_receive',
    'slapping_give', 'slapping_receive',
    'choking_give', 'choking_receive',
    'spitting_give', 'spitting_receive',
    'watersports_give', 'watersports_receive',
    
    # Oral (directional)
    'oral_sex_give', 'oral_sex_receive',
    'oral_body_give', 'oral_body_receive',
    
    # Anal (directional)
    'anal_give', 'anal_receive',
    'rimming_give', 'rimming_receive',
    
    # Power Exchange (directional)
    'restraints_give', 'restraints_receive',
    'blindfold_give', 'blindfold_receive',
    'orgasm_control_give', 'orgasm_control_receive',
    'protocols_give', 'protocols_follow',
    
    # Verbal & Roleplay (non-directional)
    'dirty_talk', 'moaning', 'roleplay', 'commands', 'begging',
    
    # Display & Performance
    'stripping_self', 'watching_strip',
    'solo_pleasure_self', 'watching_solo_pleasure',
    'posing', 'dancing', 'revealing_clothing',
    
    # General/Mutual (non-directional)
    'kissing', 'eye_contact', 'confession', 'manual_stimulation',
    'penetration', 'sensory_play', 'temperature_play',
    'impact_play', 'exhibitionism', 'voyeurism'
]

# Canonical domain tags
DOMAINS = ['sensual', 'playful', 'power', 'connection', 'exploration', 'edge']


def build_analyzer_prompt(description: str, activity_type: str, intimacy_level: str) -> str:
    """Build prompt for activity analysis."""
    return f"""You are an expert at analyzing intimacy activities. Extract structured metadata with precision.

ACTIVITY DETAILS:
- Type: {activity_type}
- Intimacy Level: {intimacy_level}
- Description: "{description}"

CRITICAL CONTEXT: The ACTIVE PLAYER (who drew this card) performs this activity.

EXTRACT THESE FIELDS:

1. **power_role**: What power dynamic role does the ACTIVE PLAYER take?
   
   Options: "top", "bottom", or "neutral"
   
   IMPORTANT DISTINCTION - Dominance/Submission (D/s) vs Sadism/Masochism (S/M):
   
   "top" = PSYCHOLOGICAL DOMINANCE through power exchange
   - Active player COMMANDS, CONTROLS, DOMINATES through authority/ownership
   - Language: "command them to...", "make them...", "order your partner...", "control their..."
   - Examples: "Tell your partner to kneel and beg", "Command them to strip"
   
   "bottom" = PSYCHOLOGICAL SUBMISSION through power exchange  
   - Active player OBEYS, SUBMITS, SERVES, ASKS PERMISSION
   - Language: "obey their...", "serve your...", "worship their...", "beg to...", "ask permission to..."
   - Examples: "Kneel and beg for permission", "Worship their body"
   
   "neutral" = DEFAULT - Everything else including:
   - Pain/sensation play (spanking, clamps, wax, biting) - This is S/M, NOT D/s
   - Mutual activities (kissing, massage, equal participation)
   - Exhibition/voyeurism (public play, watching, stripping)  
   - Performance (dancing, posing, showing off)
   - All truth questions
   - Physical activities without power language
   
   RULE: Use top/bottom ONLY when there's explicit PSYCHOLOGICAL power exchange (D/s).
   DEFAULT to neutral for sensation play, mutual acts, and ambiguous activities.
   
   PERSPECTIVE CHECK:
   - "Do X to your partner" → Active player GIVES
   - "Let your partner do X to you" → Active player RECEIVES
   - Focus on WHO commands/obeys, not just physical dominance

2. **preference_keys**: DIRECTIONAL preference tags matching survey structure.
   
   Available keys include (use exact matches):
   Directional: spanking_give, spanking_receive, oral_sex_give, oral_sex_receive,
                anal_give, anal_receive, restraints_give, restraints_receive, etc.
   
   Non-directional: kissing, dirty_talk, roleplay, moaning, eye_contact, etc.
   
   Choose 2-5 most relevant keys. Use directional (_give/_receive) when activity clearly involves one player acting on another.
   
   Examples:
   - "Spank your partner" → ["spanking_give", "impact_play"]
   - "Let your partner spank you" → ["spanking_receive", "impact_play"]
   - "Kiss passionately" → ["kissing"]

3. **domains**: 1-3 domain categories from: {', '.join(DOMAINS)}
   
   Domain definitions:
   - sensual: Physical touch, pleasure, intimacy (oral, massage, penetration)
   - playful: Fun, lighthearted, games, teasing, humor
   - power: D/s dynamics, commands, worship, psychological control
   - connection: Emotional, vulnerability, confession, eye contact
   - exploration: New experiences, public play, exhibitionism, edge play
   - edge: Intense, taboo, degradation, extreme sensation
   
   Guidelines:
   - "power" domain ONLY for D/s activities (commands, obedience, worship)
   - Don't use "power" for sensation play (spanking, wax, clamps) → use "sensual" or "edge"
   - Public/semi-public → "exploration"

4. **intensity_modifiers**: 1-3 descriptive tags
   Options: gentle, intense, extreme, taboo, playful, romantic, primal, edgy, degrading, loving

5. **requires_consent_negotiation**: true if involves edge play, pain, degradation, or explicit prior discussion needed

RESPOND WITH VALID JSON ONLY:
{{
  "power_role": "top|bottom|neutral",
  "preference_keys": ["key1", "key2"],
  "domains": ["domain1", "domain2"],
  "intensity_modifiers": ["modifier1"],
  "requires_consent_negotiation": true|false
}}

Remember: DEFAULT to neutral for power_role unless there's explicit D/s language. Focus on the ACTIVE PLAYER'S role."""


def analyze_activity(
    description: str,
    activity_type: str,
    intimacy_level: str,
    row_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single activity using Groq AI.
    
    Args:
        description: Activity description text
        activity_type: "truth" or "dare"
        intimacy_level: "L1" through "L9"
        row_id: Optional row ID for logging
    
    Returns:
        Dict with power_role, preference_keys, domains, intensity_modifiers
        None if analysis fails
    """
    try:
        prompt = build_analyzer_prompt(description, activity_type, intimacy_level)
        
        client = get_groq_client()
        
        # Use simple chat (not JSON schema) for flexibility
        response = client.chat_simple(
            system_prompt="You are an expert activity analyzer. Return only valid JSON.",
            user_prompt=prompt,
            temperature=0.3  # Lower temperature for more consistent tagging
        )
        
        # Try to parse JSON
        # Handle markdown code blocks if present
        response_clean = response.strip()
        if '```json' in response_clean:
            start = response_clean.find('```json') + 7
            end = response_clean.find('```', start)
            response_clean = response_clean[start:end].strip()
        elif '```' in response_clean:
            start = response_clean.find('```') + 3
            end = response_clean.find('```', start)
            response_clean = response_clean[start:end].strip()
        
        result = json.loads(response_clean)
        
        # Validate result has required fields
        required_fields = ['power_role', 'preference_keys', 'domains', 'intensity_modifiers']
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing field {field} in analysis for row {row_id}")
                result[field] = [] if field != 'power_role' else 'neutral'
        
        # Validate power_role is valid
        valid_roles = ['top', 'bottom', 'neutral']
        if result['power_role'] not in valid_roles:
            logger.warning(f"Invalid power_role '{result['power_role']}' for row {row_id}, defaulting to neutral")
            result['power_role'] = 'neutral'
        
        logger.info(
            f"Activity analyzed",
            extra={
                "row_id": row_id,
                "power_role": result['power_role'],
                "preference_count": len(result.get('preference_keys', [])),
                "domain_count": len(result.get('domains', []))
            }
        )
        
        return result
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for row {row_id}: {str(e)}")
        logger.error(f"Response was: {response[:500]}")
        return None
    
    except Exception as e:
        logger.error(f"Activity analysis failed for row {row_id}: {str(e)}")
        return None


def batch_analyze_activities(
    activities: List[Dict[str, Any]],
    batch_size: int = 10,
    delay_between_batches: float = 2.0
) -> Dict[int, Dict[str, Any]]:
    """
    Analyze multiple activities in batches.
    
    Args:
        activities: List of activity dicts with 'description', 'type', 'intimacy_level', 'row_id'
        batch_size: Number of activities to process in parallel
        delay_between_batches: Seconds to wait between batches (rate limiting)
    
    Returns:
        Dict mapping row_id to analysis results
    """
    import time
    
    results = {}
    total = len(activities)
    
    for i in range(0, total, batch_size):
        batch = activities[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} activities)")
        
        for activity in batch:
            row_id = activity.get('row_id')
            result = analyze_activity(
                activity['description'],
                activity['type'],
                activity['intimacy_level'],
                row_id
            )
            
            if result:
                results[row_id] = result
            else:
                # Fallback: neutral tags
                logger.warning(f"Using fallback neutral tags for row {row_id}")
                results[row_id] = {
                    'power_role': 'neutral',
                    'preference_keys': [],
                    'domains': [],
                    'intensity_modifiers': [],
                    'requires_consent_negotiation': False
                }
        
        # Rate limiting delay between batches
        if i + batch_size < total:
            logger.info(f"Waiting {delay_between_batches}s before next batch...")
            time.sleep(delay_between_batches)
    
    logger.info(f"Batch analysis complete: {len(results)}/{total} activities tagged")
    return results


def get_fallback_tags(description: str, activity_type: str) -> Dict[str, Any]:
    """
    Get fallback tags using keyword matching (when Groq fails).
    
    Simple keyword-based heuristic as backup.
    """
    desc_lower = description.lower()
    
    # Detect power role
    top_keywords = ['command', 'order', 'control', 'domina', 'master', 'lead']
    bottom_keywords = ['obey', 'serve', 'worship', 'submit', 'kneel', 'beg']
    
    has_top = any(kw in desc_lower for kw in top_keywords)
    has_bottom = any(kw in desc_lower for kw in bottom_keywords)
    
    if has_top and not has_bottom:
        power_role = 'top'
    elif has_bottom and not has_top:
        power_role = 'bottom'
    elif has_top and has_bottom:
        power_role = 'switch'
    else:
        power_role = 'neutral'
    
    # Detect preference keys
    preference_keys = []
    keyword_map = {
        'massage': ['massage', 'rub', 'knead'],
        'oral': ['oral', 'mouth', 'tongue', 'lick', 'suck'],
        'bondage': ['tie', 'bind', 'restrain', 'rope', 'cuff'],
        'spanking': ['spank', 'slap', 'paddle', 'crop'],
        'dirty_talk': ['talk dirty', 'say', 'tell', 'describe', 'confess'],
        'worship': ['worship', 'adore', 'praise'],
        'control': ['control', 'decide', 'command', 'order'],
        'sensory_play': ['blindfold', 'ice', 'feather', 'wax', 'temperature']
    }
    
    for key, keywords in keyword_map.items():
        if any(kw in desc_lower for kw in keywords):
            preference_keys.append(key)
    
    return {
        'power_role': power_role,
        'preference_keys': preference_keys[:3],  # Top 3
        'domains': ['connection'] if activity_type == 'truth' else ['sensual'],
        'intensity_modifiers': [],
        'requires_consent_negotiation': 'pain' in desc_lower or 'degrad' in desc_lower
    }

