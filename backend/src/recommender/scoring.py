"""
Activity scoring engine for preference-based and power-dynamic ranking.

Scoring weights:
- Mutual interest: 50% (both players want this activity)
- Power alignment: 30% (activity matches player power dynamics)
- Domain fit: 20% (activity matches domain preferences)
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def score_mutual_interest(
    activity_preference_keys: List[str],
    player_a_activities: Dict[str, float],
    player_b_activities: Dict[str, float]
) -> float:
    """
    Score how well activity matches both players' preferences (0-1).
    
    Recognizes directional pairs (_give/_receive, _self/_watching) where
    complementary preferences (A gives, B receives) should score high.
    
    Args:
        activity_preference_keys: List of preference keys from activity
        player_a_activities: Player A's activity preferences {key: score}
        player_b_activities: Player B's activity preferences {key: score}
    
    Returns:
        Score 0-1 (1 = both love it, 0 = mismatch)
    """
    if not activity_preference_keys:
        # No preference keys = neutral activity, score 0.5
        return 0.5
    
    scores = []
    processed_keys = set()
    
    for pref_key in activity_preference_keys:
        if pref_key in processed_keys:
            continue
        
        score_a = player_a_activities.get(pref_key, 0.5)  # Default neutral
        score_b = player_b_activities.get(pref_key, 0.5)
        
        # Check for directional pairs
        is_directional_pair = False
        complementary_score = None
        
        # Check for _give/_receive pairs
        if pref_key.endswith('_give'):
            receive_key = pref_key.replace('_give', '_receive')
            if receive_key in activity_preference_keys:
                processed_keys.add(pref_key)
                processed_keys.add(receive_key)
                is_directional_pair = True
                
                # Get complementary scores
                score_a_receive = player_a_activities.get(receive_key, 0.5)
                score_b_receive = player_b_activities.get(receive_key, 0.5)
                
                # A gives, B receives OR B gives, A receives
                comp1 = min(score_a, score_b_receive)  # A gives → B receives
                comp2 = min(score_b, score_a_receive)  # B gives → A receives
                complementary_score = max(comp1, comp2)  # Best complementary match
        
        # Check for _self/_watching pairs
        elif pref_key.endswith('_self'):
            # Try standard pattern first (_self → _watching)
            watching_key = pref_key.replace('_self', '_watching')
            
            # Special cases: stripping_self pairs with watching_strip (not stripping_watching)
            if pref_key == 'stripping_self':
                watching_key = 'watching_strip'
            elif pref_key == 'solo_pleasure_self':
                watching_key = 'watching_solo_pleasure'
            
            if watching_key in activity_preference_keys:
                processed_keys.add(pref_key)
                processed_keys.add(watching_key)
                is_directional_pair = True
                
                # Get complementary scores
                score_a_watching = player_a_activities.get(watching_key, 0.5)
                score_b_watching = player_b_activities.get(watching_key, 0.5)
                
                # A performs, B watches OR B performs, A watches
                comp1 = min(score_a, score_b_watching)  # A performs → B watches
                comp2 = min(score_b, score_a_watching)  # B performs → A watches
                complementary_score = max(comp1, comp2)  # Best complementary match
        
        # Special cases: watching_strip pairs with stripping_self
        elif pref_key == 'watching_strip':
            self_key = 'stripping_self'
            if self_key in activity_preference_keys:
                processed_keys.add(pref_key)
                processed_keys.add(self_key)
                is_directional_pair = True
                
                score_a_self = player_a_activities.get(self_key, 0.5)
                score_b_self = player_b_activities.get(self_key, 0.5)
                
                comp1 = min(score_a, score_b_self)  # A watches → B performs
                comp2 = min(score_b, score_a_self)  # B watches → A performs
                complementary_score = max(comp1, comp2)
        
        elif pref_key == 'watching_solo_pleasure':
            self_key = 'solo_pleasure_self'
            if self_key in activity_preference_keys:
                processed_keys.add(pref_key)
                processed_keys.add(self_key)
                is_directional_pair = True
                
                score_a_self = player_a_activities.get(self_key, 0.5)
                score_b_self = player_b_activities.get(self_key, 0.5)
                
                comp1 = min(score_a, score_b_self)
                comp2 = min(score_b, score_a_self)
                complementary_score = max(comp1, comp2)
        
        # If we found a directional pair, use complementary score
        if is_directional_pair and complementary_score is not None:
            # Map complementary score to recommendation score
            if complementary_score >= 0.7:
                scores.append(1.0)  # Perfect complementary match
            elif complementary_score >= 0.5:
                scores.append(0.8)  # Good complementary match
            elif complementary_score >= 0.3:
                scores.append(0.6)  # Acceptable
            else:
                scores.append(0.3)  # Weak match
            continue
        
        # Non-directional or single key: use standard logic
        processed_keys.add(pref_key)
        
        # Mutual "yes" (both >= 0.7) = Perfect match
        if score_a >= 0.7 and score_b >= 0.7:
            scores.append(1.0)
        
        # One yes, one maybe (one >= 0.7, other 0.3-0.7) = Good match
        elif (score_a >= 0.7 and 0.3 <= score_b < 0.7) or (score_b >= 0.7 and 0.3 <= score_a < 0.7):
            scores.append(0.6)
        
        # Both neutral/open (both 0.3-0.7) = Acceptable
        elif 0.3 <= score_a < 0.7 and 0.3 <= score_b < 0.7:
            scores.append(0.4)
        
        # One yes, one no (one >= 0.7, other < 0.3) = Mismatch
        elif (score_a >= 0.7 and score_b < 0.3) or (score_b >= 0.7 and score_a < 0.3):
            scores.append(0.1)
        
        # Both no (both < 0.3) = Strong mismatch
        else:
            scores.append(0.0)
    
    # Return average score across all preference keys
    return sum(scores) / len(scores) if scores else 0.5


def score_power_alignment(
    activity_power_role: str,
    player_a_orientation: str,
    player_b_orientation: str
) -> float:
    """
    Score how well activity's power role matches players' orientations (0-1).
    
    Moderate filtering approach:
    - Top activities work for Top or Switch players
    - Bottom activities work for Bottom or Switch players
    - Neutral activities work for everyone
    - Strict mismatches return 0 (filtered out)
    
    Args:
        activity_power_role: "top", "bottom", "switch", or "neutral"
        player_a_orientation: "Top", "Bottom", or "Switch"
        player_b_orientation: "Top", "Bottom", or "Switch"
    
    Returns:
        Score 0-1 (1 = perfect match, 0 = incompatible)
    """
    if not activity_power_role or activity_power_role == 'neutral':
        # Neutral activities work for everyone
        return 1.0
    
    orientations = [player_a_orientation, player_b_orientation]
    
    # Top activity (requires someone to take control/lead)
    if activity_power_role == 'top':
        has_top = any(o == 'Top' for o in orientations)
        has_switch = any(o == 'Switch' for o in orientations)
        has_bottom = any(o == 'Bottom' for o in orientations)
        
        if has_top and has_bottom:
            return 1.0  # Perfect: Top can lead, Bottom can follow
        elif has_top and has_switch:
            return 0.95  # Great: Top leads, Switch adapts
        elif has_top:
            return 0.8  # Good: Top present but no complementary Bottom
        elif has_switch:
            return 0.6  # Okay: Switch can adapt to Top role
        else:
            return 0.0  # Hard mismatch: Both Bottom, activity needs Top
    
    # Bottom activity (requires someone to receive/submit)
    elif activity_power_role == 'bottom':
        has_top = any(o == 'Top' for o in orientations)
        has_switch = any(o == 'Switch' for o in orientations)
        has_bottom = any(o == 'Bottom' for o in orientations)
        
        if has_top and has_bottom:
            return 1.0  # Perfect: Bottom can receive, Top can give
        elif has_bottom and has_switch:
            return 0.95  # Great: Bottom receives, Switch adapts
        elif has_bottom:
            return 0.8  # Good: Bottom present but no complementary Top
        elif has_switch:
            return 0.6  # Okay: Switch can adapt to Bottom role
        else:
            return 0.0  # Hard mismatch: Both Top, activity needs Bottom
    
    # Switch activity (works for any combination)
    elif activity_power_role == 'switch':
        return 1.0  # Flexible activities work for everyone
    
    # Unknown power role
    else:
        logger.warning(f"Unknown power role: {activity_power_role}")
        return 0.5  # Neutral score for unknown


def score_domain_fit(
    activity_domains: List[str],
    player_a_domain_scores: Dict[str, float],
    player_b_domain_scores: Dict[str, float]
) -> float:
    """
    Score how well activity domains match player domain preferences (0-1).
    
    Args:
        activity_domains: List of domain tags [sensual, playful, power, etc.]
        player_a_domain_scores: Player A's domain scores {domain: score}
        player_b_domain_scores: Player B's domain scores {domain: score}
    
    Returns:
        Score 0-1 (higher = better domain match)
    """
    if not activity_domains:
        # No domains = neutral, return 0.5
        return 0.5
    
    scores = []
    
    for domain in activity_domains:
        # Map domain names (activity tags may differ from profile keys)
        domain_key = domain.lower()
        
        # Try exact match or similar
        score_a = player_a_domain_scores.get(domain_key, 0.5)
        score_b = player_b_domain_scores.get(domain_key, 0.5)
        
        # Use average of both players' domain scores
        avg_score = (score_a + score_b) / 2
        scores.append(avg_score)
    
    return sum(scores) / len(scores) if scores else 0.5


def score_activity_for_players(
    activity: Dict[str, Any],
    player_a_profile: Dict[str, Any],
    player_b_profile: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate overall personalization score for an activity-player pair.
    
    Args:
        activity: Activity dict with power_role, preference_keys, domains
        player_a_profile: Complete profile for player A
        player_b_profile: Complete profile for player B
        weights: Optional custom weights (default: mutual=0.5, power=0.3, domain=0.2)
    
    Returns:
        Dict with component scores and overall score
    """
    if weights is None:
        weights = {
            'mutual_interest': 0.5,
            'power_alignment': 0.3,
            'domain_fit': 0.2
        }
    
    # Extract player data
    player_a_activities = player_a_profile.get('activities', {})
    player_b_activities = player_b_profile.get('activities', {})
    player_a_power = player_a_profile.get('power_dynamic', {})
    player_b_power = player_b_profile.get('power_dynamic', {})
    player_a_domains = player_a_profile.get('domain_scores', {})
    player_b_domains = player_b_profile.get('domain_scores', {})
    
    # Extract activity data
    activity_pref_keys = activity.get('preference_keys', [])
    activity_power_role = activity.get('power_role', 'neutral')
    activity_domains = activity.get('domains', [])
    
    # Calculate component scores
    mutual_interest = score_mutual_interest(
        activity_pref_keys,
        player_a_activities,
        player_b_activities
    )
    
    power_alignment = score_power_alignment(
        activity_power_role,
        player_a_power.get('orientation', 'Switch'),
        player_b_power.get('orientation', 'Switch')
    )
    
    domain_fit = score_domain_fit(
        activity_domains,
        player_a_domains,
        player_b_domains
    )
    
    # Calculate weighted overall score
    overall_score = (
        weights['mutual_interest'] * mutual_interest +
        weights['power_alignment'] * power_alignment +
        weights['domain_fit'] * domain_fit
    )
    
    return {
        'mutual_interest_score': round(mutual_interest, 3),
        'power_alignment_score': round(power_alignment, 3),
        'domain_fit_score': round(domain_fit, 3),
        'overall_score': round(overall_score, 3),
        'components': {
            'mutual_interest': mutual_interest,
            'power_alignment': power_alignment,
            'domain_fit': domain_fit
        },
        'weights': weights
    }


def filter_by_power_dynamics(
    activities: List[Dict[str, Any]],
    player_a_orientation: str,
    player_b_orientation: str,
    min_score: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Filter activities based on power dynamic compatibility.
    
    Removes activities that are strictly incompatible with player orientations.
    
    Args:
        activities: List of activity dicts
        player_a_orientation: "Top", "Bottom", or "Switch"
        player_b_orientation: "Top", "Bottom", or "Switch"  
        min_score: Minimum power alignment score to include (default 0.3)
    
    Returns:
        Filtered list of compatible activities
    """
    compatible = []
    
    for activity in activities:
        power_role = activity.get('power_role', 'neutral')
        
        score = score_power_alignment(
            power_role,
            player_a_orientation,
            player_b_orientation
        )
        
        if score >= min_score:
            compatible.append(activity)
    
    logger.debug(
        f"Power filtering: {len(compatible)}/{len(activities)} activities compatible",
        extra={
            'player_a': player_a_orientation,
            'player_b': player_b_orientation,
            'min_score': min_score
        }
    )
    
    return compatible

