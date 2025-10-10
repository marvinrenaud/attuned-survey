/**
 * Dial Calculator - converts trait scores to dimension scores
 */

/**
 * Clip value to range [0, 100]
 */
function clip(value) {
  return Math.max(0, Math.min(100, value));
}

/**
 * Calculate dial scores from traits using dimension formulas
 * @param {Record<string, number>} traits - Trait scores (0-100)
 * @param {Object} dimensionFormulas - Dimension formulas from schema
 * @returns {Object} - Dial scores {Adventure, Connection, Intensity, Confidence}
 */
export function calculateDials(traits, dimensionFormulas) {
  const dials = {};

  for (const dialName in dimensionFormulas) {
    const formula = dimensionFormulas[dialName].formula;
    let score = 0;

    for (const trait in formula) {
      const weight = formula[trait];
      const traitValue = traits[trait] !== undefined ? traits[trait] : 50; // Default to neutral
      score += traitValue * weight;
    }

    dials[dialName] = clip(score);
  }

  return dials;
}

/**
 * Check if profile is "Balanced" (uniform across dials)
 * Balanced is defined as low variance across the four dials
 * @param {Object} dials - {Adventure, Connection, Intensity, Confidence}
 * @returns {boolean}
 */
export function isBalanced(dials) {
  const values = Object.values(dials);
  if (values.length === 0) return false;

  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);

  // Balanced if standard deviation is less than 15 (relatively uniform)
  return stdDev < 15;
}

