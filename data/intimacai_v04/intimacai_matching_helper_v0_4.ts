// intimacai_matching_helper_v0.4.ts
// Compatibility calculation for v0.4 profiles

export type PowerDynamic = {
  label: 'Top' | 'Bottom' | 'Switch' | 'Versatile/Undefined';
  confidence: number;
  top_score: number;
  bottom_score: number;
};

export type DomainScores = {
  sensation: number;
  connection: number;
  power: number;
  exploration: number;
  verbal: number;
};

export type ActivityMap = {
  physical_touch: Record<string, number>;
  oral: Record<string, number>;
  anal: Record<string, number>;
  power_exchange: Record<string, number>;
  verbal_roleplay: Record<string, number>;
  display_performance: Record<string, number>;
};

export type BoundaryConflict = {
  player: string;
  boundary: string;
  conflicting_activity: string;
};

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/**
 * Calculate power dynamic complementarity (0-1)
 */
export function calculatePowerComplement(
  powerA: PowerDynamic,
  powerB: PowerDynamic
): number {
  if (powerA.label === 'Switch' && powerB.label === 'Switch') {
    return 0.90;
  }

  if (
    (powerA.label === 'Top' && powerB.label === 'Bottom') ||
    (powerA.label === 'Bottom' && powerB.label === 'Top')
  ) {
    const avgConfidence = (powerA.confidence + powerB.confidence) / 2;
    return clamp01(0.85 + (0.15 * avgConfidence));
  }

  if (
    (powerA.label === 'Switch' || powerA.label === 'Versatile/Undefined') &&
    (powerB.label === 'Top' || powerB.label === 'Bottom')
  ) {
    return 0.70;
  }

  if (
    (powerB.label === 'Switch' || powerB.label === 'Versatile/Undefined') &&
    (powerA.label === 'Top' || powerA.label === 'Bottom')
  ) {
    return 0.70;
  }

  // Both same pole or both undefined
  return 0.40;
}

/**
 * Calculate domain similarity (0-1)
 */
export function calculateDomainSimilarity(
  domainsA: DomainScores,
  domainsB: DomainScores
): number {
  const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
  const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
  const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
  const explorationDist = 1 - Math.abs(domainsA.exploration - domainsB.exploration) / 100;
  const verbalDist = 1 - Math.abs(domainsA.verbal - domainsB.verbal) / 100;

  return (sensationDist + connectionDist + powerDist + explorationDist + verbalDist) / 5;
}

/**
 * Calculate Jaccard coefficient for a single activity category
 */
export function calculateCategoryJaccard(
  categoryA: Record<string, number>,
  categoryB: Record<string, number>
): number {
  const keys = Object.keys(categoryA);
  let mutualYes = 0;
  let atLeastOneYes = 0;

  keys.forEach(key => {
    const valA = categoryA[key] || 0;
    const valB = categoryB[key] || 0;

    // Both interested (>= 0.5)
    if (valA >= 0.5 && valB >= 0.5) {
      mutualYes += 1;
    }

    // At least one interested
    if (valA >= 0.5 || valB >= 0.5) {
      atLeastOneYes += 1;
    }
  });

  if (atLeastOneYes === 0) return 0;
  return mutualYes / atLeastOneYes;
}

/**
 * Calculate activity-level overlap using category Jaccard (0-1)
 */
export function calculateActivityOverlap(
  activitiesA: ActivityMap,
  activitiesB: ActivityMap
): number {
  const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>;
  const jaccardScores: number[] = [];

  categories.forEach(category => {
    const jaccard = calculateCategoryJaccard(
      activitiesA[category],
      activitiesB[category]
    );
    jaccardScores.push(jaccard);
  });

  return jaccardScores.reduce((sum, val) => sum + val, 0) / jaccardScores.length;
}

/**
 * Calculate overall compatibility score (0-100)
 */
export function calculateCompatibility(
  powerA: PowerDynamic,
  powerB: PowerDynamic,
  domainsA: DomainScores,
  domainsB: DomainScores,
  activitiesA: ActivityMap,
  activitiesB: ActivityMap,
  boundaryConflicts: BoundaryConflict[] = [],
  weights = { power: 0.15, domain: 0.25, activity: 0.40, truth: 0.20 }
): number {
  const powerComp = calculatePowerComplement(powerA, powerB);
  const domainSim = calculateDomainSimilarity(domainsA, domainsB);
  const activityOverlap = calculateActivityOverlap(activitiesA, activitiesB);

  // Calculate weighted score
  let score = (
    weights.power * powerComp +
    weights.domain * domainSim +
    weights.activity * activityOverlap
    // Note: truth overlap would be added here if truth topics passed in
  );

  // Apply boundary penalty
  const boundaryPenalty = boundaryConflicts.length * 0.2;
  score = Math.max(0, score - boundaryPenalty);

  return Math.round(score * 100);
}

/**
 * Identify mutual activities (both players Y or M)
 */
export function identifyMutualActivities(
  activitiesA: ActivityMap,
  activitiesB: ActivityMap
): Record<string, string[]> {
  const result: Record<string, string[]> = {};

  const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>;
  categories.forEach(category => {
    const mutualKeys: string[] = [];
    const keys = Object.keys(activitiesA[category]);

    keys.forEach(key => {
      const valA = activitiesA[category][key] || 0;
      const valB = activitiesB[category][key] || 0;

      // Both Y or M
      if (valA >= 0.5 && valB >= 0.5) {
        mutualKeys.push(key);
      }
    });

    result[category] = mutualKeys;
  });

  return result;
}

/**
 * Simplified compatibility function with default weights
 * Matches v0.3.1 blendScore signature for backward compatibility
 */
export function blendScore(
  powerA: PowerDynamic,
  powerB: PowerDynamic,
  domainsA: DomainScores,
  domainsB: DomainScores,
  jacc: number,
  wRole = 0.15,
  wDom = 0.25,
  wJac = 0.60  // Combined activity + truth overlap
): number {
  const powerComp = calculatePowerComplement(powerA, powerB);
  const domainSim = calculateDomainSimilarity(domainsA, domainsB);

  return clamp01(
    wRole * powerComp +
    wDom * domainSim +
    wJac * jacc
  );
}

/**
 * Interpret compatibility score
 */
export function interpretCompatibility(score: number): string {
  if (score >= 85) return 'Exceptional compatibility';
  if (score >= 70) return 'High compatibility';
  if (score >= 55) return 'Moderate compatibility';
  if (score >= 40) return 'Lower compatibility';
  return 'Challenging compatibility';
}
