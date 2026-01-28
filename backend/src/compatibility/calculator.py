"""
Compatibility calculator - Python port of frontend/src/lib/matching/compatibilityMapper.js

This implements the v0.4/v0.5 compatibility algorithm with:
- Power complement calculation
- Domain similarity
- Activity overlap with asymmetric matching
- Truth topic overlap
- Boundary conflict detection
"""
import math
from typing import Dict, List, Any, Optional, Tuple


def calculate_se_modifier(se_a: float, se_b: float) -> float:
    """
    Calculate SE (Sexual Excitation) compatibility modifier.

    Research basis: Kim et al. 2021 - "Both high" > "Both low" for satisfaction.
    Pawłowska et al. 2023 - Similarity at high levels benefits satisfaction.

    Args:
        se_a: Player A's SE score (0-1)
        se_b: Player B's SE score (0-1)

    Returns:
        Modifier value: 0.03 (both high), 0.015 (high+mid), 0.005 (high+low), 0.0 (other)
    """
    HIGH = 0.65
    LOW = 0.35

    a_high = se_a >= HIGH
    b_high = se_b >= HIGH
    a_low = se_a < LOW
    b_low = se_b < LOW

    if a_high and b_high:
        # Both high - best outcome (mutual responsiveness)
        return 0.03

    elif a_high or b_high:
        # One high - check what the other is
        other = se_b if a_high else se_a
        if other >= LOW:  # Other is mid-range
            return 0.015
        else:  # Other is low
            return 0.005

    else:
        # Both mid, both low, or mid+low
        return 0.0


def calculate_sisc_modifier(sisc_a: float, sisc_b: float) -> float:
    """
    Calculate SIS-C (Consequence Inhibition) compatibility modifier.

    Research basis: Kinsey Institute research - risk tolerance alignment matters.
    Significant mismatch in SIS-C creates friction around comfort zones.

    Args:
        sisc_a: Player A's SIS-C score (0-1)
        sisc_b: Player B's SIS-C score (0-1)

    Returns:
        Modifier value: 0.02 (both mid), -0.02 (mismatch > 0.4), 0.0 (other)
    """
    MID_LOW = 0.35
    MID_HIGH = 0.65
    MISMATCH_THRESHOLD = 0.4

    delta = abs(sisc_a - sisc_b)
    both_mid = (MID_LOW <= sisc_a <= MID_HIGH) and (MID_LOW <= sisc_b <= MID_HIGH)

    if delta > MISMATCH_THRESHOLD:
        # Significant mismatch - potential friction on risk tolerance
        return -0.02

    elif both_mid:
        # Both flexible/adaptable - positive signal
        return 0.02

    else:
        # Both high or both low - aligned, neutral
        return 0.0


def calculate_power_complement(power_a: Dict[str, Any], power_b: Dict[str, Any]) -> float:
    """
    Calculate power dynamic complement (0-1).
    
    Top/Bottom pairs score higher, same-pole pairs can still work.
    """
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')
    intensity_a = power_a.get('intensity', 0.5)
    intensity_b = power_b.get('intensity', 0.5)
    
    # Perfect complement: Top + Bottom
    if (orientation_a == 'Top' and orientation_b == 'Bottom') or \
       (orientation_a == 'Bottom' and orientation_b == 'Top'):
        # Higher intensity difference = better complement
        intensity_alignment = 1.0 - abs(intensity_a - intensity_b) * 0.3
        return min(1.0, intensity_alignment)
    
    # Both Switch: Good compatibility
    if orientation_a == 'Switch' and orientation_b == 'Switch':
        return 0.85
    
    # One Switch: Moderate compatibility
    if orientation_a == 'Switch' or orientation_b == 'Switch':
        return 0.75
    
    # Same pole (both Top or both Bottom): Lower but not zero
    return 0.50


def calculate_domain_similarity(
    domains_a: Dict[str, float],
    domains_b: Dict[str, float],
    power_a: Dict[str, Any],
    power_b: Dict[str, Any]
) -> float:
    """
    Calculate domain similarity (0-1).
    
    For complementary power dynamics (Top/Bottom), divergence in exploration/verbal is beneficial.
    """
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')
    
    is_complementary = (orientation_a == 'Top' and orientation_b == 'Bottom') or \
                      (orientation_a == 'Bottom' and orientation_b == 'Top')
    
    # Calculate distances (0-1)
    # Normalize scores to 0-1 if they are 0-100
    def norm(s): return s / 100.0 if s > 1.0 else s
    
    sensation_dist = 1.0 - abs(norm(domains_a.get('sensation', 0)) - norm(domains_b.get('sensation', 0)))
    connection_dist = 1.0 - abs(norm(domains_a.get('connection', 0)) - norm(domains_b.get('connection', 0)))
    power_dist = 1.0 - abs(norm(domains_a.get('power', 0)) - norm(domains_b.get('power', 0)))
    
    if is_complementary:
        # For complementary pairs, use minimum threshold approach for exploration/verbal
        exp_a = domains_a.get('exploration', 0)
        exp_b = domains_b.get('exploration', 0)
        verb_a = domains_a.get('verbal', 0)
        verb_b = domains_b.get('verbal', 0)
        
        # Ensure 0-100 scale for threshold check
        if exp_a <= 1.0: exp_a *= 100
        if exp_b <= 1.0: exp_b *= 100
        if verb_a <= 1.0: verb_a *= 100
        if verb_b <= 1.0: verb_b *= 100
        
        min_exploration = min(exp_a, exp_b)
        min_verbal = min(verb_a, verb_b)
        
        # If minimum is 50+, score is 1.0 (no penalty)
        # If minimum is below 50, scale proportionally
        exploration_score = 1.0 if min_exploration >= 50 else min_exploration / 50.0
        verbal_score = 1.0 if min_verbal >= 50 else min_verbal / 50.0
        
        return (sensation_dist + connection_dist + power_dist + exploration_score + verbal_score) / 5.0
    else:
        # For Switch/Switch or same-pole pairs, use standard distance
        exploration_dist = 1.0 - abs(norm(domains_a.get('exploration', 0)) - norm(domains_b.get('exploration', 0)))
        verbal_dist = 1.0 - abs(norm(domains_a.get('verbal', 0)) - norm(domains_b.get('verbal', 0)))
        
        return (sensation_dist + connection_dist + power_dist + exploration_dist + verbal_dist) / 5.0


def calculate_asymmetric_directional_jaccard(
    top_activities: Dict[str, float],
    bottom_activities: Dict[str, float]
) -> float:
    """
    Asymmetric directional Jaccard for Top/Bottom pairs.
    
    Mirrors frontend/src/lib/matching/compatibilityMapper.js logic.
    
    Recognizes complementary pairs:
    - _give/_receive (e.g., spanking_give with spanking_receive)
    - _self/_watching (e.g., stripping_self with watching_strip)
    
    Primary axis (80% weight): Does Top want to GIVE what Bottom wants to RECEIVE?
    Secondary axis (20% weight): Does Bottom want to GIVE what Top wants to RECEIVE?
    """
    keys = set(list(top_activities.keys()) + list(bottom_activities.keys()))
    
    primary_matches = 0
    primary_potential = 0
    secondary_matches = 0
    secondary_potential = 0
    non_directional_matches = 0
    non_directional_potential = 0
    
    processed_keys = set()
    
    for key in keys:
        if key in processed_keys:
            continue
            
        # print(f"Processing key: {key}")
        top_val = top_activities.get(key, 0)
        bottom_val = bottom_activities.get(key, 0)
        
        # Handle _give/_receive pairs
        if key.endswith('_give'):
            processed_keys.add(key)
            receive_key = key.replace('_give', '_receive')
            processed_keys.add(receive_key)
            
            bottom_receive_val = bottom_activities.get(receive_key, 0)
            top_receive_val = top_activities.get(receive_key, 0)
            
            # PRIMARY: Top gives → Bottom receives
            if top_val >= 0.5 or bottom_receive_val >= 0.5:
                primary_potential += 1
                if top_val >= 0.5 and bottom_receive_val >= 0.5:
                    primary_matches += 1
            
            # SECONDARY: Bottom gives → Top receives
            if bottom_val >= 0.5 or top_receive_val >= 0.5:
                secondary_potential += 1
                if bottom_val >= 0.5 and top_receive_val >= 0.5:
                    secondary_matches += 1
                elif bottom_val >= 0.5 and top_receive_val < 0.5:
                    secondary_matches += 0.5  # Partial credit
        
        # Handle _self/_watching pairs (Display & Performance)
        elif key.endswith('_self'):
            # Skip special cases handled elsewhere
            if key in ['stripping_self', 'solo_pleasure_self']:
                continue
                
            processed_keys.add(key)
            watching_key = key.replace('_self', '_watching')
            processed_keys.add(watching_key)
            
            top_watching_val = top_activities.get(watching_key, 0)
            bottom_watching_val = bottom_activities.get(watching_key, 0)
            
            # PRIMARY: Bottom performs → Top watches
            if bottom_val >= 0.5 or top_watching_val >= 0.5:
                primary_potential += 1
                if bottom_val >= 0.5 and top_watching_val >= 0.5:
                    primary_matches += 1
            
            # SECONDARY: Top performs → Bottom watches
            if top_val >= 0.5 or bottom_watching_val >= 0.5:
                secondary_potential += 1
                if top_val >= 0.5 and bottom_watching_val >= 0.5:
                    secondary_matches += 1
                elif top_val >= 0.5 and bottom_watching_val < 0.5:
                    secondary_matches += 0.5  # Partial credit
        
        # Handle special cases: watching_strip pairs with stripping_self
        elif key == 'watching_strip':
            processed_keys.add(key)
            self_key = 'stripping_self'
            processed_keys.add(self_key)
            
            top_self_val = top_activities.get(self_key, 0)
            bottom_self_val = bottom_activities.get(self_key, 0)
            
            # PRIMARY: Bottom performs → Top watches
            if bottom_self_val >= 0.5 or top_val >= 0.5:
                primary_potential += 1
                if bottom_self_val >= 0.5 and top_val >= 0.5:
                    primary_matches += 1
            
            # SECONDARY: Top performs → Bottom watches
            if top_self_val >= 0.5 or bottom_val >= 0.5:
                secondary_potential += 1
                if top_self_val >= 0.5 and bottom_val >= 0.5:
                    secondary_matches += 1
                elif top_self_val >= 0.5 and bottom_val < 0.5:
                    secondary_matches += 0.5
        
        # Handle special case: watching_solo_pleasure pairs with solo_pleasure_self
        elif key == 'watching_solo_pleasure':
            processed_keys.add(key)
            self_key = 'solo_pleasure_self'
            processed_keys.add(self_key)
            
            top_self_val = top_activities.get(self_key, 0)
            bottom_self_val = bottom_activities.get(self_key, 0)
            
            # PRIMARY: Bottom performs → Top watches
            if bottom_self_val >= 0.5 or top_val >= 0.5:
                primary_potential += 1
                if bottom_self_val >= 0.5 and top_val >= 0.5:
                    primary_matches += 1
            
            # SECONDARY: Top performs → Bottom watches
            if top_self_val >= 0.5 or bottom_val >= 0.5:
                secondary_potential += 1
                if top_self_val >= 0.5 and bottom_val >= 0.5:
                    secondary_matches += 1
                elif top_self_val >= 0.5 and bottom_val < 0.5:
                    secondary_matches += 0.5
        
        # Non-directional activities
        elif not key.endswith('_receive') and not key.endswith('_watching'):
            processed_keys.add(key)
            
            if top_val >= 0.5 and bottom_val >= 0.5:
                non_directional_matches += 1
            if top_val >= 0.5 or bottom_val >= 0.5:
                non_directional_potential += 1
    
    # Weight primary axis more heavily (80%) than secondary (20%)
    total_matches = (primary_matches * 0.8) + (secondary_matches * 0.2) + non_directional_matches
    total_potential = (primary_potential * 0.8) + (secondary_potential * 0.2) + non_directional_potential
    
    if total_potential == 0:
        return 0
    
    return total_matches / total_potential


def calculate_same_pole_jaccard(
    activities_a: Dict[str, float],
    activities_b: Dict[str, float]
) -> float:
    """
    Same-pole Jaccard for Top/Top or Bottom/Bottom pairs.
    
    For these pairs, matching on giving/receiving is actually INCOMPATIBLE.
    Only compatible if one or both are versatile (can switch roles within activity).
    
    Mirrors frontend/src/lib/matching/compatibilityMapper.js calculateSamePoleJaccard()
    """
    keys = set(list(activities_a.keys()) + list(activities_b.keys()))
    
    compatible_interactions = 0
    total_possible_interactions = 0
    
    for key in keys:
        val_a = activities_a.get(key, 0)
        val_b = activities_b.get(key, 0)
        
        if key.endswith('_give'):
            receive_key = key.replace('_give', '_receive')
            receive_a = activities_a.get(receive_key, 0)
            receive_b = activities_b.get(receive_key, 0)
            
            # For same-pole pairs, both wanting same role is incompatible
            if val_a >= 0.5 or val_b >= 0.5:
                total_possible_interactions += 1
                
                # Only way it works: versatility (can do both roles)
                if (val_a >= 0.5 and receive_a >= 0.5) and (val_b >= 0.5 and receive_b < 0.5):
                    compatible_interactions += 0.3
                elif (val_a >= 0.5 and receive_a < 0.5) and (val_b >= 0.5 and receive_b >= 0.5):
                    compatible_interactions += 0.3
                elif (val_a >= 0.5 and receive_a >= 0.5) and (val_b >= 0.5 and receive_b >= 0.5):
                    compatible_interactions += 0.5
        
        elif not key.endswith('_receive') and not key.endswith('_watching'):
            # Non-directional activities
            if val_a >= 0.5 and val_b >= 0.5:
                compatible_interactions += 1.0 # v0.5 uses 1.0 for non-directional in same-pole
            if val_a >= 0.5 or val_b >= 0.5:
                total_possible_interactions += 1
    
    if total_possible_interactions == 0:
        return 0
    
    return compatible_interactions / total_possible_interactions


def calculate_activity_overlap(
    activities_a: Dict[str, Any],
    activities_b: Dict[str, Any],
    power_a: Dict[str, Any],
    power_b: Dict[str, Any]
) -> float:
    """
    Calculate activity overlap (0-1) by averaging category scores.
    """
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')
    
    is_top_bottom = (orientation_a == 'Top' and orientation_b == 'Bottom') or \
                    (orientation_a == 'Bottom' and orientation_b == 'Top')
    
    is_same_pole = (orientation_a == 'Top' and orientation_b == 'Top') or \
                   (orientation_a == 'Bottom' and orientation_b == 'Bottom')
    
    categories = list(activities_a.keys())
    scores = []
    
    for category in categories:
        cat_a = activities_a.get(category, {})
        cat_b = activities_b.get(category, {})
        
        # Ensure we have dicts (in case of flat structure mixed in, though we expect categorized)
        if not isinstance(cat_a, dict): cat_a = {}
        if not isinstance(cat_b, dict): cat_b = {}
        
        score = 0.0
        
        has_directional = category in [
            'physical_touch', 'oral', 'anal', 'power_exchange', 'display_performance', 'verbal_roleplay'
        ]
        
        if is_top_bottom and has_directional:
            if orientation_a == 'Top':
                score = calculate_asymmetric_directional_jaccard(cat_a, cat_b)
            else:
                score = calculate_asymmetric_directional_jaccard(cat_b, cat_a)
        elif is_same_pole and has_directional:
            score = calculate_same_pole_jaccard(cat_a, cat_b)
        else:
            # Standard Jaccard
            keys = set(list(cat_a.keys()) + list(cat_b.keys()))
            mutual = 0
            potential = 0
            for k in keys:
                va = cat_a.get(k, 0)
                vb = cat_b.get(k, 0)
                if va >= 0.5 and vb >= 0.5: mutual += 1
                if va >= 0.5 or vb >= 0.5: potential += 1
            
            score = mutual / potential if potential > 0 else 0.5
            
        scores.append(score)
    
    return sum(scores) / len(scores) if scores else 0.5


def calculate_truth_overlap(
    truth_topics_a: Dict[str, float],
    truth_topics_b: Dict[str, float]
) -> float:
    """
    Calculate truth topic overlap (0-1).
    
    Both players comfortable with same topics = better.
    """
    topics = ['past_experiences', 'fantasies', 'turn_ons', 'turn_offs',
              'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired']
    
    overlaps = []
    
    for topic in topics:
        score_a = truth_topics_a.get(topic, 0.0)
        score_b = truth_topics_b.get(topic, 0.0)
        
        # Both high = good
        if score_a >= 0.5 and score_b >= 0.5:
            overlaps.append(min(score_a, score_b))
        # Both low = neutral (0.5)
        elif score_a < 0.5 and score_b < 0.5:
            overlaps.append(0.5)
        # Mismatch = lower
        else:
            overlaps.append(0.3)
    
    return sum(overlaps) / len(overlaps) if overlaps else 0.5



# Map hard limit IDs to activity substrings/keys
# Based on official boundary-to-activity mapping documentation
HARD_LIMIT_MAP = {
    # 1. Impact Play
    'hardBoundaryImpact': ['spanking', 'slapping', 'biting'],
    'impact_play': ['spanking', 'slapping', 'biting'],
    
    # 2. Bondage/Restraints
    'hardBoundaryRestrain': ['restraints', 'blindfold'],
    'restraints_bondage': ['restraints', 'blindfold'],
    
    # 3. Breath Play
    'hardBoundaryBreath': ['choking'],
    'breath_play': ['choking'],
    
    # 4. Degradation/Humiliation
    'hardBoundaryDegrade': ['degradation', 'humiliation'],
    'degradation_humiliation': ['degradation', 'humiliation'],
    
    # 5. Public Play
    'hardBoundaryPublic': ['exhibitionism', 'voyeurism', 'public_play'],
    'public_activities': ['exhibitionism', 'voyeurism', 'public_play'],
    
    # 6. Recording
    'hardBoundaryRecord': ['recording', 'photos', 'videos'],
    'recording': ['recording', 'photos', 'videos'],
    
    # 7. Anal Activities
    'hardBoundaryAnal': ['anal', 'rimming'],
    'anal_activities': ['anal', 'rimming'],
    
    # 8. Watersports/Scat
    'hardBoundaryWatersports': ['watersports', 'scat'],
    'watersports': ['watersports', 'scat'],
}

def check_boundary_conflicts(
    player_a: Dict[str, Any],
    player_b: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Check for boundary conflicts between players.
    
    Returns list of conflict dicts.
    """
    conflicts = []
    
    activities_a = player_a.get('activities', {})
    activities_b = player_b.get('activities', {})
    boundaries_a = player_a.get('boundaries', {})
    boundaries_b = player_b.get('boundaries', {})
    
    hard_limits_a = set(boundaries_a.get('hard_limits', []))
    hard_limits_b = set(boundaries_b.get('hard_limits', []))
    
    def check_conflicts(activities, hard_limits, player_name_wants, player_name_limits):
        local_conflicts = []
        for limit_id in hard_limits:
            restricted_keys = HARD_LIMIT_MAP.get(limit_id, [])
            if not restricted_keys:
                continue
            
            conflicting_activities = []
            for act_key, score in activities.items():
                if score >= 0.7:
                    # Check if activity matches any restricted key substring
                    for restricted in restricted_keys:
                        if restricted in act_key:
                            conflicting_activities.append(act_key)
                            break
            
            if conflicting_activities:
                activities_str = ", ".join(conflicting_activities)
                local_conflicts.append({
                    'type': 'hard_limit_conflict',
                    'activity': activities_str,
                    'limit_id': limit_id,
                    'description': f'{player_name_wants} wants {activities_str}, but {player_name_limits} has hard limit: {limit_id}'
                })
                
        return local_conflicts

    # Check A wants vs B limits
    conflicts.extend(check_conflicts(activities_a, hard_limits_b, "Player A", "Player B"))
    
    # Check B wants vs A limits
    conflicts.extend(check_conflicts(activities_b, hard_limits_a, "Player B", "Player A"))
    
    return conflicts


def identify_mutual_activities(
    activities_a: Dict[str, float],
    activities_b: Dict[str, float]
) -> List[str]:
    """Identify activities both players want (both >= 0.7)."""
    mutual = []
    
    for activity in activities_a:
        if activity in activities_b:
            if activities_a[activity] >= 0.7 and activities_b[activity] >= 0.7:
                mutual.append(activity)
    
    return sorted(mutual)


def identify_growth_opportunities(
    activities_a: Dict[str, float],
    activities_b: Dict[str, float]
) -> List[str]:
    """Identify activities one wants and other is open to (one >= 0.7, other 0.3-0.7)."""
    opportunities = []
    
    for activity in activities_a:
        if activity in activities_b:
            score_a = activities_a[activity]
            score_b = activities_b[activity]
            
            if (score_a >= 0.7 and 0.3 <= score_b < 0.7) or \
               (score_b >= 0.7 and 0.3 <= score_a < 0.7):
                opportunities.append(activity)
    
    return sorted(opportunities)


def interpret_compatibility(score: int) -> str:
    """Interpret compatibility percentage."""
    if score >= 85:
        return 'Exceptional compatibility'
    elif score >= 70:
        return 'High compatibility'
    elif score >= 55:
        return 'Moderate compatibility'
    elif score >= 40:
        return 'Lower compatibility'
    else:
        return 'Challenging compatibility'


def flatten_activities(activities: Dict[str, Any]) -> Dict[str, float]:
    """
    Flatten nested activities dictionary into a single level.
    """
    flat = {}
    for key, value in activities.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                flat[subkey] = subvalue
        else:
            flat[key] = value
    return flat


def calculate_compatibility(
    player_a: Dict[str, Any],
    player_b: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate complete compatibility between two players.

    Args:
        player_a: Player A's complete profile
        player_b: Player B's complete profile
        weights: Optional custom weights (default: power=0.15, domain=0.25, activity=0.40, truth=0.15, se=0.03, sisc=0.02)

    Returns:
        Complete compatibility result dict
    """
    if weights is None:
        # Updated weights: Truth reduced from 0.20 to 0.15, added SE (0.03) and SIS-C (0.02)
        weights = {
            'power': 0.15,
            'domain': 0.25,
            'activity': 0.40,
            'truth': 0.15,  # Reduced from 0.20
            'se': 0.03,     # NEW: SE capacity (added as modifier)
            'sisc': 0.02,   # NEW: SIS-C alignment (added as modifier)
        }
    
    # Extract components
    power_a = player_a.get('power_dynamic', {})
    power_b = player_b.get('power_dynamic', {})
    domains_a = player_a.get('domain_scores', {})
    domains_b = player_b.get('domain_scores', {})
    arousal_a = player_a.get('arousal_propensity', {})
    arousal_b = player_b.get('arousal_propensity', {})
    
    # Use categorized activities directly for overlap calculation
    activities_a = player_a.get('activities', {})
    activities_b = player_b.get('activities', {})
    
    truth_topics_a = player_a.get('truth_topics', {})
    truth_topics_b = player_b.get('truth_topics', {})
    boundaries_a = player_a.get('boundaries', {})
    boundaries_b = player_b.get('boundaries', {})
    
    # Calculate components
    power_complement = calculate_power_complement(power_a, power_b)
    domain_similarity = calculate_domain_similarity(domains_a, domains_b, power_a, power_b)
    activity_overlap = calculate_activity_overlap(activities_a, activities_b, power_a, power_b)
    truth_overlap = calculate_truth_overlap(truth_topics_a, truth_topics_b)

    # Calculate arousal modifiers (NEW)
    se_a = arousal_a.get('sexual_excitation', 0.5)
    se_b = arousal_b.get('sexual_excitation', 0.5)
    sisc_a = arousal_a.get('inhibition_consequence', 0.5)
    sisc_b = arousal_b.get('inhibition_consequence', 0.5)

    se_modifier = calculate_se_modifier(se_a, se_b)
    sisc_modifier = calculate_sisc_modifier(sisc_a, sisc_b)
    
    # Detect same-pole pairs for truth multiplier
    is_same_pole = (power_a.get('orientation') == 'Top' and power_b.get('orientation') == 'Top') or \
                   (power_a.get('orientation') == 'Bottom' and power_b.get('orientation') == 'Bottom')
    
    adjusted_truth_overlap = truth_overlap * 0.5 if is_same_pole else truth_overlap
    
    # Boundary conflicts (need flat activities for this check)
    flat_a = flatten_activities(activities_a)
    flat_b = flatten_activities(activities_b)
    player_a_proxy = {'activities': flat_a, 'boundaries': boundaries_a}
    player_b_proxy = {'activities': flat_b, 'boundaries': boundaries_b}
    boundary_conflicts = check_boundary_conflicts(player_a_proxy, player_b_proxy)
    
    # Calculate weighted overall score (UPDATED to include arousal)
    overall_score = (
        weights['power'] * power_complement +
        weights['domain'] * domain_similarity +
        weights['activity'] * activity_overlap +
        weights['truth'] * adjusted_truth_overlap +
        se_modifier +      # SE is additive (0.0 to 0.03)
        sisc_modifier      # SIS-C is additive (-0.02 to 0.02)
    )
    
    # Apply boundary penalty
    boundary_penalty = len(boundary_conflicts) * 0.20
    overall_score = max(0, overall_score - boundary_penalty)

    # Cap at 1.0 (100%)
    overall_score = min(1.0, overall_score)

    # Convert to percentage
    overall_percentage = round(overall_score * 100)
    
    # Identify mutual interests (using flat activities)
    mutual_activities = identify_mutual_activities(flat_a, flat_b)
    growth_opportunities = identify_growth_opportunities(flat_a, flat_b)
    
    # Mutual truth topics
    mutual_truth_topics = []
    topic_keys = ['past_experiences', 'fantasies', 'turn_ons', 'turn_offs',
                  'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired']
    for key in topic_keys:
        if truth_topics_a.get(key, 0) >= 0.5 and truth_topics_b.get(key, 0) >= 0.5:
            mutual_truth_topics.append(key)
    
    # Blocked activities
    all_hard_limits = list(set(
        boundaries_a.get('hard_limits', []) +
        boundaries_b.get('hard_limits', [])
    ))
    
    return {
        'compatibility_version': '0.6',  # Version bump for arousal integration
        'overall_compatibility': {
            'score': overall_percentage,
            'interpretation': interpret_compatibility(overall_percentage)
        },
        'breakdown': {
            'power_complement': round(power_complement * 100),
            'domain_similarity': round(domain_similarity * 100),
            'activity_overlap': round(activity_overlap * 100),
            'truth_overlap': round(adjusted_truth_overlap * 100),
            'se_modifier': round(se_modifier * 100),       # NEW
            'sisc_modifier': round(sisc_modifier * 100),   # NEW
        },
        'arousal_alignment': {  # NEW section
            'se_a': round(se_a, 2),
            'se_b': round(se_b, 2),
            'sisc_a': round(sisc_a, 2),
            'sisc_b': round(sisc_b, 2),
            'se_modifier': round(se_modifier * 100),
            'sisc_modifier': round(sisc_modifier * 100),
        },
        'mutual_activities': mutual_activities,
        'growth_opportunities': growth_opportunities,
        'mutual_truth_topics': mutual_truth_topics,
        'blocked_activities': {
            'reason': 'hard_boundaries',
            'activities': all_hard_limits
        },
        'boundary_conflicts': boundary_conflicts
    }

