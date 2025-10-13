/**
 * Overlap Helper - Matching algorithm (v0.3.1)
 * Direction-aware matching with boundary gates and trait complement.
 */

import { CATEGORY_MAP, CATEGORIES } from './categoryMap.js';

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
// Direction-aware Jaccard:
// - For bases with A/B variants (e.g., B14a/B14b), compute cross-direction overlap
//   mean(min(A[b], B[a]), min(A[a], B[b])) with union as mean of corresponding maxima.
// - For non-directional items, compare same IDs.
function jaccardWeightedDirectional(itemIds, answersA, answersB) {
  let intersection = 0;
  let union = 0;

  // Group by base (e.g., B14)
  const baseToVariants = new Map();
  const nonDirectional = [];

  for (const id of itemIds) {
    const m = /^([A-Za-z]+\d+)([ab])$/i.exec(id);
    if (m) {
      const base = m[1];
      const variant = m[2].toLowerCase();
      if (!baseToVariants.has(base)) baseToVariants.set(base, new Set());
      baseToVariants.get(base).add(variant);
    } else {
      nonDirectional.push(id);
    }
  }

  // Handle directional bases
  for (const [base, variants] of baseToVariants.entries()) {
    const hasA = variants.has('a');
    const hasB = variants.has('b');

    // Cross-direction terms
    const Ab = ynm01(answersA[`${base}b`]);
    const Ba = ynm01(answersB[`${base}a`]);
    const Aa = ynm01(answersA[`${base}a`]);
    const Bb = ynm01(answersB[`${base}b`]);

    // Only form terms if at least one side of that term is represented in the map
    // and at least one respondent answered (non-zero).
    if (hasA || hasB) {
      // Term 1: A does (b) with B receives (a)
      if (hasB || hasA) {
        if (!(Ab === 0 && Ba === 0)) {
          intersection += Math.min(Ab, Ba);
          union += Math.max(Ab, Ba);
        }
      }
      // Term 2: A receives (a) with B does (b)
      if (hasA || hasB) {
        if (!(Aa === 0 && Bb === 0)) {
          intersection += Math.min(Aa, Bb);
          union += Math.max(Aa, Bb);
        }
      }
    }
  }

  // Handle non-directional items as standard Jaccard
  for (const id of nonDirectional) {
    const a = ynm01(answersA[id]);
    const b = ynm01(answersB[id]);
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

  // Hard NO gates by simple token matching against category key
  const catToken = category.toLowerCase().replace(/_/g, '-');
  if (hardNosA.has(catToken) || hardNosB.has(catToken)) return 0;

  // Recording gate
  if (category === 'RECORDING') {
    if (boundariesA?.noRecording || boundariesB?.noRecording) return 0;
  }

  // Impact cap scaling (exclude excess by scaling overlap)
  if (category === 'IMPACT') {
    const capA = typeof boundariesA?.impactCap === 'number' ? Math.max(0, Math.min(100, boundariesA.impactCap)) : 100;
    const capB = typeof boundariesB?.impactCap === 'number' ? Math.max(0, Math.min(100, boundariesB.impactCap)) : 100;
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
    jaccardWeight = 0.20,
    powerWeight = 0.20,
    domainWeight = 0.60
  } = options;

  // Calculate category similarities
  const catScores = {};
  let sum = 0;
  const categories = CATEGORIES;

  for (const category of categories) {
    const itemIds = CATEGORY_MAP[category] || [];
    const rawScore = jaccardWeightedDirectional(itemIds, answersA, answersB);
    const gatedScore = gateCategoryScore(category, rawScore, boundariesA, boundariesB);
    catScores[category] = gatedScore;
    sum += gatedScore;
  }

  const meanJ = categories.length > 0 ? sum / categories.length : 0;

  // Calculate power complement
  const powerComplement = powerComplementFromTraits(traitsA, traitsB);

  // Domain similarity placeholder: if domain vectors exist, compute here.
  // Fallback to trait similarity via cosine-like average.
  let domainSim = 0;
  if (traitsA && traitsB) {
    const keys = Array.from(new Set([...Object.keys(traitsA), ...Object.keys(traitsB)]));
    if (keys.length > 0) {
      let num = 0, den = 0;
      for (const k of keys) {
        const a = typeof traitsA[k] === 'number' ? traitsA[k] : 0;
        const b = typeof traitsB[k] === 'number' ? traitsB[k] : 0;
        // traits are 0..1 in this app
        num += 1 - Math.abs(a - b);
        den += 1;
      }
      domainSim = den > 0 ? Math.max(0, Math.min(1, num / den)) : 0;
    }
  }

  // Overall score
  const overall = Math.max(0, Math.min(1, jaccardWeight * meanJ + powerWeight * powerComplement + domainWeight * domainSim));

  return {
    overall: overall * 100, // Scale to 0-100
    catScores,
    meanJ,
    powerComplement
  };
}

