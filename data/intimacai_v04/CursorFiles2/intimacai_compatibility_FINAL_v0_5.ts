// intimacai_compatibility_FINAL_v0.5.ts
// FULLY CORRECTED with asymmetric Top/Bottom dynamics AND same-pole incompatibility recognition

export type PowerOrientation = 'Top' | 'Bottom' | 'Switch' | 'Versatile/Undefined';

export type PowerDynamic = {
  orientation: PowerOrientation;
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

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/**
 * Calculate power dynamic complementarity (unchanged)
 */
export function calculatePowerComplement(
  powerA: PowerDynamic,
  powerB: PowerDynamic
): number {
  if (powerA.orientation === 'Switch' && powerB.orientation === 'Switch') {
    return 0.90;
  }

  if (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  ) {
    const avgConfidence = (powerA.confidence + powerB.confidence) / 2;
    return clamp01(0.85 + (0.15 * avgConfidence));
  }

  if (
    (powerA.orientation === 'Switch' || powerA.orientation === 'Versatile/Undefined') &&
    (powerB.orientation === 'Top' || powerB.orientation === 'Bottom')
  ) {
    return 0.70;
  }

  if (
    (powerB.orientation === 'Switch' || powerB.orientation === 'Versatile/Undefined') &&
    (powerA.orientation === 'Top' || powerA.orientation === 'Bottom')
  ) {
    return 0.70;
  }

  return 0.40;
}

/**
 * CORRECTED: Domain similarity that recognizes complementary dynamics
 * For Top/Bottom pairs, divergence in exploration/verbal is actually beneficial
 */
export function calculateDomainSimilarity(
  domainsA: DomainScores,
  domainsB: DomainScores,
  powerA: PowerDynamic,
  powerB: PowerDynamic
): number {
  
  const isComplementaryPair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  );

  if (isComplementaryPair) {
    // For complementary pairs, use minimum threshold approach for exploration/verbal
    // An eager Bottom (95) + measured Top (60) is ideal, not a problem!
    
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
    
    // For exploration and verbal: as long as minimum is adequate (>50), don't penalize
    const minExploration = Math.min(domainsA.exploration, domainsB.exploration);
    const minVerbal = Math.min(domainsA.verbal, domainsB.verbal);
    
    // If minimum is 50+, score is 1.0 (no penalty)
    // If minimum is below 50, scale proportionally
    const explorationScore = minExploration >= 50 ? 1.0 : minExploration / 50;
    const verbalScore = minVerbal >= 50 ? 1.0 : minVerbal / 50;
    
    return (sensationDist + connectionDist + powerDist + explorationScore + verbalScore) / 5;
  } else {
    // For Switch/Switch or same-pole pairs, use standard distance
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100;
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100;
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100;
    const explorationDist = 1 - Math.abs(domainsA.exploration - domainsB.exploration) / 100;
    const verbalDist = 1 - Math.abs(domainsA.verbal - domainsB.verbal) / 100;
    
    return (sensationDist + connectionDist + powerDist + explorationDist + verbalDist) / 5;
  }
}

/**
 * Standard Jaccard for non-directional or symmetric pairs
 */
export function calculateStandardJaccard(
  categoryA: Record<string, number>,
  categoryB: Record<string, number>
): number {
  const keys = Object.keys(categoryA);
  let mutualYes = 0;
  let atLeastOneYes = 0;

  keys.forEach(key => {
    const valA = categoryA[key] || 0;
    const valB = categoryB[key] || 0;

    if (valA >= 0.5 && valB >= 0.5) {
      mutualYes += 1;
    }

    if (valA >= 0.5 || valB >= 0.5) {
      atLeastOneYes += 1;
    }
  });

  if (atLeastOneYes === 0) return 0;
  return mutualYes / atLeastOneYes;
}

/**
 * FULLY CORRECTED: Asymmetric directional Jaccard for Top/Bottom pairs
 * Recognizes that Top/Bottom dynamics are inherently asymmetric
 */
export function calculateAsymmetricDirectionalJaccard(
  topCategory: Record<string, number>,
  bottomCategory: Record<string, number>
): number {
  const keys = Object.keys(topCategory);
  
  let primaryMatches = 0;      // Top gives what Bottom wants to receive
  let primaryPotential = 0;     // Total opportunities for Top to give
  let secondaryMatches = 0;     // Bottom gives what Top wants to receive  
  let secondaryPotential = 0;   // Total opportunities for Bottom to give
  let nonDirectionalMatches = 0;
  let nonDirectionalPotential = 0;

  keys.forEach(key => {
    const topVal = topCategory[key] || 0;
    const bottomVal = bottomCategory[key] || 0;

    if (key.endsWith('_give')) {
      const receiveKey = key.replace('_give', '_receive');
      const bottomReceiveVal = bottomCategory[receiveKey] || 0;
      
      // PRIMARY: Top wants to GIVE → Bottom wants to RECEIVE
      if (topVal >= 0.5 || bottomReceiveVal >= 0.5) {
        primaryPotential++;
        if (topVal >= 0.5 && bottomReceiveVal >= 0.5) {
          primaryMatches++;
        }
      }
      
      // SECONDARY: Bottom wants to GIVE → Top wants to RECEIVE
      // (Less critical - Tops often don't want to receive)
      const topReceiveVal = topCategory[receiveKey] || 0;
      if (bottomVal >= 0.5 || topReceiveVal >= 0.5) {
        secondaryPotential++;
        if (bottomVal >= 0.5 && topReceiveVal >= 0.5) {
          secondaryMatches++;
        }
        // If Bottom wants to give but Top doesn't want to receive, give partial credit
        // (This is okay in Top/Bottom dynamics)
        else if (bottomVal >= 0.5 && topReceiveVal < 0.5) {
          secondaryMatches += 0.5; // 50% credit for "willing but not needed"
        }
      }
    } 
    else if (!key.endsWith('_receive')) {
      // Non-directional activities
      if (topVal >= 0.5 && bottomVal >= 0.5) {
        nonDirectionalMatches++;
      }
      if (topVal >= 0.5 || bottomVal >= 0.5) {
        nonDirectionalPotential++;
      }
    }
  });

  // Weight primary axis more heavily (80%) than secondary (20%)
  const totalMatches = (primaryMatches * 0.8) + (secondaryMatches * 0.2) + nonDirectionalMatches;
  const totalPotential = (primaryPotential * 0.8) + (secondaryPotential * 0.2) + nonDirectionalPotential;

  if (totalPotential === 0) return 0;
  return totalMatches / totalPotential;
}

/**
 * NEW v0.5: Inverse Jaccard for same-pole pairs (Top/Top or Bottom/Bottom)
 * For these pairs, matching on giving/receiving is actually INCOMPATIBLE
 * They both want to give, but no one wants to receive
 */
export function calculateSamePoleJaccard(
  categoryA: Record<string, number>,
  categoryB: Record<string, number>
): number {
  const keys = Object.keys(categoryA);
  let compatibleInteractions = 0;
  let totalPossibleInteractions = 0;

  keys.forEach(key => {
    const valA = categoryA[key] || 0;
    const valB = categoryB[key] || 0;

    if (key.endsWith('_give')) {
      const receiveKey = key.replace('_give', '_receive');
      const receiveA = categoryA[receiveKey] || 0;
      const receiveB = categoryB[receiveKey] || 0;
      
      // For same-pole pairs, we need OPPOSITE preferences on give/receive
      // But since they're both the same pole, this rarely happens
      
      if (valA >= 0.5 || valB >= 0.5) {
        totalPossibleInteractions++;
        
        // The only way this works is if one is versatile (wants to give AND receive)
        // Give partial credit for this flexibility
        if ((valA >= 0.5 && receiveA >= 0.5) && (valB >= 0.5 && receiveB < 0.5)) {
          compatibleInteractions += 0.3; // A is versatile, B only gives
        } else if ((valA >= 0.5 && receiveA < 0.5) && (valB >= 0.5 && receiveB >= 0.5)) {
          compatibleInteractions += 0.3; // B is versatile, A only gives
        } else if ((valA >= 0.5 && receiveA >= 0.5) && (valB >= 0.5 && receiveB >= 0.5)) {
          compatibleInteractions += 0.5; // Both are versatile - better!
        }
        // If both only want to give and not receive = 0 compatibility (default)
      }
    }
    else if (!key.endsWith('_receive')) {
      // Non-directional activities can still work for same-pole pairs
      if (valA >= 0.5 && valB >= 0.5) {
        compatibleInteractions++;
      }
      if (valA >= 0.5 || valB >= 0.5) {
        totalPossibleInteractions++;
      }
    }
  });

  if (totalPossibleInteractions === 0) return 0;
  return compatibleInteractions / totalPossibleInteractions;
}

/**
 * CORRECTED v0.5: Activity overlap with full Top/Bottom dynamics AND same-pole awareness
 */
export function calculateActivityOverlap(
  powerA: PowerDynamic,
  powerB: PowerDynamic,
  activitiesA: ActivityMap,
  activitiesB: ActivityMap
): number {
  
  const isTopBottomPair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  );

  const isSamePolePair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Top') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Bottom')
  );

  const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>;
  const scores: number[] = [];

  categories.forEach(category => {
    let score: number;

    const hasDirectionalActivities = [
      'physical_touch', 'oral', 'anal', 'power_exchange', 'display_performance'
    ].includes(category);

    if (isTopBottomPair && hasDirectionalActivities) {
      // Use asymmetric directional Jaccard for complementary pairs
      const topActivities = powerA.orientation === 'Top' ? activitiesA : activitiesB;
      const bottomActivities = powerA.orientation === 'Bottom' ? activitiesA : activitiesB;

      score = calculateAsymmetricDirectionalJaccard(
        topActivities[category],
        bottomActivities[category]
      );
    } 
    else if (isSamePolePair && hasDirectionalActivities) {
      // NEW v0.5: Use inverse Jaccard for same-pole pairs
      score = calculateSamePoleJaccard(
        activitiesA[category],
        activitiesB[category]
      );
    }
    else {
      // Use standard Jaccard for Switch/Switch or non-directional categories
      score = calculateStandardJaccard(
        activitiesA[category],
        activitiesB[category]
      );
    }

    scores.push(score);
  });

  return scores.reduce((sum, val) => sum + val, 0) / scores.length;
}

/**
 * FINAL v0.5: Overall compatibility calculation with all corrections
 */
export function calculateCompatibility(
  powerA: PowerDynamic,
  powerB: PowerDynamic,
  domainsA: DomainScores,
  domainsB: DomainScores,
  activitiesA: ActivityMap,
  activitiesB: ActivityMap,
  truthOverlap: number = 1.0,
  boundaryConflicts: number = 0,
  weights = { power: 0.15, domain: 0.25, activity: 0.40, truth: 0.20 }
): { score: number; breakdown: any } {
  
  const powerComp = calculatePowerComplement(powerA, powerB);
  const domainSim = calculateDomainSimilarity(domainsA, domainsB, powerA, powerB);
  const activityOverlap = calculateActivityOverlap(powerA, powerB, activitiesA, activitiesB);

  let score = (
    weights.power * powerComp +
    weights.domain * domainSim +
    weights.activity * activityOverlap +
    weights.truth * truthOverlap
  );

  const boundaryPenalty = boundaryConflicts * 0.2;
  score = Math.max(0, score - boundaryPenalty);

  return {
    score: Math.round(score * 100),
    breakdown: {
      power_complement: Math.round(powerComp * 100),
      domain_similarity: Math.round(domainSim * 100),
      activity_overlap: Math.round(activityOverlap * 100),
      truth_overlap: Math.round(truthOverlap * 100),
      boundary_conflicts: boundaryConflicts
    }
  };
}

// ============================================
// TESTING WITH THREE SCENARIOS
// ============================================

// USER 1: Top (Big Black Haiti)
const user1_power: PowerDynamic = {
  orientation: 'Top',
  confidence: 1.0,
  top_score: 100,
  bottom_score: 0
};

const user1_domains: DomainScores = {
  sensation: 61,
  connection: 82,
  power: 60,
  exploration: 60,
  verbal: 70
};

const user1_activities: ActivityMap = {
  physical_touch: {
    massage_receive: 1, massage_give: 1,
    hair_pull_gentle_receive: 0, hair_pull_gentle_give: 1,
    biting_moderate_receive: 0.5, biting_moderate_give: 1,
    spanking_moderate_receive: 0, spanking_moderate_give: 1,
    hands_genitals_receive: 1, hands_genitals_give: 1,
    spanking_hard_receive: 0, spanking_hard_give: 1,
    slapping_receive: 0, slapping_give: 1,
    choking_receive: 0, choking_give: 1,
    spitting_receive: 0.5, spitting_give: 1,
    watersports_receive: 0.5, watersports_give: 1
  },
  oral: {
    oral_sex_receive: 1, oral_sex_give: 1,
    oral_body_receive: 1, oral_body_give: 1
  },
  anal: {
    anal_fingers_toys_receive: 0, anal_fingers_toys_give: 1,
    rimming_receive: 1, rimming_give: 1
  },
  power_exchange: {
    restraints_receive: 0, restraints_give: 1,
    blindfold_receive: 0, blindfold_give: 1,
    orgasm_control_receive: 1, orgasm_control_give: 1,
    protocols_follow: 0, protocols_give: 1
  },
  verbal_roleplay: {
    dirty_talk: 1, moaning: 1, roleplay: 0.5, commands: 1, begging: 0
  },
  display_performance: {
    stripping_me: 0, watching_strip: 1,
    watched_solo_pleasure: 0.5, watching_solo_pleasure: 1,
    posing: 0, dancing: 0, revealing_clothing: 0
  }
};

// USER 2: Bottom (Quick Check)
const user2_power: PowerDynamic = {
  orientation: 'Bottom',
  confidence: 1.0,
  top_score: 0,
  bottom_score: 100
};

const user2_domains: DomainScores = {
  sensation: 64,
  connection: 100,
  power: 70,
  exploration: 95,
  verbal: 100
};

const user2_activities: ActivityMap = {
  physical_touch: {
    massage_receive: 1, massage_give: 1,
    hair_pull_gentle_receive: 1, hair_pull_gentle_give: 0,
    biting_moderate_receive: 1, biting_moderate_give: 0,
    spanking_moderate_receive: 1, spanking_moderate_give: 0,
    hands_genitals_receive: 1, hands_genitals_give: 1,
    spanking_hard_receive: 1, spanking_hard_give: 0,
    slapping_receive: 1, slapping_give: 0,
    choking_receive: 1, choking_give: 0,
    spitting_receive: 1, spitting_give: 1,
    watersports_receive: 1, watersports_give: 1
  },
  oral: {
    oral_sex_receive: 1, oral_sex_give: 1,
    oral_body_receive: 1, oral_body_give: 1
  },
  anal: {
    anal_fingers_toys_receive: 1, anal_fingers_toys_give: 1,
    rimming_receive: 1, rimming_give: 1
  },
  power_exchange: {
    restraints_receive: 1, restraints_give: 0,
    blindfold_receive: 1, blindfold_give: 0,
    orgasm_control_receive: 1, orgasm_control_give: 1,
    protocols_follow: 1, protocols_give: 0
  },
  verbal_roleplay: {
    dirty_talk: 1, moaning: 1, roleplay: 1, commands: 1, begging: 1
  },
  display_performance: {
    stripping_me: 1, watching_strip: 0.5,
    watched_solo_pleasure: 1, watching_solo_pleasure: 1,
    posing: 1, dancing: 1, revealing_clothing: 1
  }
};

// USER 3: Top (Male Test 2) - mirror of User 1
const user3_power: PowerDynamic = {
  orientation: 'Top',
  confidence: 1.0,
  top_score: 100,
  bottom_score: 0
};

const user3_domains: DomainScores = {
  sensation: 57,
  connection: 77,
  power: 60,
  exploration: 65,
  verbal: 90
};

const user3_activities: ActivityMap = {
  physical_touch: {
    massage_receive: 1, massage_give: 1,
    hair_pull_gentle_receive: 0, hair_pull_gentle_give: 1,
    biting_moderate_receive: 0, biting_moderate_give: 1,
    spanking_moderate_receive: 0, spanking_moderate_give: 1,
    hands_genitals_receive: 1, hands_genitals_give: 1,
    spanking_hard_receive: 0, spanking_hard_give: 1,
    slapping_receive: 0, slapping_give: 1,
    choking_receive: 0, choking_give: 1,
    spitting_receive: 0.5, spitting_give: 1,
    watersports_receive: 0.5, watersports_give: 1
  },
  oral: {
    oral_sex_receive: 1, oral_sex_give: 1,
    oral_body_receive: 1, oral_body_give: 1
  },
  anal: {
    anal_fingers_toys_receive: 0, anal_fingers_toys_give: 1,
    rimming_receive: 1, rimming_give: 1
  },
  power_exchange: {
    restraints_receive: 0, restraints_give: 1,
    blindfold_receive: 0, blindfold_give: 1,
    orgasm_control_receive: 0.5, orgasm_control_give: 1,
    protocols_follow: 0, protocols_give: 1
  },
  verbal_roleplay: {
    dirty_talk: 1, moaning: 1, roleplay: 1, commands: 1, begging: 0.5
  },
  display_performance: {
    stripping_me: 0, watching_strip: 1,
    watched_solo_pleasure: 0.5, watching_solo_pleasure: 1,
    posing: 0, dancing: 0, revealing_clothing: 0
  }
};

console.log("=".repeat(70));
console.log("COMPATIBILITY v0.5 - ALL PAIR TYPES TEST");
console.log("=".repeat(70));

// TEST 1: Top/Bottom (Should be 90%)
console.log("\n📊 TEST 1: Top (User 1) + Bottom (User 2)");
console.log("Expected: ~90% compatibility (complementary pair)");
const result1 = calculateCompatibility(
  user1_power, user2_power,
  user1_domains, user2_domains,
  user1_activities, user2_activities,
  1.0, 0
);
console.log(`  Power Complement:  ${result1.breakdown.power_complement}%`);
console.log(`  Domain Similarity: ${result1.breakdown.domain_similarity}%`);
console.log(`  Activity Overlap:  ${result1.breakdown.activity_overlap}%`);
console.log(`  Truth Overlap:     ${result1.breakdown.truth_overlap}%`);
console.log(`  TOTAL:             ${result1.score}%`);
console.log(`  Status: ${result1.score >= 85 ? '✅ PASS' : '❌ FAIL'}`);

// TEST 2: Top/Top (Should be 35-45%)
console.log("\n📊 TEST 2: Top (User 1) + Top (User 3)");
console.log("Expected: ~35-45% compatibility (same-pole incompatible)");
const result2 = calculateCompatibility(
  user1_power, user3_power,
  user1_domains, user3_domains,
  user1_activities, user3_activities,
  1.0, 0
);
console.log(`  Power Complement:  ${result2.breakdown.power_complement}%`);
console.log(`  Domain Similarity: ${result2.breakdown.domain_similarity}%`);
console.log(`  Activity Overlap:  ${result2.breakdown.activity_overlap}%`);
console.log(`  Truth Overlap:     ${result2.breakdown.truth_overlap}%`);
console.log(`  TOTAL:             ${result2.score}%`);
console.log(`  Status: ${result2.score >= 35 && result2.score <= 50 ? '✅ PASS' : '❌ FAIL'}`);

// TEST 3: Bottom/Top (reverse of test 1, should also be ~90%)
console.log("\n📊 TEST 3: Bottom (User 2) + Top (User 1)");
console.log("Expected: ~90% compatibility (reverse order, same result)");
const result3 = calculateCompatibility(
  user2_power, user1_power,
  user2_domains, user1_domains,
  user2_activities, user1_activities,
  1.0, 0
);
console.log(`  Power Complement:  ${result3.breakdown.power_complement}%`);
console.log(`  Domain Similarity: ${result3.breakdown.domain_similarity}%`);
console.log(`  Activity Overlap:  ${result3.breakdown.activity_overlap}%`);
console.log(`  Truth Overlap:     ${result3.breakdown.truth_overlap}%`);
console.log(`  TOTAL:             ${result3.score}%`);
console.log(`  Status: ${result3.score >= 85 ? '✅ PASS' : '❌ FAIL'}`);

console.log("\n" + "=".repeat(70));
console.log("TEST SUMMARY");
console.log("=".repeat(70));
console.log(`Top/Bottom compatibility: ${result1.score}% (expected 85-95%)`);
console.log(`Top/Top compatibility:    ${result2.score}% (expected 35-50%)`);
console.log(`Bottom/Top compatibility: ${result3.score}% (expected 85-95%)`);
console.log("=".repeat(70));

console.log("\n✅ v0.5 FEATURES:");
console.log("   ✓ Asymmetric directional Jaccard for Top/Bottom pairs");
console.log("   ✓ Complementary-aware domain similarity");
console.log("   ✓ Same-pole incompatibility recognition (NEW!)");
console.log("   ✓ Proper handling of all power dynamic combinations");
