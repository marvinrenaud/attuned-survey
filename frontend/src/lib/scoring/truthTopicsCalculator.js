/**
 * Truth Topics Calculator (v0.4)
 * Processes truth topic responses and calculates openness score
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
 * Calculate mean of array
 * @param {number[]} values
 * @returns {number}
 */
function mean(values) {
  if (!values || values.length === 0) return 0;
  const sum = values.reduce((a, b) => a + b, 0);
  return sum / values.length;
}

/**
 * Convert truth topic responses and calculate openness score
 * @param {Object} answers - Raw survey answers
 * @returns {Object} - Truth topics with openness score
 */
export function convertTruthTopics(answers) {
  const truthTopics = {};
  const values = [];

  // Truth Topics: B29-B36 (8 items)
  const topicMap = {
    'B29': 'past_experiences',
    'B30': 'fantasies',
    'B31': 'turn_ons',
    'B32': 'turn_offs',
    'B33': 'insecurities',
    'B34': 'boundaries',
    'B35': 'future_fantasies',
    'B36': 'feeling_desired'
  };

  Object.entries(topicMap).forEach(([qid, topicKey]) => {
    const value = convertYMN(answers[qid]);
    truthTopics[topicKey] = value;
    values.push(value);
  });

  // Calculate openness score (0-100)
  truthTopics.openness_score = Math.round(mean(values) * 100);

  return truthTopics;
}

/**
 * Get descriptive text for truth topic openness
 * @param {Object} truthTopics - Truth topics object
 * @returns {string} - Human-readable description
 */
export function getTruthTopicsDescription(truthTopics) {
  const { openness_score } = truthTopics;

  if (openness_score >= 80) {
    return 'You are very open to discussing intimate topics and sharing personal thoughts with your partner. This high level of openness can foster deep emotional connection.';
  } else if (openness_score >= 60) {
    return 'You are moderately open to discussing intimate topics. You are comfortable sharing many aspects of your desires and boundaries.';
  } else if (openness_score >= 40) {
    return 'You have selective openness about intimate topics. You may prefer to warm up gradually or focus on specific types of conversation.';
  } else {
    return 'You prefer to keep some intimate topics private or may still be exploring your comfort level with these conversations. That\'s perfectly valid - everyone has their own pace.';
  }
}

/**
 * Identify which topics both partners are open to
 * @param {Object} truthTopicsA - First person's truth topics
 * @param {Object} truthTopicsB - Second person's truth topics
 * @returns {string[]} - Array of mutually open topic keys
 */
export function identifyMutualTruthTopics(truthTopicsA, truthTopicsB) {
  const mutual = [];
  const topicKeys = [
    'past_experiences', 'fantasies', 'turn_ons', 'turn_offs',
    'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired'
  ];

  topicKeys.forEach(key => {
    // Both interested (Y or M = >= 0.5)
    if (truthTopicsA[key] >= 0.5 && truthTopicsB[key] >= 0.5) {
      mutual.push(key);
    }
  });

  return mutual;
}

/**
 * Calculate truth overlap for compatibility
 * @param {Object} truthTopicsA - First person's truth topics
 * @param {Object} truthTopicsB - Second person's truth topics
 * @returns {number} - Overlap score 0-1
 */
export function calculateTruthOverlap(truthTopicsA, truthTopicsB) {
  const topicKeys = [
    'past_experiences', 'fantasies', 'turn_ons', 'turn_offs',
    'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired'
  ];

  let mutualCount = 0;
  topicKeys.forEach(key => {
    if (truthTopicsA[key] >= 0.5 && truthTopicsB[key] >= 0.5) {
      mutualCount++;
    }
  });

  return mutualCount / topicKeys.length;
}

