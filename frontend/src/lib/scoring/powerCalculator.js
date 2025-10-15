/**
 * Power Dynamic Calculator (v0.4)
 * Determines power orientation (Top/Bottom/Switch/Versatile) from survey responses
 */

/**
 * Map Likert 1-7 response to 0-1 scale
 * @param {number} value - Likert response (1-7)
 * @returns {number} - Normalized value (0-1)
 */
function normalizeLikert(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 1 || n > 7) return 0;
  return (n - 1) / 6;
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
 * Interpret confidence score
 * @param {number} confidence - Confidence from 0-1
 * @returns {string} - Confidence interpretation
 */
function interpretConfidence(confidence) {
  if (confidence <= 0.30) return 'Low confidence';
  if (confidence <= 0.60) return 'Moderate confidence';
  if (confidence <= 0.85) return 'High confidence';
  return 'Very high confidence';
}

/**
 * Calculate power dynamic from survey responses
 * @param {Object} answers - Survey answers object
 * @returns {Object} - Power dynamic scores and orientation
 */
export function calculatePowerDynamic(answers) {
  // Configuration from v0.4 schema
  const THETA_FLOOR = 30;  // Minimum threshold for engagement
  const DELTA_BAND = 15;   // Band for determining Switch

  // Top items: A13, A15
  const topItems = ['A13', 'A15']
    .map(id => normalizeLikert(answers[id]));
  const topScore = mean(topItems) * 100;

  // Bottom items: A14, A16
  const bottomItems = ['A14', 'A16']
    .map(id => normalizeLikert(answers[id]));
  const bottomScore = mean(bottomItems) * 100;

  // Determine orientation
  let orientation;
  let confidence;
  let interpretation;

  if (topScore < THETA_FLOOR && bottomScore < THETA_FLOOR) {
    // Both scores low - still exploring
    orientation = 'Versatile/Undefined';
    confidence = Math.max(topScore, bottomScore) / 100;
    interpretation = 'Low engagement - still exploring preferences';
  } else if (
    Math.abs(topScore - bottomScore) <= DELTA_BAND &&
    Math.min(topScore, bottomScore) >= THETA_FLOOR
  ) {
    // Scores close and both engaged - Switch
    orientation = 'Switch';
    confidence = Math.min(topScore, bottomScore) / 100;
    interpretation = interpretConfidence(confidence) + ' Switch';
  } else if (topScore > bottomScore) {
    // Top-leaning
    orientation = 'Top';
    confidence = (topScore / 100) * (1 - 0.3 * (bottomScore / 100));
    interpretation = interpretConfidence(confidence) + ' Top';
  } else {
    // Bottom-leaning
    orientation = 'Bottom';
    confidence = (bottomScore / 100) * (1 - 0.3 * (topScore / 100));
    interpretation = interpretConfidence(confidence) + ' Bottom';
  }

  return {
    orientation,
    top_score: Math.round(topScore),
    bottom_score: Math.round(bottomScore),
    confidence: Math.round(confidence * 100) / 100,
    interpretation
  };
}

/**
 * Get descriptive text for power dynamic
 * @param {Object} powerDynamic - Power dynamic object
 * @returns {string} - Human-readable description
 */
export function getPowerDescription(powerDynamic) {
  const { orientation, confidence, top_score, bottom_score } = powerDynamic;

  switch (orientation) {
    case 'Top':
      if (confidence >= 0.7) {
        return `You strongly identify with the dominant role, enjoying giving direction and taking control during intimate activities. Your Top score is ${top_score}/100.`;
      } else {
        return `You lean toward the dominant role but also have some flexibility. Your Top score is ${top_score}/100, Bottom score is ${bottom_score}/100.`;
      }
    
    case 'Bottom':
      if (confidence >= 0.7) {
        return `You strongly identify with the submissive role, enjoying following direction and letting your partner take control. Your Bottom score is ${bottom_score}/100.`;
      } else {
        return `You lean toward the submissive role but also have some flexibility. Your Bottom score is ${bottom_score}/100, Top score is ${top_score}/100.`;
      }
    
    case 'Switch':
      return `You enjoy both dominant and submissive roles depending on the situation or mood. You're comfortable with power exchange in either direction. Top: ${top_score}/100, Bottom: ${bottom_score}/100.`;
    
    case 'Versatile/Undefined':
      return `Power dynamics aren't a strong focus for you right now, or you're still exploring what roles feel comfortable. This is perfectly normal - many people develop these preferences over time.`;
    
    default:
      return `Your power dynamic orientation: ${orientation}`;
  }
}

/**
 * Get power complement score for compatibility
 * Used in compatibility calculations
 * @param {Object} powerA - First person's power dynamic
 * @param {Object} powerB - Second person's power dynamic
 * @returns {number} - Complement score 0-1
 */
export function calculatePowerComplement(powerA, powerB) {
  const orientationA = powerA.orientation;
  const orientationB = powerB.orientation;

  // Switch + Switch: High compatibility
  if (orientationA === 'Switch' && orientationB === 'Switch') {
    return 0.90;
  }

  // Top + Bottom: Excellent complement (scaled by confidence)
  if (
    (orientationA === 'Top' && orientationB === 'Bottom') ||
    (orientationA === 'Bottom' && orientationB === 'Top')
  ) {
    const avgConfidence = (powerA.confidence + powerB.confidence) / 2;
    return 0.85 + (0.15 * avgConfidence);
  }

  // Switch + (Top or Bottom): Good compatibility
  if (
    (orientationA === 'Switch' || orientationA === 'Versatile/Undefined') &&
    (orientationB === 'Top' || orientationB === 'Bottom')
  ) {
    return 0.70;
  }

  if (
    (orientationB === 'Switch' || orientationB === 'Versatile/Undefined') &&
    (orientationA === 'Top' || orientationA === 'Bottom')
  ) {
    return 0.70;
  }

  // Both same pole (Top+Top or Bottom+Bottom) or both undefined: Lower compatibility
  return 0.40;
}

