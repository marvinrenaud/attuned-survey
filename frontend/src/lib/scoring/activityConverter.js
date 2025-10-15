/**
 * Activity Converter (v0.4)
 * Converts Y/M/N responses to numeric values and organizes by category
 */

/**
 * Convert YMN response to numeric value
 * @param {string} response - 'Y', 'M', or 'N'
 * @returns {number} - 1.0, 0.5, or 0.0
 */
function convertYMN(response) {
  const r = (response || '').toString().trim().toUpperCase();
  if (r === 'Y' || r === 'YES') return 1.0;
  if (r === 'M' || r === 'MAYBE') return 0.5;
  return 0.0;
}

/**
 * Convert activity responses from raw answers to categorized numeric values
 * @param {Object} answers - Raw survey answers
 * @returns {Object} - Organized activity map by category
 */
export function convertActivities(answers) {
  const activities = {
    physical_touch: {},
    oral: {},
    anal: {},
    power_exchange: {},
    verbal_roleplay: {},
    display_performance: {}
  };

  // Physical Touch: B1-B10 (20 items - 10 pairs)
  const physicalTouchIds = [
    'massage_receive', 'massage_give',
    'hair_pull_gentle_receive', 'hair_pull_gentle_give',
    'biting_moderate_receive', 'biting_moderate_give',
    'spanking_moderate_receive', 'spanking_moderate_give',
    'hands_genitals_receive', 'hands_genitals_give',
    'spanking_hard_receive', 'spanking_hard_give',
    'slapping_receive', 'slapping_give',
    'choking_receive', 'choking_give',
    'spitting_receive', 'spitting_give',
    'watersports_receive', 'watersports_give'
  ];
  const physicalTouchQuestions = [
    'B1a', 'B1b', 'B2a', 'B2b', 'B3a', 'B3b', 'B4a', 'B4b', 'B5a', 'B5b',
    'B6a', 'B6b', 'B7a', 'B7b', 'B8a', 'B8b', 'B9a', 'B9b', 'B10a', 'B10b'
  ];
  physicalTouchQuestions.forEach((qid, idx) => {
    activities.physical_touch[physicalTouchIds[idx]] = convertYMN(answers[qid]);
  });

  // Oral: B11-B12 (4 items - 2 pairs)
  activities.oral.oral_sex_receive = convertYMN(answers['B11a']);
  activities.oral.oral_sex_give = convertYMN(answers['B11b']);
  activities.oral.oral_body_receive = convertYMN(answers['B12a']);
  activities.oral.oral_body_give = convertYMN(answers['B12b']);

  // Anal: B13-B14 (4 items - 2 pairs)
  activities.anal.anal_fingers_toys_receive = convertYMN(answers['B13a']);
  activities.anal.anal_fingers_toys_give = convertYMN(answers['B13b']);
  activities.anal.rimming_receive = convertYMN(answers['B14a']);
  activities.anal.rimming_give = convertYMN(answers['B14b']);

  // Power Exchange: B15-B18 (8 items - 4 pairs)
  activities.power_exchange.restraints_receive = convertYMN(answers['B15a']);
  activities.power_exchange.restraints_give = convertYMN(answers['B15b']);
  activities.power_exchange.blindfold_receive = convertYMN(answers['B16a']);
  activities.power_exchange.blindfold_give = convertYMN(answers['B16b']);
  activities.power_exchange.orgasm_control_receive = convertYMN(answers['B17a']);
  activities.power_exchange.orgasm_control_give = convertYMN(answers['B17b']);
  activities.power_exchange.protocols_follow = convertYMN(answers['B18a']);
  activities.power_exchange.protocols_give = convertYMN(answers['B18b']);

  // Verbal & Roleplay: B19-B23 (5 items - non-directional)
  activities.verbal_roleplay.dirty_talk = convertYMN(answers['B19']);
  activities.verbal_roleplay.moaning = convertYMN(answers['B20']);
  activities.verbal_roleplay.roleplay = convertYMN(answers['B21']);
  activities.verbal_roleplay.commands = convertYMN(answers['B22']);
  activities.verbal_roleplay.begging = convertYMN(answers['B23']);

  // Display & Performance: B24-B28 (7 items - partially directional)
  activities.display_performance.stripping_me = convertYMN(answers['B24a']);
  activities.display_performance.watching_strip = convertYMN(answers['B24b']);
  activities.display_performance.watched_solo_pleasure = convertYMN(answers['B25a']);
  activities.display_performance.watching_solo_pleasure = convertYMN(answers['B25b']);
  activities.display_performance.posing = convertYMN(answers['B26']);
  activities.display_performance.dancing = convertYMN(answers['B27']);
  activities.display_performance.revealing_clothing = convertYMN(answers['B28']);

  return activities;
}

/**
 * Get all activity values as a flat array (for statistics)
 * @param {Object} activities - Activity map from convertActivities
 * @returns {number[]} - Array of all activity values
 */
export function getActivityValues(activities) {
  const values = [];
  for (const category of Object.values(activities)) {
    for (const value of Object.values(category)) {
      values.push(value);
    }
  }
  return values;
}

/**
 * Count activities by response type
 * @param {Object} activities - Activity map from convertActivities
 * @returns {Object} - Counts of Yes/Maybe/No responses
 */
export function countActivityResponses(activities) {
  const values = getActivityValues(activities);
  return {
    yes: values.filter(v => v === 1.0).length,
    maybe: values.filter(v => v === 0.5).length,
    no: values.filter(v => v === 0.0).length,
    total: values.length
  };
}

