"""AI-powered activity analysis for extracting tags, power roles, and preferences."""
import json
import logging
from typing import Dict, List, Any, Optional

from .groq_client import get_groq_client

logger = logging.getLogger(__name__)


# Canonical list of preference keys that match survey responses
PREFERENCE_KEYS = [
    # Physical activities
    'massage', 'kissing', 'oral', 'manual_stimulation', 'penetration',
    'anal', 'edging', 'orgasm_control', 'simultaneous_climax',
    
    # Power dynamics
    'dominance', 'submission', 'control', 'worship', 'service',
    'commands', 'obedience', 'restraint', 'bondage',
    
    # Sensory & roleplay
    'sensory_play', 'blindfold', 'temperature_play', 'roleplay',
    'costumes', 'fantasy', 'exhibitionism', 'voyeurism',
    
    # Intensity & edge
    'spanking', 'impact_play', 'pain', 'degradation', 'humiliation',
    'primal', 'rough', 'gentle', 'romantic',
    
    # Communication
    'dirty_talk', 'verbal', 'eye_contact', 'confession',
    'compliments', 'affirmation'
]

# Canonical domain tags
DOMAINS = ['sensual', 'playful', 'power', 'connection', 'exploration', 'edge']


def build_analyzer_prompt(description: str, activity_type: str, intimacy_level: str) -> str:
    """Build prompt for activity analysis."""
    return f"""You are an expert at analyzing intimacy activities and extracting structured metadata.

Analyze this activity and extract the following information:

ACTIVITY DETAILS:
- Type: {activity_type}
- Intimacy Level: {intimacy_level}
- Description: "{description}"

EXTRACT THESE FIELDS:

1. **power_role**: The power dynamic role this activity requires.
   Options: "top" (requires controlling/dominant player), "bottom" (requires receiving/submissive player), "switch" (works for either), "neutral" (no power dynamic)
   
   Guidelines:
   - "top" if: commanding, controlling, leading, dominating, using partner, giving orders
   - "bottom" if: obeying, serving, being used, receiving commands, submitting, worshiping
   - "neutral" if: equal participation, no power imbalance
   - "switch" if: role could flip or alternate

2. **preference_keys**: List of relevant preference tags from this list:
   {', '.join(PREFERENCE_KEYS[:20])}... (and others like penetration, anal, roleplay, etc.)
   
   Choose 1-5 most relevant keys that best describe this activity.

3. **domains**: List of 1-3 domain categories:
   {', '.join(DOMAINS)}

4. **intensity_modifiers**: Descriptive tags like:
   - gentle, intense, extreme, taboo, playful, romantic, primal, edgy, degrading, loving, etc.
   Choose 1-3 most relevant.

5. **requires_consent_negotiation**: true if activity involves edge play, pain, degradation, or anything requiring explicit prior discussion

RESPOND WITH VALID JSON:
{{
  "power_role": "top|bottom|switch|neutral",
  "preference_keys": ["key1", "key2", ...],
  "domains": ["domain1", "domain2"],
  "intensity_modifiers": ["modifier1", "modifier2"],
  "requires_consent_negotiation": true|false
}}

Be precise and consistent. Consider the language carefully - words like "command", "obey", "worship", "serve" indicate power dynamics."""


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
        valid_roles = ['top', 'bottom', 'switch', 'neutral']
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

