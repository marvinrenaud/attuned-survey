"""Activity generation orchestrator using Groq."""
import json
import logging
import uuid
from typing import Dict, Any, List, Optional

from .groq_client import get_groq_client
from .prompts import build_system_prompt, build_user_prompt, build_regeneration_prompt
from ..recommender.schema import SESSION_RECOMMENDATIONS_SCHEMA
from ..recommender.validator import validate_payload, ValidationError

logger = logging.getLogger(__name__)


def generate_recommendations(
    player_a: Dict[str, Any],
    player_b: Dict[str, Any],
    session_config: Dict[str, Any],
    curated_bank: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate activity recommendations using Groq.
    
    Args:
        player_a: Player A's complete profile
        player_b: Player B's complete profile
        session_config: Session configuration (rating, target_activities, etc.)
        curated_bank: Optional pre-selected activities to consider
        request_id: Optional request ID for logging
    
    Returns:
        Complete recommendations dict with session_id and activities
    
    Raises:
        ValidationError: If generated output fails validation
        Exception: If generation fails
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    logger.info(
        f"Starting recommendation generation",
        extra={
            "request_id": request_id,
            "rating": session_config.get('rating'),
            "target_activities": session_config.get('target_activities'),
            "activity_type": session_config.get('activity_type')
        }
    )
    
    # Build prompts
    rating = session_config.get('rating', 'R')
    system_prompt = build_system_prompt(rating)
    user_prompt = build_user_prompt(player_a, player_b, session_config, curated_bank)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Call Groq
    try:
        client = get_groq_client()
        
        response_text = client.chat_json_schema(
            messages=messages,
            json_schema=SESSION_RECOMMENDATIONS_SCHEMA,
            temperature=session_config.get('temperature')
        )
        
        # Parse response
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {str(e)}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            raise ValidationError(f"Groq returned invalid JSON: {str(e)}")
        
        # Validate against schema
        try:
            validate_payload(response_data, SESSION_RECOMMENDATIONS_SCHEMA)
        except ValidationError as e:
            logger.error(f"Groq response failed schema validation: {str(e)}")
            logger.error(f"Response data: {json.dumps(response_data, indent=2)[:1000]}")
            raise
        
        # Ensure session_id is set
        if 'session_id' not in response_data or not response_data['session_id']:
            response_data['session_id'] = session_config.get('session_id', str(uuid.uuid4()))
        
        logger.info(
            f"Recommendation generation successful",
            extra={
                "request_id": request_id,
                "session_id": response_data['session_id'],
                "activity_count": len(response_data.get('activities', []))
            }
        )
        
        return response_data
    
    except Exception as e:
        logger.error(
            f"Recommendation generation failed: {str(e)}",
            extra={"request_id": request_id, "error_type": type(e).__name__}
        )
        raise


def regenerate_single_activity(
    failed_activity: Dict[str, Any],
    reason: str,
    player_a: Dict[str, Any],
    player_b: Dict[str, Any],
    seq: int,
    rating: str,
    request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Regenerate a single failed activity.
    
    Args:
        failed_activity: The activity that failed
        reason: Why it failed
        player_a: Player A's profile
        player_b: Player B's profile
        seq: Sequence number
        rating: Session rating
        request_id: Optional request ID for logging
    
    Returns:
        New activity dict or None if regeneration fails
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    logger.info(
        f"Regenerating activity at seq {seq}",
        extra={"request_id": request_id, "reason": reason}
    )
    
    try:
        system_prompt = build_system_prompt(rating)
        user_prompt = build_regeneration_prompt(
            failed_activity, reason, player_a, player_b, seq, rating
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        client = get_groq_client()
        
        # Note: For single activity, we just expect a simple JSON object
        # not the full session schema
        response_text = client.chat_simple(system_prompt, user_prompt)
        
        # Try to parse as JSON
        try:
            # Extract JSON if wrapped in markdown code blocks
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            
            new_activity = json.loads(response_text)
            
            logger.info(
                f"Activity regeneration successful",
                extra={"request_id": request_id, "seq": seq}
            )
            
            return new_activity
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse regenerated activity JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}")
            return None
    
    except Exception as e:
        logger.error(
            f"Activity regeneration failed: {str(e)}",
            extra={"request_id": request_id, "seq": seq}
        )
        return None

