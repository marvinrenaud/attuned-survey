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
    
    For complementary power dynamics (Top/Bottom), some domains use complementary logic.
    """
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')
    
    is_complementary = (orientation_a == 'Top' and orientation_b == 'Bottom') or \
                      (orientation_a == 'Bottom' and orientation_b == 'Top')
    
    # Domains that use complementary logic for Top/Bottom pairs
    complementary_domains = ['dominance', 'submission', 'service']
    
    similarities = []
    
    for domain in domains_a:
        if domain not in domains_b:
            continue
        
        score_a = domains_a[domain]
        score_b = domains_b[domain]
        
        if is_complementary and domain in complementary_domains:
            # Complementary: high + low = good
            similarity = 1.0 - abs(score_a - (1.0 - score_b))
        else:
            # Normal: similar = good
            similarity = 1.0 - abs(score_a - score_b)
        
        similarities.append(similarity)
    
    return sum(similarities) / len(similarities) if similarities else 0.5


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
    - Special cases like watching_strip with stripping_self
    
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
        
        # Handle _self/_watching pairs
        elif key.endswith('_self'):
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
        
        # Non-directional activities (don't end with _receive, _watching, or already processed)
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
                # A versatile (give AND receive), B not → Minimal credit
                if (val_a >= 0.5 and receive_a >= 0.5) and (val_b >= 0.5 and receive_b < 0.5):
                    compatible_interactions += 0.1
                # B versatile, A not → Minimal credit
                elif (val_a >= 0.5 and receive_a < 0.5) and (val_b >= 0.5 and receive_b >= 0.5):
                    compatible_interactions += 0.1
                # Both versatile → Slight credit
                elif (val_a >= 0.5 and receive_a >= 0.5) and (val_b >= 0.5 and receive_b >= 0.5):
                    compatible_interactions += 0.2
                # Else: Both want same role, no versatility = 0 (incompatible)
        
        elif not key.endswith('_receive'):
            # Non-directional activities get REDUCED credit for same-pole pairs
            # Power incompatibility affects everything
            if val_a >= 0.5 and val_b >= 0.5:
                compatible_interactions += 0.3  # Reduced from 1.0
            if val_a >= 0.5 or val_b >= 0.5:
                total_possible_interactions += 1
    
    if total_possible_interactions == 0:
        return 0
    
    return compatible_interactions / total_possible_interactions


def calculate_activity_overlap(
    activities_a: Dict[str, float],
    activities_b: Dict[str, float],
    power_a: Dict[str, Any],
    power_b: Dict[str, Any]
) -> float:
    """
    Calculate activity overlap (0-1).
    
    Uses asymmetric matching for Top/Bottom pairs.
    Uses same-pole Jaccard for Top/Top or Bottom/Bottom pairs.
    Uses standard Jaccard for Switch pairs or mixed combinations.
    """
    orientation_a = power_a.get('orientation', 'Switch')
    orientation_b = power_b.get('orientation', 'Switch')
    
    is_top_bottom = (orientation_a == 'Top' and orientation_b == 'Bottom') or \
                    (orientation_a == 'Bottom' and orientation_b == 'Top')
    
    is_same_pole = (orientation_a == 'Top' and orientation_b == 'Top') or \
                   (orientation_a == 'Bottom' and orientation_b == 'Bottom')
    
    # For Top/Bottom pairs, use asymmetric directional Jaccard
    if is_top_bottom:
        # Determine who is Top and who is Bottom
        if orientation_a == 'Top':
            return calculate_asymmetric_directional_jaccard(activities_a, activities_b)
        else:
            return calculate_asymmetric_directional_jaccard(activities_b, activities_a)
    
    # For same-pole pairs, use same-pole Jaccard
    if is_same_pole:
        return calculate_same_pole_jaccard(activities_a, activities_b)
    
    # For Switch pairs or mixed, use standard Jaccard
    all_activities = set(list(activities_a.keys()) + list(activities_b.keys()))
    
    mutual_yes = 0
    at_least_one_yes = 0
    
    for activity in all_activities:
        score_a = activities_a.get(activity, 0.0)
        score_b = activities_b.get(activity, 0.0)
        
        # Both interested (>= 0.5)
        if score_a >= 0.5 and score_b >= 0.5:
            mutual_yes += 1
        
        # At least one interested
        if score_a >= 0.5 or score_b >= 0.5:
            at_least_one_yes += 1
    
    if at_least_one_yes == 0:
        return 0.5
    
    return mutual_yes / at_least_one_yes


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
    
    # Check if one player's Yes conflicts with other's hard limit
    for activity, score_a in activities_a.items():
        if score_a >= 0.7:  # Player A wants this
            if activity in hard_limits_b:  # Player B hard limit
                conflicts.append({
                    'type': 'hard_limit_conflict',
                    'activity': activity,
                    'description': f'Player A wants {activity}, but it\'s Player B\'s hard limit'
                })
    
    for activity, score_b in activities_b.items():
        if score_b >= 0.7:  # Player B wants this
            if activity in hard_limits_a:  # Player A hard limit
                conflicts.append({
                    'type': 'hard_limit_conflict',
                    'activity': activity,
                    'description': f'Player B wants {activity}, but it\'s Player A\'s hard limit'
                })
    
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
        weights: Optional custom weights (default: power=0.20, domain=0.25, activity=0.45, truth=0.10)
    
    Returns:
        Complete compatibility result dict
    """
    if weights is None:
        weights = {'power': 0.20, 'domain': 0.25, 'activity': 0.45, 'truth': 0.10}
    
    # Extract components
    power_a = player_a.get('power_dynamic', {})
    power_b = player_b.get('power_dynamic', {})
    domains_a = player_a.get('domain_scores', {})
    domains_b = player_b.get('domain_scores', {})
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
    
    # Detect same-pole pairs for truth multiplier
    is_same_pole = (power_a.get('orientation') == 'Top' and power_b.get('orientation') == 'Top') or \
                   (power_a.get('orientation') == 'Bottom' and power_b.get('orientation') == 'Bottom')
    
    adjusted_truth_overlap = truth_overlap * 0.5 if is_same_pole else truth_overlap
    
    # Boundary conflicts
    player_a_proxy = {'activities': activities_a, 'boundaries': boundaries_a}
    player_b_proxy = {'activities': activities_b, 'boundaries': boundaries_b}
    boundary_conflicts = check_boundary_conflicts(player_a_proxy, player_b_proxy)
    
    # Calculate weighted overall score
    overall_score = (
        weights['power'] * power_complement +
        weights['domain'] * domain_similarity +
        weights['activity'] * activity_overlap +
        weights['truth'] * adjusted_truth_overlap
    )
    
    # Apply boundary penalty
    boundary_penalty = len(boundary_conflicts) * 0.20
    overall_score = max(0, overall_score - boundary_penalty)
    
    # Convert to percentage
    overall_percentage = round(overall_score * 100)
    
    # Identify mutual interests
    mutual_activities = identify_mutual_activities(activities_a, activities_b)
    growth_opportunities = identify_growth_opportunities(activities_a, activities_b)
    
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
        'compatibility_version': '0.5',
        'overall_compatibility': {
            'score': overall_percentage,
            'interpretation': interpret_compatibility(overall_percentage)
        },
        'breakdown': {
            'power_complement': round(power_complement * 100),
            'domain_similarity': round(domain_similarity * 100),
            'activity_overlap': round(activity_overlap * 100),
            'truth_overlap': round(adjusted_truth_overlap * 100),
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

