/**
 * Activity Tags Generator (v0.4)
 * Generates boolean tags for activity filtering and gating
 */

/**
 * Check if user has interest (Y or M = >= 0.5)
 * @param {number} value - Activity value (0, 0.5, or 1.0)
 * @returns {boolean}
 */
function hasInterest(value) {
  return value >= 0.5;
}

/**
 * Generate activity tags for AI engine gating
 * @param {Object} activities - Activity map from activityConverter
 * @param {Object} boundaries - Boundaries object
 * @returns {Object} - Boolean tags
 */
export function generateActivityTags(activities, boundaries) {
  const tags = {};

  // Gentle activities: massage, light touch
  tags.open_to_gentle = 
    hasInterest(activities.physical_touch?.massage_receive) ||
    hasInterest(activities.physical_touch?.massage_give) ||
    hasInterest(activities.physical_touch?.hair_pull_gentle_receive) ||
    hasInterest(activities.physical_touch?.hair_pull_gentle_give);

  // Moderate activities: biting, moderate spanking, hands on genitals
  tags.open_to_moderate = 
    hasInterest(activities.physical_touch?.biting_moderate_receive) ||
    hasInterest(activities.physical_touch?.biting_moderate_give) ||
    hasInterest(activities.physical_touch?.spanking_moderate_receive) ||
    hasInterest(activities.physical_touch?.spanking_moderate_give) ||
    hasInterest(activities.physical_touch?.hands_genitals_receive) ||
    hasInterest(activities.physical_touch?.hands_genitals_give);

  // Intense activities: hard spanking, slapping, choking, watersports
  tags.open_to_intense = 
    hasInterest(activities.physical_touch?.spanking_hard_receive) ||
    hasInterest(activities.physical_touch?.spanking_hard_give) ||
    hasInterest(activities.physical_touch?.slapping_receive) ||
    hasInterest(activities.physical_touch?.slapping_give) ||
    hasInterest(activities.physical_touch?.choking_receive) ||
    hasInterest(activities.physical_touch?.choking_give) ||
    hasInterest(activities.physical_touch?.spitting_receive) ||
    hasInterest(activities.physical_touch?.spitting_give) ||
    hasInterest(activities.physical_touch?.watersports_receive) ||
    hasInterest(activities.physical_touch?.watersports_give);

  // Oral activities
  tags.open_to_oral = 
    hasInterest(activities.oral?.oral_sex_receive) ||
    hasInterest(activities.oral?.oral_sex_give) ||
    hasInterest(activities.oral?.oral_body_receive) ||
    hasInterest(activities.oral?.oral_body_give);

  // Anal activities
  tags.open_to_anal = 
    hasInterest(activities.anal?.anal_fingers_toys_receive) ||
    hasInterest(activities.anal?.anal_fingers_toys_give) ||
    hasInterest(activities.anal?.rimming_receive) ||
    hasInterest(activities.anal?.rimming_give);

  // Restraints/bondage
  tags.open_to_restraints = 
    hasInterest(activities.power_exchange?.restraints_receive) ||
    hasInterest(activities.power_exchange?.restraints_give) ||
    hasInterest(activities.power_exchange?.blindfold_receive) ||
    hasInterest(activities.power_exchange?.blindfold_give);

  // Orgasm control
  tags.open_to_orgasm_control = 
    hasInterest(activities.power_exchange?.orgasm_control_receive) ||
    hasInterest(activities.power_exchange?.orgasm_control_give);

  // Roleplay
  tags.open_to_roleplay = 
    hasInterest(activities.verbal_roleplay?.roleplay) ||
    hasInterest(activities.power_exchange?.protocols_receive) ||
    hasInterest(activities.power_exchange?.protocols_give);

  // Display/performance
  tags.open_to_display = 
    hasInterest(activities.display_performance?.stripping_self) ||
    hasInterest(activities.display_performance?.watching_strip) ||
    hasInterest(activities.display_performance?.solo_pleasure_self) ||
    hasInterest(activities.display_performance?.watching_solo_pleasure) ||
    hasInterest(activities.display_performance?.posing_self) ||
    hasInterest(activities.display_performance?.dancing_self);

  // Group/multi-partner activities
  // Gated by boundaries - if not explicitly blocked, assume open (or check specific activities)
  const hardLimits = boundaries?.hard_limits || [];
  tags.open_to_group = !hardLimits.includes('multi_partner');

  return tags;
}

/**
 * Get activity intensity level
 * @param {Object} activities - Activity map
 * @returns {string} - 'gentle', 'moderate', 'intense', or 'mixed'
 */
export function getIntensityLevel(activities) {
  const tags = generateActivityTags(activities, {});
  
  if (tags.open_to_intense) return 'intense';
  if (tags.open_to_moderate) return 'moderate';
  if (tags.open_to_gentle) return 'gentle';
  return 'exploring';
}

/**
 * Get summary of activity preferences
 * @param {Object} activities - Activity map
 * @returns {Object} - Summary statistics
 */
export function getActivitySummary(activities) {
  const tags = generateActivityTags(activities, {});
  
  return {
    intensity: getIntensityLevel(activities),
    tags,
    category_counts: {
      physical_touch: Object.values(activities.physical_touch || {}).filter(v => v >= 0.5).length,
      oral: Object.values(activities.oral || {}).filter(v => v >= 0.5).length,
      anal: Object.values(activities.anal || {}).filter(v => v >= 0.5).length,
      power_exchange: Object.values(activities.power_exchange || {}).filter(v => v >= 0.5).length,
      verbal_roleplay: Object.values(activities.verbal_roleplay || {}).filter(v => v >= 0.5).length,
      display_performance: Object.values(activities.display_performance || {}).filter(v => v >= 0.5).length
    }
  };
}

