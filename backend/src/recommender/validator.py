"""Activity validation logic."""
import jsonschema
from typing import Optional, List, Dict, Any
from .schema import ACTIVITY_OUTPUT_SCHEMA, SESSION_RECOMMENDATIONS_SCHEMA
from .picker import get_intensity_window


class ValidationError(Exception):
    """Raised when activity validation fails."""
    pass


def validate_payload(payload: dict, schema: dict = SESSION_RECOMMENDATIONS_SCHEMA) -> None:
    """
    Validate payload against JSON schema.
    
    Args:
        payload: Data to validate
        schema: JSON schema to validate against
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Schema validation failed: {e.message} at {'.'.join(str(p) for p in e.path)}")
    except jsonschema.SchemaError as e:
        raise ValidationError(f"Invalid schema: {e.message}")


def check_activity_item(
    item: dict,
    seq: int,
    rating: str,
    avoid_maybe_until: int = 6,
    hard_limits: Optional[List[str]] = None,
    target_activities: int = 25
) -> tuple[bool, Optional[str]]:
    """
    Validate a single activity item against rules.
    
    Args:
        item: Activity item dict
        seq: Sequence number
        rating: Session rating (G/R/X)
        avoid_maybe_until: Don't allow maybe items before this step
        hard_limits: List of hard limit keys to avoid
        target_activities: Total activities for intensity window calculation
    
    Returns:
        (is_valid, error_message) tuple
    """
    hard_limits = hard_limits or []
    
    # 1. Check intensity window (rating-aware)
    min_intensity, max_intensity = get_intensity_window(seq, target_activities, rating)
    if not (min_intensity <= item.get('intensity', 0) <= max_intensity):
        return False, f"Intensity {item.get('intensity')} out of range [{min_intensity}-{max_intensity}] for step {seq}"
    
    # 2. Check script length and step count
    script = item.get('script', {})
    steps = script.get('steps', [])
    
    if len(steps) > 2:
        return False, f"Too many steps: {len(steps)} (max 2)"
    
    if len(steps) == 0:
        return False, "No steps in script"
    
    for step_idx, step in enumerate(steps):
        action = step.get('do', '')
        word_count = len(action.split())
        
        # Ideal: 6-15 words, but allow up to 20 for flexibility
        if word_count < 3:
            return False, f"Step {step_idx + 1} too short: {word_count} words (min 3)"
        if word_count > 20:
            return False, f"Step {step_idx + 1} too long: {word_count} words (max 20)"
    
    # 3. Check maybe items before step 6
    checks = item.get('checks', {})
    if seq < avoid_maybe_until and checks.get('maybe_items_present', False):
        return False, f"No Maybe items allowed before step {avoid_maybe_until}"
    
    # 4. Check hard limits
    if not checks.get('respects_hard_limits', True):
        return False, "Activity violates hard limits"
    
    # 5. Check rating consistency
    item_rating = item.get('rating', 'R')
    if not is_rating_compatible(item_rating, rating):
        return False, f"Activity rating {item_rating} incompatible with session rating {rating}"
    
    # 6. Check actor labels are valid
    for step in steps:
        actor = step.get('actor', '')
        if actor not in ['A', 'B']:
            return False, f"Invalid actor label: {actor} (must be A or B)"
    
    # All checks passed
    return True, None


def is_rating_compatible(item_rating: str, session_rating: str) -> bool:
    """
    Check if an activity rating is compatible with session rating.
    
    Rules:
    - G session: only G activities
    - R session: G or R activities
    - X session: any rating
    """
    rating_hierarchy = {'G': 0, 'R': 1, 'X': 2}
    
    item_level = rating_hierarchy.get(item_rating, 1)
    session_level = rating_hierarchy.get(session_rating, 1)
    
    return item_level <= session_level


def validate_activity_sequence(activities: List[dict], config: dict) -> tuple[bool, List[str]]:
    """
    Validate a complete sequence of activities.
    
    Args:
        activities: List of activity dicts
        config: Session configuration dict
    
    Returns:
        (is_valid, error_messages) tuple
    """
    errors = []
    
    rating = config.get('rating', 'R')
    target = config.get('target_activities', 25)
    hard_limits = config.get('hard_limits', [])
    avoid_maybe_until = config.get('rules', {}).get('avoid_maybe_until', 6)
    
    # Check each activity
    for activity in activities:
        seq = activity.get('seq', 0)
        is_valid, error = check_activity_item(
            activity, seq, rating, avoid_maybe_until, hard_limits, target
        )
        
        if not is_valid:
            errors.append(f"Step {seq}: {error}")
    
    # Check warmup truths requirement
    truth_count_in_warmup = sum(
        1 for a in activities 
        if a.get('seq', 0) <= 5 and a.get('type') == 'truth'
    )
    if truth_count_in_warmup < 2:
        errors.append(f"Warmup (steps 1-5) must have at least 2 truths, found {truth_count_in_warmup}")
    
    return len(errors) == 0, errors

