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
 * Extract boundary flags from answers (v0.3.x with legacy compatibility)
 * Assumptions (v0.3.x):
 * - C1: numeric 0..100 impact cap (default 100 if blank)
 * - C2: comma-separated "hard no" tokens (normalized to kebab-case)
 * - C4: "Recording is OK" (Y/N). noRecording = true when C4 is N/NO/FALSE/0.
 *
 * Legacy shims:
 * - If hardNos include "recording"/"no-recording", force noRecording = true.
 * - If C5 existed as legacy "No recording (Y/N)" and is 'N', force noRecording = true.
 */
export function extractBoundaries(answers = {}) {
  // ---- Impact cap (C1) ----
  let impactCap = Number(answers.C1);
  if (!Number.isFinite(impactCap)) impactCap = 100;
  impactCap = Math.max(0, Math.min(100, impactCap));

  // ---- Hard NOs (C2) ----
  let hardNos = [];
  if (answers.C2 != null && String(answers.C2).trim() !== '') {
    hardNos = String(answers.C2)
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .map(s =>
        String(s)
          .toLowerCase()
          .replace(/\s+/g, '-')
          .replace(/[^a-z0-9-]/g, '')
      );
  }

  // ---- Recording gate (C4 = "Recording is OK") ----
  const c4raw = String(answers.C4 ?? '').trim().toUpperCase();
  const recordingOk =
    c4raw === 'Y' || c4raw === 'YES' || c4raw === 'TRUE' || c4raw === '1';
  const recordingNo =
    c4raw === 'N' || c4raw === 'NO' || c4raw === 'FALSE' || c4raw === '0';

  let noRecording = false;
  if (recordingNo) noRecording = true;          // v0.3.x normal path
  else if (recordingOk) noRecording = false;    // explicit OK
  else noRecording = false;                      // default if missing/blank

  // ---- Legacy shims ----
  // 1) Hard NO token implies "no recording"
  const hardNoSet = new Set(hardNos);
  if (hardNoSet.has('recording') || hardNoSet.has('no-recording')) {
    noRecording = true;
  }

  // 2) Legacy C5: "No recording (Y/N)" -> treat 'N' as noRecording
  if (typeof answers.C5 === 'string') {
    const c5 = answers.C5.trim().toUpperCase();
    if (c5 === 'N' || c5 === 'NO' || c5 === 'FALSE' || c5 === '0') {
      noRecording = true;
    }
  }

  return { hardNos, impactCap, noRecording };
}

