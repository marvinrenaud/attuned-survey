/**
 * Arousal Propensity Calculator (v0.4)
 * Calculates Sexual Excitation and Sexual Inhibition scores from SES/SIS responses
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
 * Interpret 0-1 score into descriptive band
 * @param {number} score - Score from 0-1
 * @returns {string} - Interpretation band
 */
function interpretBand(score) {
  if (score <= 0.30) return 'Low';
  if (score <= 0.55) return 'Moderate-Low';
  if (score <= 0.75) return 'Moderate-High';
  return 'High';
}

/**
 * Calculate arousal propensity from survey responses
 * @param {Object} answers - Survey answers object
 * @returns {Object} - Arousal propensity scores and interpretations
 */
export function calculateArousalPropensity(answers) {
  // SE items: A1-A4
  const seItems = ['A1', 'A2', 'A3', 'A4']
    .map(id => normalizeLikert(answers[id]));
  const seNormalized = mean(seItems);

  // SIS-P items: A5-A8
  const sisPItems = ['A5', 'A6', 'A7', 'A8']
    .map(id => normalizeLikert(answers[id]));
  const sisPNormalized = mean(sisPItems);

  // SIS-C items: A9-A12
  const sisCItems = ['A9', 'A10', 'A11', 'A12']
    .map(id => normalizeLikert(answers[id]));
  const sisCNormalized = mean(sisCItems);

  return {
    sexual_excitation: Math.round(seNormalized * 100) / 100,
    inhibition_performance: Math.round(sisPNormalized * 100) / 100,
    inhibition_consequence: Math.round(sisCNormalized * 100) / 100,
    interpretation: {
      se: interpretBand(seNormalized),
      sis_p: interpretBand(sisPNormalized),
      sis_c: interpretBand(sisCNormalized)
    }
  };
}

/**
 * Get descriptive text for arousal profile
 * @param {Object} arousalProfile - Arousal propensity object
 * @returns {string} - Human-readable description
 */
export function getArousalDescription(arousalProfile) {
  const { sexual_excitation, inhibition_performance, inhibition_consequence, interpretation } = arousalProfile;
  
  let description = '';
  
  // Sexual Excitation
  if (sexual_excitation >= 0.7) {
    description += 'You have a highly responsive arousal style - you get turned on easily by erotic cues and situations. ';
  } else if (sexual_excitation >= 0.5) {
    description += 'You have a moderate arousal responsiveness - you can get turned on with the right stimuli. ';
  } else {
    description += 'You have a slower-building arousal style that benefits from intentional buildup and patience. ';
  }
  
  // Performance Inhibition
  if (inhibition_performance >= 0.6) {
    description += 'Performance concerns significantly affect your arousal - reassurance and low-pressure environments help. ';
  } else if (inhibition_performance >= 0.4) {
    description += 'Performance worries occasionally impact your arousal. ';
  } else {
    description += 'You experience minimal performance anxiety during intimate activities. ';
  }
  
  // Consequence Inhibition
  if (inhibition_consequence >= 0.6) {
    description += 'Privacy and safety concerns are important for your arousal - secure, private settings work best.';
  } else if (inhibition_consequence >= 0.4) {
    description += 'You have moderate sensitivity to external concerns like privacy or consequences.';
  } else {
    description += 'You are relatively uninhibited by concerns about consequences or privacy.';
  }
  
  return description;
}

