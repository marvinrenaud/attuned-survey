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


def score_truth_topic_fit(
    activity_type: str,
    activity_truth_topics: Optional[List[str]],
    player_a_truth_topics: Dict[str, float],
    player_b_truth_topics: Dict[str, float]
) -> Optional[float]:
    """
    Score how well activity's truth topics match player preferences.

    Returns None to BYPASS scoring (for dares or untagged truth activities).
    When scoring applies, uses minimum of both players' preferences.

    Note: Hard filtering (blocking activities where either player said NO)
    is done in repository.py. This function only handles soft ranking
    for activities that passed the hard filter.

    Args:
        activity_type: "truth" or "dare"
        activity_truth_topics: List of topic keys from activity.truth_topics
        player_a_truth_topics: Player A's topic preferences {topic: 0.0-1.0}
        player_b_truth_topics: Player B's topic preferences {topic: 0.0-1.0}

    Returns:
        None - if dare activity or no truth_topics (bypass, don't include in weighted avg)
        float 0-1 - score based on min of both players' preferences (YES=1.0 > MAYBE=0.5)
    """
    # Bypass for dares - truth topic scoring doesn't apply
    if activity_type != 'truth':
        return None

    # Bypass for untagged truth activities - no penalty, normal scoring
    if not activity_truth_topics:
        return None

    # Score using minimum (most restrictive player sets the ceiling)
    # At this point, hard filtering has already removed activities where
    # either player said NO (0.0), so we're only ranking YES vs MAYBE
    scores = []
    for topic in activity_truth_topics:
        score_a = player_a_truth_topics.get(topic, 0.5)  # Default neutral
        score_b = player_b_truth_topics.get(topic, 0.5)
        scores.append(min(score_a, score_b))

    return sum(scores) / len(scores) if scores else 0.5


def score_activity_for_players(
    activity: Dict[str, Any],
    player_a_profile: Dict[str, Any],
    player_b_profile: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    session_context: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Calculate overall personalization score for an activity-player pair.

    Args:
        activity: Activity dict with power_role, preference_keys, domains
        player_a_profile: Complete profile for player A
        player_b_profile: Complete profile for player B
        weights: Optional custom weights (default: mutual=0.5, power=0.3, domain=0.2)
        session_context: Optional dict with 'seq' and 'target' for pacing

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

    # Extract arousal data
    arousal_a = player_a_profile.get('arousal_propensity', {})
    arousal_b = player_b_profile.get('arousal_propensity', {})
    se_a = arousal_a.get('sexual_excitation', 0.5)
    se_b = arousal_b.get('sexual_excitation', 0.5)
    sisp_a = arousal_a.get('inhibition_performance', 0.5)
    sisp_b = arousal_b.get('inhibition_performance', 0.5)

    # Extract truth topics data
    player_a_truth_topics = player_a_profile.get('truth_topics', {})
    player_b_truth_topics = player_b_profile.get('truth_topics', {})

    # Extract activity data
    activity_type = activity.get('type', 'dare')
    activity_pref_keys = activity.get('preference_keys', [])
    activity_power_role = activity.get('power_role', 'neutral')
    activity_domains = activity.get('domains', [])
    activity_truth_topics = activity.get('truth_topics', [])
    activity_intensity = activity.get('intensity', activity.get('intensity_level', 2))
    is_performance = activity.get('is_performance', activity.get('performance_pressure', 'low') in ['high', 'moderate'])

    # Map intensity_level string to numeric if needed
    if isinstance(activity_intensity, str):
        intensity_map = {'gentle': 1, 'moderate': 2, 'intense': 3}
        activity_intensity = intensity_map.get(activity_intensity, 2)

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

    # Calculate truth topic fit (returns None to bypass for dares/untagged)
    truth_topic_fit = score_truth_topic_fit(
        activity_type,
        activity_truth_topics,
        player_a_truth_topics,
        player_b_truth_topics
    )

    # Calculate arousal modifiers
    se_pacing_modifier = 0.0
    sisp_modifier = 0.0

    if session_context:
        seq = session_context.get('seq', 1)
        target = session_context.get('target', 25)
        se_pacing_modifier = calculate_se_pacing_modifier(
            activity_intensity, se_a, se_b, seq, target
        )

    sisp_modifier = calculate_sisp_modifier(is_performance, sisp_a, sisp_b)

    # Calculate weighted overall score
    # If truth_topic_fit is not None, include it with adjusted weights
    if truth_topic_fit is not None:
        # Adjust weights to include truth topic fit (15% of total)
        adjusted_weights = {
            'mutual_interest': weights['mutual_interest'] * 0.85,  # 50% → 42.5%
            'power_alignment': weights['power_alignment'] * 0.85,  # 30% → 25.5%
            'domain_fit': weights['domain_fit'] * 0.85,            # 20% → 17%
            'truth_topic_fit': 0.15                                 # 15% for truth topics
        }
        base_score = (
            adjusted_weights['mutual_interest'] * mutual_interest +
            adjusted_weights['power_alignment'] * power_alignment +
            adjusted_weights['domain_fit'] * domain_fit +
            adjusted_weights['truth_topic_fit'] * truth_topic_fit
        )
        used_weights = adjusted_weights
    else:
        # No truth topic scoring - use original weights
        base_score = (
            weights['mutual_interest'] * mutual_interest +
            weights['power_alignment'] * power_alignment +
            weights['domain_fit'] * domain_fit
        )
        used_weights = weights

    # Apply arousal modifiers
    overall_score = base_score + se_pacing_modifier + sisp_modifier
    overall_score = max(0.0, min(1.0, overall_score))  # Clamp to 0-1

    return {
        'mutual_interest_score': round(mutual_interest, 3),
        'power_alignment_score': round(power_alignment, 3),
        'domain_fit_score': round(domain_fit, 3),
        'truth_topic_fit_score': round(truth_topic_fit, 3) if truth_topic_fit is not None else None,
        'se_pacing_modifier': round(se_pacing_modifier, 3),
        'sisp_modifier': round(sisp_modifier, 3),
        'overall_score': round(overall_score, 3),
        'components': {
            'mutual_interest': mutual_interest,
            'power_alignment': power_alignment,
            'domain_fit': domain_fit,
            'truth_topic_fit': truth_topic_fit,
            'se_pacing': se_pacing_modifier,
            'sisp': sisp_modifier,
        },
        'weights': used_weights
    }


def calculate_se_pacing_modifier(
    activity_intensity: int,
    se_a: float,
    se_b: float,
    seq: int,
    target: int = 25
) -> float:
    """
    Calculate SE-based pacing modifier for activity scoring.

    High SE pairs can handle faster intensity progression.
    Low SE pairs benefit from slower buildup.

    The session is divided into phases:
    - Early (0-20%): expected intensity ~1.5
    - Build (20-60%): expected intensity ~2.5
    - Peak (60-88%): expected intensity ~3.5
    - Afterglow (88-100%): expected intensity ~2.5

    High SE pairs get +0.5 to expected intensity (can handle more earlier).
    Low SE pairs get -0.5 to expected intensity (need slower buildup).

    Args:
        activity_intensity: Activity intensity level (1-5)
        se_a: Player A's SE score (0-1)
        se_b: Player B's SE score (0-1)
        seq: Current sequence number in session
        target: Total target activities

    Returns:
        Modifier to add to activity score (-0.05 to 0.05)
    """
    avg_se = (se_a + se_b) / 2
    progress = seq / target  # 0.0 to 1.0

    # Expected intensity at this point in session
    # Early (0-20%): intensity 1-2
    # Mid (20-60%): intensity 2-3
    # Peak (60-88%): intensity 3-4
    # Afterglow (88-100%): intensity 2-3
    if progress <= 0.2:
        expected_intensity = 1.5
    elif progress <= 0.6:
        expected_intensity = 2.5
    elif progress <= 0.88:
        expected_intensity = 3.5
    else:
        expected_intensity = 2.5

    # High SE pairs can handle higher intensity earlier
    if avg_se >= 0.65:
        se_intensity_bonus = 0.5  # Allow 0.5 higher intensity
    elif avg_se < 0.35:
        se_intensity_bonus = -0.5  # Prefer 0.5 lower intensity
    else:
        se_intensity_bonus = 0.0

    adjusted_expected = expected_intensity + se_intensity_bonus

    # Calculate how well this activity fits the adjusted expectation
    intensity_diff = abs(activity_intensity - adjusted_expected)

    # Convert to modifier (-0.05 to 0.05)
    # Perfect match = +0.05, far off = -0.05
    if intensity_diff <= 0.5:
        return 0.05
    elif intensity_diff <= 1.0:
        return 0.02
    elif intensity_diff <= 1.5:
        return 0.0
    else:
        return -0.05


def calculate_sisp_modifier(
    is_performance_activity: bool,
    sisp_a: float,
    sisp_b: float
) -> float:
    """
    Calculate SIS-P modifier for performance-pressure activities.

    High SIS-P individuals experience arousal drop under performance pressure.
    Activities that put someone "on the spot" should be deprioritized.

    Args:
        is_performance_activity: Whether activity has performance pressure
        sisp_a: Player A's SIS-P score (0-1)
        sisp_b: Player B's SIS-P score (0-1)

    Returns:
        Modifier: 0 for non-performance, -0.15 to 0 for performance based on SIS-P
    """
    if not is_performance_activity:
        return 0.0

    # Use max SIS-P (most performance-anxious person)
    max_sisp = max(sisp_a, sisp_b)

    if max_sisp >= 0.65:
        # High performance anxiety - significant penalty
        return -0.15
    elif max_sisp >= 0.50:
        # Moderate - small penalty
        return -0.05
    else:
        # Low - no penalty
        return 0.0


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

