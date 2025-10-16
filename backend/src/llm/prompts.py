"""Prompt builders for activity generation."""
import json
from typing import Dict, Any, List, Optional


def build_system_prompt(rating: str = 'R') -> str:
    """
    Build system prompt with rules and constraints.
    
    Args:
        rating: Content rating (G, R, or X)
    
    Returns:
        System prompt string
    """
    rating_guidelines = {
        'G': "Activities must be family-friendly, non-sexual, and suitable for all audiences. Focus on emotional connection, communication, and playful interaction.",
        'R': "Activities can include sensual and intimate content but should avoid explicit sexual acts. Focus on building desire, connection, and exploration within boundaries.",
        'X': "Activities can include explicit sexual content but must always respect consent and boundaries. Focus on mutual pleasure and exploration."
    }
    
    guidelines = rating_guidelines.get(rating, rating_guidelines['R'])
    
    return f"""You are an expert intimacy coach creating personalized activities for couples. Your goal is to generate activities that promote connection, communication, and mutual pleasure while respecting boundaries.

CRITICAL RULES:
1. **Consent First**: All activities MUST respect hard limits. Never suggest anything in a player's hard_limits list.
2. **Rating Gates**: {guidelines}
3. **Progression**: Activities should follow an intensity arc:
   - Warmup (steps 1-5): Gentle, connection-building (intensity 1-2)
   - Build (steps 6-15): Increasing intimacy (intensity 2-3)
   - Peak (steps 16-22): Most intense activities (intensity 4-5)
   - Afterglow (steps 23-25): Wind down, connection (intensity 2-3)
4. **Actor Labels**: Always use "A" and "B" for players, never names or pronouns.
5. **Brevity**: Each step description should be 6-15 words. Max 2 steps per activity.
6. **Maybe Items**: Do not include "maybe" items before step 6. These are activities players are uncertain about.
7. **Anatomy Match**: Ensure activities match players' anatomy (inferred from sex field).
8. **Power Dynamics**: Consider players' power preferences (Top/Bottom/Switch).
9. **Mutual Interest**: Prioritize activities both players marked as "Yes" (score >= 0.7).

OUTPUT FORMAT:
- Provide a complete session with the requested number of activities
- Each activity must have: id, seq, type (truth/dare), rating, intensity, roles, script (with steps), tags, provenance, and checks
- The "checks" field should validate: respects_hard_limits, uses_yes_overlap, maybe_items_present, anatomy_ok
- Ensure variety in activity types and intensities within the appropriate windows

REMEMBER: Safety, consent, and mutual enjoyment are paramount. When in doubt, choose the safer, more consensual option."""


def build_user_prompt(
    player_a: Dict[str, Any],
    player_b: Dict[str, Any],
    session_config: Dict[str, Any],
    curated_bank: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Build user prompt with player profiles and session configuration.
    
    Args:
        player_a: Player A's profile dict
        player_b: Player B's profile dict
        session_config: Session configuration dict
        curated_bank: Optional list of pre-selected activities to consider
    
    Returns:
        User prompt string
    """
    # Extract key profile information
    a_power = player_a.get('power_dynamic', {})
    b_power = player_b.get('power_dynamic', {})
    
    a_activities = player_a.get('activities', {})
    b_activities = player_b.get('activities', {})
    
    a_boundaries = player_a.get('boundaries', {})
    b_boundaries = player_b.get('boundaries', {})
    
    a_hard_limits = a_boundaries.get('hard_limits', [])
    b_hard_limits = b_boundaries.get('hard_limits', [])
    all_hard_limits = list(set(a_hard_limits + b_hard_limits))
    
    # Find mutual interests (both >= 0.7)
    mutual_interests = []
    for activity_key in a_activities:
        if activity_key in b_activities:
            if a_activities[activity_key] >= 0.7 and b_activities[activity_key] >= 0.7:
                mutual_interests.append(activity_key)
    
    # Session configuration
    rating = session_config.get('rating', 'R')
    target_activities = session_config.get('target_activities', 25)
    activity_type = session_config.get('activity_type', 'random')
    
    prompt = f"""Generate {target_activities} activities for a couple's intimacy session.

PLAYER A PROFILE:
- Power Dynamic: {a_power.get('orientation', 'Switch')} (intensity: {a_power.get('intensity', 0.5)})
- Sex: {player_a.get('sex', 'not specified')}
- Hard Limits (NEVER suggest): {', '.join(all_hard_limits) if all_hard_limits else 'None specified'}

PLAYER B PROFILE:
- Power Dynamic: {b_power.get('orientation', 'Switch')} (intensity: {b_power.get('intensity', 0.5)})
- Sex: {player_b.get('sex', 'not specified')}

MUTUAL INTERESTS (prioritize these):
{', '.join(mutual_interests[:20]) if mutual_interests else 'None identified - use general activities'}

SESSION CONFIGURATION:
- Rating: {rating}
- Total Activities: {target_activities}
- Activity Type Mode: {activity_type}
- Warmup Phase (steps 1-5): Intensity 1-2
- Build Phase (steps 6-15): Intensity 2-3
- Peak Phase (steps 16-22): Intensity 4-5
- Afterglow Phase (steps 23-25): Intensity 2-3

SPECIAL REQUIREMENTS:
- Ensure at least 2 "truth" activities in steps 1-5 (warmup)
- Balance ~50/50 between truths and dares (unless activity_type is 'truth' or 'dare')
- Consider power dynamics when assigning roles
- Vary intensity within each phase's range
- Include variety in tags (verbal, physical, sensual, intimate, playful, etc.)

OUTPUT:
Generate the complete session as a JSON object matching the schema with session_id and activities array."""

    if curated_bank:
        prompt += f"\n\nCURATED ACTIVITY BANK (consider adapting these):\n"
        prompt += json.dumps(curated_bank[:10], indent=2)  # Include up to 10 examples
    
    return prompt


def build_regeneration_prompt(
    failed_activity: Dict[str, Any],
    reason: str,
    player_a: Dict[str, Any],
    player_b: Dict[str, Any],
    seq: int,
    rating: str
) -> str:
    """
    Build prompt for regenerating a single failed activity.
    
    Args:
        failed_activity: The activity that failed validation
        reason: Why it failed
        player_a: Player A's profile
        player_b: Player B's profile
        seq: Sequence number for the activity
        rating: Session rating
    
    Returns:
        User prompt string for regeneration
    """
    from ..recommender.picker import get_intensity_window, get_phase_name
    
    intensity_min, intensity_max = get_intensity_window(seq)
    phase = get_phase_name(seq)
    
    a_hard_limits = player_a.get('boundaries', {}).get('hard_limits', [])
    b_hard_limits = player_b.get('boundaries', {}).get('hard_limits', [])
    all_hard_limits = list(set(a_hard_limits + b_hard_limits))
    
    return f"""The previous activity failed validation. Please generate a replacement.

FAILURE REASON: {reason}

REQUIREMENTS FOR STEP {seq}:
- Phase: {phase}
- Intensity Range: {intensity_min}-{intensity_max}
- Rating: {rating}
- Type: {failed_activity.get('type', 'either truth or dare')}
- Hard Limits to Avoid: {', '.join(all_hard_limits) if all_hard_limits else 'None'}

PREVIOUS ATTEMPT (failed):
{json.dumps(failed_activity, indent=2)}

Generate a single activity that addresses the failure reason and meets all requirements. Return as a JSON object matching the activity schema."""

