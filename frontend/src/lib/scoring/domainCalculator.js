/**
 * Domain Calculator (v0.4)
 * Calculates 5 domain scores: Sensation, Connection, Power, Exploration, Verbal
 */

/**
 * Calculate mean of array
 * @param {number[]} values
 * @returns {number}
 */
function mean(values) {
  if (!values || values.length === 0) return 50; // Default neutral if no data
  const filtered = values.filter(v => v !== undefined && v !== null);
  if (filtered.length === 0) return 50;
  const sum = filtered.reduce((a, b) => a + b, 0);
  return sum / filtered.length;
}

/**
 * Convert 0-1 value to 0-100 percentage
 * @param {number} value
 * @returns {number}
 */
function toPercentage(value) {
  if (value === undefined || value === null) return 50;
  return Math.round(value * 100);
}

/**
 * Calculate domain scores from activities and truth topics
 * Based on v0.4 implementation guide
 * @param {Object} activities - Converted activities object
 * @param {Object} truthTopics - Converted truth topics object
 * @returns {Object} - Domain scores (0-100 for each)
 */
export function calculateDomainScores(activities, truthTopics) {
  // SENSATION: Physical intensity (moderate to extreme activities)
  const sensationItems = [
    activities.physical_touch?.biting_moderate_receive,
    activities.physical_touch?.biting_moderate_give,
    activities.physical_touch?.spanking_moderate_receive,
    activities.physical_touch?.spanking_moderate_give,
    activities.physical_touch?.spanking_hard_receive,
    activities.physical_touch?.spanking_hard_give,
    activities.physical_touch?.slapping_receive,
    activities.physical_touch?.slapping_give,
    activities.physical_touch?.choking_receive,
    activities.physical_touch?.choking_give,
    activities.physical_touch?.spitting_receive,
    activities.physical_touch?.spitting_give,
    activities.physical_touch?.watersports_receive,
    activities.physical_touch?.watersports_give
  ].filter(v => v !== undefined);
  
  const sensation = Math.round(mean(sensationItems) * 100);

  // CONNECTION: Emotional intimacy
  const connectionItems = [
    activities.physical_touch?.massage_receive,
    activities.physical_touch?.massage_give,
    activities.oral?.oral_body_receive,
    activities.oral?.oral_body_give,
    activities.verbal_roleplay?.moaning,
    activities.display_performance?.posing,
    activities.display_performance?.revealing_clothing,
    truthTopics?.fantasies,
    truthTopics?.insecurities,
    truthTopics?.future_fantasies,
    truthTopics?.feeling_desired
  ].filter(v => v !== undefined);
  
  const connection = Math.round(mean(connectionItems) * 100);

  // POWER: Control and structure
  const powerItems = [
    activities.power_exchange?.restraints_receive,
    activities.power_exchange?.restraints_give,
    activities.power_exchange?.blindfold_receive,
    activities.power_exchange?.blindfold_give,
    activities.power_exchange?.orgasm_control_receive,
    activities.power_exchange?.orgasm_control_give,
    activities.power_exchange?.protocols_follow,
    activities.power_exchange?.protocols_give,
    activities.verbal_roleplay?.commands,
    activities.verbal_roleplay?.begging
  ].filter(v => v !== undefined);
  
  const power = Math.round(mean(powerItems) * 100);

  // EXPLORATION: Novelty and risk
  const explorationItems = [
    activities.verbal_roleplay?.roleplay,
    activities.display_performance?.stripping_me,
    activities.display_performance?.watching_strip,
    activities.display_performance?.watched_solo_pleasure,
    activities.display_performance?.watching_solo_pleasure,
    activities.display_performance?.dancing,
    activities.physical_touch?.spitting_receive,
    activities.physical_touch?.spitting_give,
    activities.physical_touch?.watersports_receive,
    activities.physical_touch?.watersports_give
  ].filter(v => v !== undefined);
  
  const exploration = Math.round(mean(explorationItems) * 100);

  // VERBAL: Communication and expression
  const verbalItems = [
    activities.verbal_roleplay?.dirty_talk,
    activities.verbal_roleplay?.moaning,
    activities.verbal_roleplay?.roleplay,
    activities.verbal_roleplay?.commands,
    activities.verbal_roleplay?.begging
  ].filter(v => v !== undefined);
  
  const verbal = Math.round(mean(verbalItems) * 100);

  return {
    sensation,
    connection,
    power,
    exploration,
    verbal
  };
}

/**
 * Get domain descriptions
 * @param {Object} domains - Domain scores
 * @returns {Object} - Descriptions for each domain
 */
export function getDomainDescriptions(domains) {
  const { sensation, connection, power, exploration, verbal } = domains;
  
  const descriptions = {};

  // Sensation
  if (sensation >= 70) {
    descriptions.sensation = 'You have a strong preference for physical intensity and sensation play.';
  } else if (sensation >= 40) {
    descriptions.sensation = 'You enjoy moderate physical sensation and intensity.';
  } else {
    descriptions.sensation = 'You prefer gentler physical touch and intimacy.';
  }

  // Connection
  if (connection >= 70) {
    descriptions.connection = 'Emotional intimacy and deep connection are very important to you.';
  } else if (connection >= 40) {
    descriptions.connection = 'You appreciate emotional connection balanced with physical intimacy.';
  } else {
    descriptions.connection = 'You may focus more on physical aspects than emotional connection.';
  }

  // Power
  if (power >= 70) {
    descriptions.power = 'You strongly enjoy power dynamics and control in intimate activities.';
  } else if (power >= 40) {
    descriptions.power = 'You appreciate some structure and power exchange.';
  } else {
    descriptions.power = 'Power dynamics are not a major focus for you.';
  }

  // Exploration
  if (exploration >= 70) {
    descriptions.exploration = 'You love novelty, risk, and trying new experiences.';
  } else if (exploration >= 40) {
    descriptions.exploration = 'You are open to some new experiences while maintaining comfort zones.';
  } else {
    descriptions.exploration = 'You prefer familiar activities and gradual exploration.';
  }

  // Verbal
  if (verbal >= 70) {
    descriptions.verbal = 'Communication and verbal expression are central to your intimate experiences.';
  } else if (verbal >= 40) {
    descriptions.verbal = 'You enjoy some verbal communication during intimacy.';
  } else {
    descriptions.verbal = 'You may prefer less verbal communication, focusing on physical connection.';
  }

  return descriptions;
}

/**
 * Calculate domain similarity for compatibility
 * UPDATED: Power-aware logic that recognizes complementary differences for Top/Bottom pairs
 * @param {Object} domainsA - First person's domains
 * @param {Object} domainsB - Second person's domains
 * @param {Object} powerA - First person's power dynamic (optional for backward compatibility)
 * @param {Object} powerB - Second person's power dynamic (optional for backward compatibility)
 * @returns {number} - Similarity score 0-1
 */
export function calculateDomainSimilarity(domainsA, domainsB, powerA, powerB) {
  // Detect if this is a complementary Top/Bottom pair
  const isComplementaryPair = powerA && powerB && (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  );

  if (isComplementaryPair) {
    // For complementary pairs, use minimum threshold approach for exploration/verbal
    // An eager Bottom (95) + measured Top (60) is ideal, not a problem!
    
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
    
    // For exploration and verbal: as long as minimum is adequate (>50), don't penalize
    const minExploration = Math.min(domainsA.exploration, domainsB.exploration);
    const minVerbal = Math.min(domainsA.verbal, domainsB.verbal);
    
    // If minimum is 50+, score is 1.0 (no penalty)
    // If minimum is below 50, scale proportionally
    const explorationScore = minExploration >= 50 ? 1.0 : minExploration / 50;
    const verbalScore = minVerbal >= 50 ? 1.0 : minVerbal / 50;
    
    return (sensationDist + connectionDist + powerDist + explorationScore + verbalScore) / 5;
  } else {
    // For Switch/Switch or same-pole pairs, use standard distance
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
    const explorationDist = 1 - Math.abs(domainsA.exploration - domainsB.exploration) / 100;
    const verbalDist = 1 - Math.abs(domainsA.verbal - domainsB.verbal) / 100;
    
    return (sensationDist + connectionDist + powerDist + explorationDist + verbalDist) / 5;
  }
}

/**
 * LEGACY v0.3.1 - Compute domains from traits
 * Kept for backward compatibility with old profiles in Admin panel
 * @param {Object} traits - v0.3.1 trait scores
 * @returns {Object} - Domain scores for display
 */
export function computeDomainsFromTraits(traits = {}) {
  const toPercentage = (value) => {
    if (value === undefined || value === null || Number.isNaN(value)) return 50;
    const n = Number(value);
    const pct = n <= 1 ? n * 100 : n; // support 0..1 or 0..100 traits
    if (!Number.isFinite(pct)) return 50;
    return Math.max(0, Math.min(100, pct));
  };

  const mean = (values) => {
    if (!values || values.length === 0) return 50;
    const nums = values.map((v) => toPercentage(v));
    const sum = nums.reduce((a, b) => a + b, 0);
    return Math.max(0, Math.min(100, sum / nums.length));
  };

  const powerTop = toPercentage(traits.POWER_TOP);
  const powerBottom = toPercentage(traits.POWER_BOTTOM);
  const connection = mean([traits.ROMANTIC, traits.SENSUAL]);
  const sensory = Math.max(
    0,
    Math.min(
      100,
      0.4 * toPercentage(traits.IMPACT) +
        0.4 * toPercentage(traits.BONDAGE) +
        0.2 * toPercentage(traits.TOYS)
    )
  );
  const exploration = mean([
    traits.NOVELTY,
    traits.EXHIBITION,
    traits.VOYEUR,
    traits.PUBLIC_EDGE,
  ]);
  const structure = toPercentage(traits.ROLEPLAY);

  return {
    powerTop,
    powerBottom,
    connection,
    sensory,
    exploration,
    structure,
  };
}
