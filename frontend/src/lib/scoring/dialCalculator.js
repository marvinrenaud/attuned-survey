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
  // traits are expected on 0–1 scale; missing = 0.5 (neutral)
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const to01 = (v) => {
    if (typeof v !== 'number' || Number.isNaN(v)) return 0.5;
    // If a trait accidentally arrives on 0–100, auto-detect and scale down
    if (v > 1) return clamp01(v / 100);
    return clamp01(v);
  };

  const result = {};
  for (const [dialName, dialSpec] of Object.entries(dimensionFormulas || {})) {
    const weights = dialSpec?.weights || {};
    let num = 0;
    let den = 0;
    for (const [trait, weight] of Object.entries(weights)) {
      const raw = traits?.[trait];
      const val01 = raw === undefined ? 0.5 : to01(raw);
      num += val01 * weight;
      den += Math.abs(weight);
    }
    // Average back to 0–1, then output 0–100 for display
    const dial01 = den > 0 ? num / den : 0;
    result[dialName] = Math.max(0, Math.min(100, dial01 * 100));
  }
  return result;
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

