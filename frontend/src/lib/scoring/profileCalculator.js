/**
 * Profile Calculator (v0.4)
 * Main orchestrator for complete intimacy profile calculation
 */

import { calculateArousalPropensity } from './arousalCalculator.js';
import { calculatePowerDynamic } from './powerCalculator.js';
import { convertActivities } from './activityConverter.js';
import { convertTruthTopics } from './truthTopicsCalculator.js';
import { calculateDomainScores } from './domainCalculator.js';
import { generateActivityTags } from './activityTags.js';

/**
 * Extract boundaries from answers
 * @param {Object} answers - Raw survey answers
 * @returns {Object} - Boundaries object
 */
function extractBoundaries(answers) {
  // C1: Hard boundaries (checklist - could be array or comma-separated string)
  let hardLimits = [];
  const c1 = answers['C1'];
  
  if (Array.isArray(c1)) {
    hardLimits = c1;
  } else if (typeof c1 === 'string' && c1.trim() !== '') {
    hardLimits = c1.split(',').map(s => s.trim()).filter(Boolean);
  }

  // C2: Additional notes (free text)
  const additionalNotes = (answers['C2'] || '').toString().trim();

  return {
    hard_limits: hardLimits,
    additional_notes: additionalNotes
  };
}

/**
 * Calculate complete intimacy profile from survey responses
 * @param {string} userId - User identifier
 * @param {Object} answers - Raw survey answers
 * @returns {Object} - Complete IntimacyProfile
 */
export function calculateProfile(userId, answers) {
  // 1. Arousal Propensity (A1-A12)
  const arousalPropensity = calculateArousalPropensity(answers);

  // 2. Power Dynamic (A13-A16)
  const powerDynamic = calculatePowerDynamic(answers);

  // 3. Convert Activities (B1-B28)
  const activities = convertActivities(answers);

  // 4. Convert Truth Topics (B29-B36)
  const truthTopics = convertTruthTopics(answers);

  // 5. Calculate Domain Scores
  const domainScores = calculateDomainScores(activities, truthTopics);

  // 6. Extract Boundaries (C1-C2)
  const boundaries = extractBoundaries(answers);

  // 7. Generate Activity Tags
  const activityTags = generateActivityTags(activities, boundaries);

  // Build complete profile
  const profile = {
    user_id: userId,
    profile_version: '0.4',
    timestamp: new Date().toISOString(),
    arousal_propensity: arousalPropensity,
    power_dynamic: powerDynamic,
    domain_scores: domainScores,
    activities: activities,
    truth_topics: truthTopics,
    boundaries: boundaries,
    activity_tags: activityTags
  };

  return profile;
}

/**
 * Validate survey responses before calculation
 * @param {Object} answers - Survey answers
 * @returns {Object} - {valid: boolean, errors: string[]}
 */
export function validateResponses(answers) {
  const errors = [];

  // Check arousal responses (A1-A12)
  for (let i = 1; i <= 12; i++) {
    const id = `A${i}`;
    const val = Number(answers[id]);
    if (!Number.isFinite(val) || val < 1 || val > 7) {
      errors.push(`Arousal question ${id} must be between 1-7`);
    }
  }

  // Check power responses (A13-A16)
  for (let i = 13; i <= 16; i++) {
    const id = `A${i}`;
    const val = Number(answers[id]);
    if (!Number.isFinite(val) || val < 1 || val > 7) {
      errors.push(`Power question ${id} must be between 1-7`);
    }
  }

  // Check activity responses (B1-B28) - should be Y/M/N
  const activityIds = [];
  
  // Physical touch: B1-B10 (pairs)
  for (let i = 1; i <= 10; i++) {
    activityIds.push(`B${i}a`, `B${i}b`);
  }
  
  // Oral: B11-B12
  activityIds.push('B11a', 'B11b', 'B12a', 'B12b');
  
  // Anal: B13-B14
  activityIds.push('B13a', 'B13b', 'B14a', 'B14b');
  
  // Power exchange: B15-B18
  activityIds.push('B15a', 'B15b', 'B16a', 'B16b', 'B17a', 'B17b', 'B18a', 'B18b');
  
  // Verbal: B19-B23 (no pairs)
  for (let i = 19; i <= 23; i++) {
    activityIds.push(`B${i}`);
  }
  
  // Display: B24-B25 (pairs), B26-B28 (no pairs)
  activityIds.push('B24a', 'B24b', 'B25a', 'B25b', 'B26', 'B27', 'B28');

  activityIds.forEach(id => {
    const val = (answers[id] || '').toString().trim().toUpperCase();
    if (!['Y', 'M', 'N', 'YES', 'MAYBE', 'NO', ''].includes(val)) {
      errors.push(`Activity question ${id} must be Y, M, or N`);
    }
  });

  // Check truth topics (B29-B36)
  for (let i = 29; i <= 36; i++) {
    const id = `B${i}`;
    const val = (answers[id] || '').toString().trim().toUpperCase();
    if (!['Y', 'M', 'N', 'YES', 'MAYBE', 'NO', ''].includes(val)) {
      errors.push(`Truth topic question ${id} must be Y, M, or N`);
    }
  }

  // Boundaries are optional, so no validation needed

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Generate profile summary for display
 * @param {Object} profile - Complete profile
 * @returns {string} - Human-readable summary
 */
export function generateProfileSummary(profile) {
  const { arousal_propensity, power_dynamic, domain_scores } = profile;

  let summary = '';

  // Arousal style
  if (arousal_propensity.sexual_excitation >= 0.7 && arousal_propensity.inhibition_performance < 0.4) {
    summary += 'You have a highly responsive arousal style with low performance anxiety. ';
  } else if (arousal_propensity.sexual_excitation < 0.4) {
    summary += 'You have a slower-building arousal style that benefits from intentional buildup. ';
  } else {
    summary += 'You have a moderate arousal style. ';
  }

  // Power dynamic
  summary += `Your power dynamic orientation is **${power_dynamic.orientation}** with ${power_dynamic.interpretation.toLowerCase()}. `;

  // Top domain
  const sortedDomains = Object.entries(domain_scores)
    .sort((a, b) => b[1] - a[1]);
  const topDomain = sortedDomains[0];

  summary += `Your highest domain preference is **${topDomain[0]}** (${topDomain[1]}/100).`;

  return summary;
}

/**
 * Export profile to JSON for storage
 * @param {Object} profile - Profile object
 * @returns {string} - JSON string
 */
export function exportProfile(profile) {
  return JSON.stringify(profile, null, 2);
}

/**
 * Import profile from JSON
 * @param {string} json - JSON string
 * @returns {Object} - Profile object
 */
export function importProfile(json) {
  try {
    return JSON.parse(json);
  } catch (e) {
    console.error('Failed to parse profile JSON:', e);
    return null;
  }
}

