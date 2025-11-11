/**
 * Category Map (v0.4)
 * Maps question IDs to activity categories
 */

// Map v0.4 question IDs to categories
export const CATEGORY_MAP = {
  // Physical Touch: B1-B10
  'B1a': 'physical_touch',
  'B1b': 'physical_touch',
  'B2a': 'physical_touch',
  'B2b': 'physical_touch',
  'B3a': 'physical_touch',
  'B3b': 'physical_touch',
  'B4a': 'physical_touch',
  'B4b': 'physical_touch',
  'B5a': 'physical_touch',
  'B5b': 'physical_touch',
  'B6a': 'physical_touch',
  'B6b': 'physical_touch',
  'B7a': 'physical_touch',
  'B7b': 'physical_touch',
  'B8a': 'physical_touch',
  'B8b': 'physical_touch',
  'B9a': 'physical_touch',
  'B9b': 'physical_touch',
  'B10a': 'physical_touch',
  'B10b': 'physical_touch',

  // Oral: B11-B12
  'B11a': 'oral',
  'B11b': 'oral',
  'B12a': 'oral',
  'B12b': 'oral',

  // Anal: B13-B14
  'B13a': 'anal',
  'B13b': 'anal',
  'B14a': 'anal',
  'B14b': 'anal',

  // Power Exchange: B15-B18
  'B15a': 'power_exchange',
  'B15b': 'power_exchange',
  'B16a': 'power_exchange',
  'B16b': 'power_exchange',
  'B17a': 'power_exchange',
  'B17b': 'power_exchange',
  'B18a': 'power_exchange',
  'B18b': 'power_exchange',

  // Verbal & Roleplay: B19-B23
  'B19': 'verbal_roleplay',
  'B20': 'verbal_roleplay',
  'B21': 'verbal_roleplay',
  'B22': 'verbal_roleplay',
  'B23': 'verbal_roleplay',

  // Display & Performance: B24-B28
  'B24a': 'display_performance',
  'B24b': 'display_performance',
  'B25a': 'display_performance',
  'B25b': 'display_performance',
  'B26': 'display_performance',
  'B27': 'display_performance',
  'B28': 'display_performance',

  // Truth Topics: B29-B36
  'B29': 'truth_topics',
  'B30': 'truth_topics',
  'B31': 'truth_topics',
  'B32': 'truth_topics',
  'B33': 'truth_topics',
  'B34': 'truth_topics',
  'B35': 'truth_topics',
  'B36': 'truth_topics'
};

/**
 * Get category for a question ID
 * @param {string} questionId - Question ID
 * @returns {string|null} - Category name or null
 */
export function getCategory(questionId) {
  return CATEGORY_MAP[questionId] || null;
}

/**
 * Get all question IDs for a category
 * @param {string} category - Category name
 * @returns {string[]} - Array of question IDs
 */
export function getQuestionsByCategory(category) {
  return Object.entries(CATEGORY_MAP)
    .filter(([_, cat]) => cat === category)
    .map(([qid, _]) => qid);
}

/**
 * Get all categories
 * @returns {string[]} - Array of unique category names
 */
export function getAllCategories() {
  return Array.from(new Set(Object.values(CATEGORY_MAP)));
}

/**
 * Map activity key to human-readable name
 * @param {string} activityKey - Activity key (e.g., 'massage_receive')
 * @returns {string} - Human-readable name
 */
export function getActivityName(activityKey) {
  const nameMap = {
    // Physical touch
    'massage_receive': 'Massage (receiving)',
    'massage_give': 'Massage (giving)',
    'hair_pull_gentle_receive': 'Hair pulling - gentle (receiving)',
    'hair_pull_gentle_give': 'Hair pulling - gentle (giving)',
    'biting_moderate_receive': 'Biting/scratching - moderate (receiving)',
    'biting_moderate_give': 'Biting/scratching - moderate (giving)',
    'spanking_moderate_receive': 'Spanking - moderate (receiving)',
    'spanking_moderate_give': 'Spanking - moderate (giving)',
    'hands_genitals_receive': 'Hands on genitals (receiving)',
    'hands_genitals_give': 'Hands on genitals (giving)',
    'spanking_hard_receive': 'Spanking - hard (receiving)',
    'spanking_hard_give': 'Spanking - hard (giving)',
    'slapping_receive': 'Slapping (receiving)',
    'slapping_give': 'Slapping (giving)',
    'choking_receive': 'Choking/breath play (receiving)',
    'choking_give': 'Choking/breath play (giving)',
    'spitting_receive': 'Spitting (receiving)',
    'spitting_give': 'Spitting (giving)',
    'watersports_receive': 'Watersports (receiving)',
    'watersports_give': 'Watersports (giving)',

    // Oral
    'oral_sex_receive': 'Oral sex on genitals (receiving)',
    'oral_sex_give': 'Oral sex on genitals (giving)',
    'oral_body_receive': 'Oral on body parts (receiving)',
    'oral_body_give': 'Oral on body parts (giving)',

    // Anal
    'anal_fingers_toys_receive': 'Anal stimulation (receiving)',
    'anal_fingers_toys_give': 'Anal stimulation (giving)',
    'rimming_receive': 'Rimming (receiving)',
    'rimming_give': 'Rimming (giving)',

    // Power exchange
    'restraints_receive': 'Restraints (receiving)',
    'restraints_give': 'Restraints (giving)',
    'blindfold_receive': 'Blindfold/sensory deprivation (receiving)',
    'blindfold_give': 'Blindfold/sensory deprivation (giving)',
    'orgasm_control_receive': 'Orgasm control (receiving)',
    'orgasm_control_give': 'Orgasm control (giving)',
    'protocols_receive': 'Following protocols/commands',
    'protocols_give': 'Giving protocols/commands',

    // Verbal & roleplay
    'dirty_talk': 'Dirty talk',
    'moaning': 'Moaning/vocal encouragement',
    'roleplay': 'Roleplay scenarios',
    'commands_receive': 'Receiving commands',
    'commands_give': 'Giving commands',
    'begging_receive': 'Begging/pleading',
    'begging_give': 'Hearing partner beg',

    // Display & performance
    'stripping_self': 'Stripping (performing)',
    'watching_strip': 'Watching partner strip',
    'solo_pleasure_self': 'Being watched (solo)',
    'watching_solo_pleasure': 'Watching partner (solo)',
    'posing_self': 'Posing for viewing',
    'posing_watching': 'Watching partner pose',
    'dancing_self': 'Sensual dancing',
    'dancing_watching': 'Watching partner dance',
    'revealing_clothing_self': 'Wearing revealing clothing',
    'revealing_clothing_watching': 'Viewing partner in revealing clothing'
  };

  return nameMap[activityKey] || activityKey;
}

/**
 * Map category to human-readable name
 * @param {string} category - Category key
 * @returns {string} - Human-readable name
 */
export function getCategoryName(category) {
  const nameMap = {
    'physical_touch': 'Physical Touch & Sensation',
    'oral': 'Oral Activities',
    'anal': 'Anal Activities',
    'power_exchange': 'Power Exchange & Control',
    'verbal_roleplay': 'Verbal & Roleplay',
    'display_performance': 'Display & Performance',
    'truth_topics': 'Truth Topics'
  };

  return nameMap[category] || category;
}
