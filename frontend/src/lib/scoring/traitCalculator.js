/**
 * Trait Calculator - converts raw answers to trait scores
 */

/**
 * Convert Likert7 response (1-7) to 0-100 scale
 * @param {number} value - Likert response 1-7
 * @returns {number} - Scaled value 0-100
 */
function scaleLikert7(value) {
  if (value < 1 || value > 7) return 0;
  return ((value - 1) / 6) * 100;
}

/**
 * Convert YMN response to numeric value
 * @param {string} value - 'Y', 'M', or 'N'
 * @returns {number} - Y=1, M=0.5, N=0
 */
function scaleYMN(value) {
  const v = (value || '').trim().toUpperCase();
  if (v === 'Y') return 1.0;
  if (v === 'M') return 0.5;
  return 0.0;
}

/**
 * Clip value to range [0, 100]
 * @param {number} value
 * @returns {number}
 */
function clip(value) {
  return Math.max(0, Math.min(100, value));
}

/**
 * Calculate trait scores from answers
 * @param {Record<string, string | number>} answers - Raw answers keyed by question ID
 * @param {Array} items - Question items with trait weights from schema
 * @returns {Record<string, number>} - Trait scores (0-100)
 */
export function calculateTraits(answers, items) {
  const traitAccumulators = {};
  const traitCounts = {};

  // Process each item
  for (const item of items) {
    const answer = answers[item.id];
    if (answer === undefined || answer === null || answer === '') continue;

    let scaledValue = 0;
    
    // Scale based on question type
    if (item.type === 'likert7') {
      scaledValue = scaleLikert7(Number(answer));
    } else if (item.type === 'ymn') {
      scaledValue = scaleYMN(String(answer)) * 100; // Scale to 0-100
    } else if (item.type === 'slider') {
      scaledValue = Number(answer); // Already 0-100
    } else if (item.type === 'boundary') {
      // Boundaries don't contribute to traits directly
      continue;
    }

    // Apply trait weights
    for (const traitWeight of item.traits || []) {
      const { trait, weight } = traitWeight;
      
      if (!traitAccumulators[trait]) {
        traitAccumulators[trait] = 0;
        traitCounts[trait] = 0;
      }

      // Weighted contribution
      const contribution = scaledValue * weight;
      traitAccumulators[trait] += contribution;
      traitCounts[trait] += Math.abs(weight); // Count absolute weight for normalization
    }
  }

  // Normalize and clip traits
  const traits = {};
  for (const trait in traitAccumulators) {
    if (traitCounts[trait] > 0) {
      // Average by total absolute weight
      const rawScore = traitAccumulators[trait] / traitCounts[trait];
      traits[trait] = clip(rawScore);
    } else {
      traits[trait] = 50; // Default neutral
    }
  }

  // Apply SIS_P penalty (from schema notes)
  if (traits.SIS_P !== undefined) {
    traits.SIS_P = clip(traits.SIS_P * 0.65); // -0.35 penalty = multiply by 0.65
  }

  return traits;
}

/**
 * Extract boundary flags from answers
 * @param {Record<string, string | number>} answers
 * @returns {Object}
 */
export function extractBoundaries(answers) {
  const boundaries = {
    hardNos: [],
    impactCap: undefined,
    noRecording: false
  };

  // C1: Impact cap
  if (answers.C1 !== undefined && answers.C1 !== '') {
    boundaries.impactCap = Number(answers.C1);
  }

  // C2: Hard NOs (comma-separated string)
  if (answers.C2) {
    const hardNoStr = String(answers.C2).toLowerCase();
    boundaries.hardNos = hardNoStr.split(',').map(s => s.trim()).filter(Boolean);
  }

  // C4: No recording
  if (answers.C4) {
    const c4 = String(answers.C4).trim().toUpperCase();
    boundaries.noRecording = (c4 === 'Y' || c4 === 'YES' || c4 === 'TRUE');
  }

  return boundaries;
}

