/**
 * Overlap Helper - Matching algorithm (v0.2.3)
 * Computes compatibility between two respondents
 */

import { CATEGORY_MAP, CATEGORY_TOKENS } from './categoryMap.js';

/**
 * Convert YMN answer to numeric value
 */
function ynm01(value) {
  const v = (value || '').trim().toUpperCase();
  if (v === 'Y') return 1.0;
  if (v === 'M') return 0.5;
  return 0.0;
}

/**
 * Calculate weighted Jaccard similarity for a set of items
 */
function jaccardWeighted(itemIds, answersA, answersB) {
  let intersection = 0;
  let union = 0;

  for (const id of itemIds) {
    const a = ynm01(answersA[id]);
    const b = ynm01(answersB[id]);

    // Skip if both blank
    if (a === 0 && b === 0) continue;

    intersection += Math.min(a, b);
    union += Math.max(a, b);
  }

  return union === 0 ? 0 : intersection / union;
}

/**
 * Apply boundary gates to category score
 */
function gateCategoryScore(category, score, boundariesA, boundariesB) {
  let gatedScore = score;

  const hardNosA = new Set((boundariesA?.hardNos || []).map(x => x.toLowerCase()));
  const hardNosB = new Set((boundariesB?.hardNos || []).map(x => x.toLowerCase()));

  // Hard NO gate - if either person has a hard NO, score = 0
  const tokens = CATEGORY_TOKENS[category] || [];
  for (const token of tokens) {
    if (hardNosA.has(token) || hardNosB.has(token)) {
      return 0;
    }
  }

  // Recording gate
  if (category === 'RECORDING') {
    if (boundariesA?.noRecording || boundariesB?.noRecording) {
      return 0;
    }
  }

  // Impact cap scaling
  if (category === 'IMPACT') {
    const capA = typeof boundariesA?.impactCap === 'number' 
      ? Math.max(0, Math.min(100, boundariesA.impactCap)) 
      : 100;
    const capB = typeof boundariesB?.impactCap === 'number' 
      ? Math.max(0, Math.min(100, boundariesB.impactCap)) 
      : 100;
    const scale = Math.min(capA, capB) / 100;
    gatedScore *= scale;
  }

  return gatedScore;
}

/**
 * Calculate power complement from trait scores
 */
function powerComplementFromTraits(traitsA, traitsB) {
  if (!traitsA || !traitsB) return 0;

  const topA = (traitsA.POWER_TOP ?? 50) / 100;
  const botA = (traitsA.POWER_BOTTOM ?? 50) / 100;
  const topB = (traitsB.POWER_TOP ?? 50) / 100;
  const botB = (traitsB.POWER_BOTTOM ?? 50) / 100;

  const comp1 = Math.max(0, Math.min(1, topA)) * Math.max(0, Math.min(1, botB));
  const comp2 = Math.max(0, Math.min(1, topB)) * Math.max(0, Math.min(1, botA));

  return Math.max(comp1, comp2);
}

/**
 * Compute overall match between two submissions
 * @param {Object} options
 * @param {Record<string, string | number>} options.answersA
 * @param {Record<string, string | number>} options.answersB
 * @param {Record<string, number>} options.traitsA
 * @param {Record<string, number>} options.traitsB
 * @param {Object} options.boundariesA
 * @param {Object} options.boundariesB
 * @param {number} [options.jaccardWeight=0.85]
 * @param {number} [options.powerWeight=0.15]
 * @returns {Object} {overall, catScores, meanJ, powerComplement}
 */
export function computeOverallMatch(options) {
  const {
    answersA,
    answersB,
    traitsA,
    traitsB,
    boundariesA,
    boundariesB,
    jaccardWeight = 0.85,
    powerWeight = 0.15
  } = options;

  // Calculate category similarities
  const catScores = {};
  let sum = 0;
  const categories = Object.keys(CATEGORY_MAP);

  for (const category of categories) {
    const itemIds = CATEGORY_MAP[category];
    const rawScore = jaccardWeighted(itemIds, answersA, answersB);
    const gatedScore = gateCategoryScore(category, rawScore, boundariesA, boundariesB);
    catScores[category] = gatedScore;
    sum += gatedScore;
  }

  const meanJ = categories.length > 0 ? sum / categories.length : 0;

  // Calculate power complement
  const powerComplement = powerComplementFromTraits(traitsA, traitsB);

  // Overall score
  const overall = Math.max(0, Math.min(1, jaccardWeight * meanJ + powerWeight * powerComplement));

  return {
    overall: overall * 100, // Scale to 0-100
    catScores,
    meanJ,
    powerComplement
  };
}

