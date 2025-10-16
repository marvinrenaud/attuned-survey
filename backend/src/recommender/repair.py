"""Activity repair and fallback logic."""
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def fast_repair(
    bad_item: dict,
    seq: int,
    rating: str,
    activity_type: str,
    intensity_min: int,
    intensity_max: int,
    candidates: List[dict],
    hard_limits: Optional[List[str]] = None
) -> Optional[dict]:
    """
    Attempt to repair a failed activity by finding a suitable replacement.
    
    Strategy:
    1. Try same intensity window + same type from candidates
    2. Try neighbor intensity (±1) + same type
    3. Try any intensity + same type
    4. Use safe fallback template
    5. Return None (caller can regenerate with AI if enabled)
    
    Args:
        bad_item: The failed activity item
        seq: Sequence number
        rating: Session rating
        activity_type: 'truth' or 'dare'
        intensity_min: Minimum intensity for this step
        intensity_max: Maximum intensity for this step
        candidates: List of candidate activities from database
        hard_limits: List of hard limit keys to avoid
    
    Returns:
        Repaired activity dict or None if repair failed
    """
    hard_limits = hard_limits or []
    
    # Strategy 1: Same intensity window + same type
    matches = [
        c for c in candidates
        if c.get('type') == activity_type
        and intensity_min <= c.get('intensity', 0) <= intensity_max
        and c.get('rating') == rating
        and not has_hard_limit_conflict(c, hard_limits)
    ]
    
    if matches:
        logger.info(f"Repair: Found {len(matches)} exact matches for {activity_type} intensity {intensity_min}-{intensity_max}")
        return matches[0]
    
    # Strategy 2: Neighbor intensity (±1)
    neighbor_min = max(1, intensity_min - 1)
    neighbor_max = min(5, intensity_max + 1)
    
    matches = [
        c for c in candidates
        if c.get('type') == activity_type
        and neighbor_min <= c.get('intensity', 0) <= neighbor_max
        and c.get('rating') == rating
        and not has_hard_limit_conflict(c, hard_limits)
    ]
    
    if matches:
        logger.info(f"Repair: Found {len(matches)} neighbor intensity matches")
        return matches[0]
    
    # Strategy 3: Any intensity, same type
    matches = [
        c for c in candidates
        if c.get('type') == activity_type
        and c.get('rating') == rating
        and not has_hard_limit_conflict(c, hard_limits)
    ]
    
    if matches:
        logger.warning(f"Repair: Using any intensity match (desperation mode)")
        return matches[0]
    
    # Strategy 4: Safe fallback templates
    fallback = get_safe_fallback(activity_type, seq, rating, intensity_min, intensity_max)
    if fallback:
        logger.warning(f"Repair: Using safe fallback template")
        return fallback
    
    # Strategy 5: Give up (caller can regenerate)
    logger.error(f"Repair failed: No suitable replacement found for {activity_type} at step {seq}")
    return None


def has_hard_limit_conflict(activity: dict, hard_limits: List[str]) -> bool:
    """Check if activity conflicts with hard limits."""
    activity_limits = activity.get('hard_limit_keys', [])
    if not activity_limits:
        return False
    
    return any(limit in hard_limits for limit in activity_limits)


def get_safe_fallback(
    activity_type: str,
    seq: int,
    rating: str,
    intensity_min: int,
    intensity_max: int
) -> Optional[dict]:
    """
    Get a safe fallback activity template.
    
    These are ultra-safe, generic activities that should work for any pair.
    """
    # Use middle of intensity range
    intensity = (intensity_min + intensity_max) // 2
    
    # Safe truth fallbacks
    truth_fallbacks = {
        1: "Share your favorite memory from this year",
        2: "Describe what attracted you to your partner",
        3: "Share a fantasy you'd like to explore together",
        4: "Describe your ideal intimate evening",
        5: "Share your deepest desire for this relationship"
    }
    
    # Safe dare fallbacks
    dare_fallbacks = {
        1: "Give your partner a genuine compliment",
        2: "Massage your partner's shoulders for 30 seconds",
        3: "Kiss your partner passionately for 10 seconds",
        4: "Undress your partner slowly and mindfully",
        5: "Pleasure your partner using only your hands"
    }
    
    fallbacks = truth_fallbacks if activity_type == 'truth' else dare_fallbacks
    
    # Adjust for rating
    if rating == 'G':
        intensity = min(intensity, 2)  # Cap at gentle for G-rated
    
    description = fallbacks.get(intensity)
    if not description:
        return None
    
    return {
        'type': activity_type,
        'rating': rating,
        'intensity': intensity,
        'script': {
            'steps': [
                {'actor': 'A', 'do': description}
            ]
        },
        'tags': ['fallback', 'safe'],
        'provenance': {
            'source': 'bank',
            'template_id': None
        },
        'checks': {
            'respects_hard_limits': True,
            'uses_yes_overlap': True,
            'maybe_items_present': False,
            'anatomy_ok': True,
            'power_alignment': None,
            'notes': 'Safe fallback template'
        }
    }


def create_placeholder_activity(
    seq: int,
    activity_type: str,
    rating: str,
    intensity: int
) -> dict:
    """Create a placeholder activity when all else fails."""
    return {
        'id': f'placeholder_{seq}',
        'seq': seq,
        'type': activity_type,
        'rating': rating,
        'intensity': intensity,
        'roles': {'active_player': 'A', 'partner_player': 'B'},
        'script': {
            'steps': [
                {
                    'actor': 'A',
                    'do': f'Placeholder {activity_type} activity - please regenerate'
                }
            ]
        },
        'tags': ['placeholder'],
        'provenance': {'source': 'bank', 'template_id': None},
        'checks': {
            'respects_hard_limits': True,
            'uses_yes_overlap': False,
            'maybe_items_present': False,
            'anatomy_ok': True,
            'power_alignment': None,
            'notes': 'Placeholder - regeneration recommended'
        }
    }

