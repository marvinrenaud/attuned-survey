/**
 * Compatibility Mapper (v0.4)
 * Implements v0.4 compatibility algorithm between two profiles
 */

import { calculatePowerComplement } from '../scoring/powerCalculator.js';
import { calculateDomainSimilarity } from '../scoring/domainCalculator.js';
import { calculateTruthOverlap } from '../scoring/truthTopicsCalculator.js';

/**
 * Standard symmetric Jaccard coefficient
 * Used for Switch/Switch pairs, same-pole pairs, and non-directional activities
 * @param {Object} categoryA - First person's category activities
 * @param {Object} categoryB - Second person's category activities
 * @returns {number} - Jaccard score 0-1
 */
function calculateStandardJaccard(categoryA, categoryB) {
  const keys = Object.keys(categoryA);
  let mutualYes = 0;
  let atLeastOneYes = 0;

  keys.forEach(key => {
    const valA = categoryA[key] || 0;
    const valB = categoryB[key] || 0;

    // Both interested (Y or M = >= 0.5)
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
 * Asymmetric directional Jaccard for Top/Bottom pairs
 * Recognizes that Top/Bottom dynamics are inherently asymmetric
 * Primary axis: Does Top want to GIVE what Bottom wants to RECEIVE?
 * Secondary axis: Does Bottom want to GIVE what Top wants to RECEIVE?
 * @param {Object} topCategory - Top person's category activities
 * @param {Object} bottomCategory - Bottom person's category activities
 * @returns {number} - Jaccard score 0-1
 */
function calculateAsymmetricDirectionalJaccard(topCategory, bottomCategory) {
  // Validate inputs
  if (!topCategory || !bottomCategory || typeof topCategory !== 'object' || typeof bottomCategory !== 'object') {
    console.error('calculateAsymmetricDirectionalJaccard: Invalid input - expected objects, got:', typeof topCategory, typeof bottomCategory);
    return 0;
  }

  const keys = Object.keys(topCategory);
  
  let primaryMatches = 0;          // Top gives what Bottom wants to receive
  let primaryPotential = 0;         // Total opportunities for Top to give
  let secondaryMatches = 0;         // Bottom gives what Top wants to receive
  let secondaryPotential = 0;       // Total opportunities for Bottom to give
  let nonDirectionalMatches = 0;
  let nonDirectionalPotential = 0;

  keys.forEach(key => {
    const topVal = topCategory[key] || 0;
    const bottomVal = bottomCategory[key] || 0;

    if (key.endsWith('_give')) {
      const receiveKey = key.replace('_give', '_receive');
      const bottomReceiveVal = bottomCategory[receiveKey] || 0;
      
      // PRIMARY AXIS: Top wants to GIVE → Bottom wants to RECEIVE
      if (topVal >= 0.5 || bottomReceiveVal >= 0.5) {
        primaryPotential++;
        if (topVal >= 0.5 && bottomReceiveVal >= 0.5) {
          primaryMatches++;
        }
      }
      
      // SECONDARY AXIS: Bottom wants to GIVE → Top wants to RECEIVE
      // (Less critical - Tops often don't want to receive)
      const topReceiveVal = topCategory[receiveKey] || 0;
      if (bottomVal >= 0.5 || topReceiveVal >= 0.5) {
        secondaryPotential++;
        if (bottomVal >= 0.5 && topReceiveVal >= 0.5) {
          secondaryMatches++;
        }
        // If Bottom wants to give but Top doesn't want to receive, give partial credit
        // (This is okay in Top/Bottom dynamics - Tops often don't want to receive)
        else if (bottomVal >= 0.5 && topReceiveVal < 0.5) {
          secondaryMatches += 0.5; // 50% credit for "willing but not needed"
        }
      }
    } 
    else if (!key.endsWith('_receive')) {
      // Non-directional activities (e.g., dirty_talk, moaning, roleplay)
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
 * Calculate activity-level overlap with power-aware Jaccard selection
 * Uses asymmetric directional Jaccard for Top/Bottom pairs, standard for others
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @param {Object} powerA - First person's power dynamic
 * @param {Object} powerB - Second person's power dynamic
 * @returns {number} - Overlap score 0-1
 */
function calculateActivityOverlap(activitiesA, activitiesB, powerA, powerB) {
  const isTopBottomPair = (
    (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
    (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
  );

  const categories = ['physical_touch', 'oral', 'anal', 'power_exchange', 'verbal_roleplay', 'display_performance'];
  const scores = [];

  categories.forEach(category => {
    if (!activitiesA[category] || !activitiesB[category]) {
      return; // Skip missing categories
    }

    let score;

    // Determine if this category has directional activities
    const hasDirectionalActivities = [
      'physical_touch', 'oral', 'anal', 'power_exchange', 'display_performance'
    ].includes(category);

    if (isTopBottomPair && hasDirectionalActivities) {
      // Use asymmetric directional Jaccard
      const topActivities = powerA.orientation === 'Top' ? activitiesA[category] : activitiesB[category];
      const bottomActivities = powerA.orientation === 'Bottom' ? activitiesA[category] : activitiesB[category];

      score = calculateAsymmetricDirectionalJaccard(topActivities, bottomActivities);
    } else {
      // Use standard Jaccard for Switch/Switch, same-pole pairs, or non-directional categories
      score = calculateStandardJaccard(activitiesA[category], activitiesB[category]);
    }

    scores.push(score);
  });

  if (scores.length === 0) return 0;
  return scores.reduce((sum, val) => sum + val, 0) / scores.length;
}

/**
 * Check for boundary conflicts between players
 * @param {Object} playerA - First player's profile
 * @param {Object} playerB - Second player's profile
 * @returns {Array} - Array of boundary conflicts
 */
function checkBoundaryConflicts(playerA, playerB) {
  const conflicts = [];

  // Boundary to activity mapping
  const boundaryMap = {
    'impact_play': [
      'spanking_moderate_give', 'spanking_moderate_receive',
      'spanking_hard_give', 'spanking_hard_receive',
      'slapping_give', 'slapping_receive',
      'biting_moderate_give', 'biting_moderate_receive'
    ],
    'restraints_bondage': [
      'restraints_give', 'restraints_receive',
      'blindfold_give', 'blindfold_receive'
    ],
    'breath_play': [
      'choking_give', 'choking_receive'
    ],
    'anal_activities': [
      'anal_fingers_toys_give', 'anal_fingers_toys_receive',
      'rimming_give', 'rimming_receive'
    ],
    'degradation_humiliation': [],  // FIXED: Begging is NOT degradation - it's verbal power exchange
    'roleplay': ['roleplay', 'protocols_follow', 'protocols_give'],
    'watersports': ['watersports_give', 'watersports_receive'],
    'toys_props': []  // Would need separate tracking
  };

  // Check A's boundaries vs B's interests
  const limitsA = playerA.boundaries?.hard_limits || [];
  limitsA.forEach(limit => {
    const activityKeys = boundaryMap[limit] || [];
    activityKeys.forEach(actKey => {
      // Search all activity categories in B's profile
      Object.values(playerB.activities || {}).forEach(category => {
        if (category[actKey] !== undefined && category[actKey] >= 0.5) {
          conflicts.push({
            player: playerA.user_id,
            boundary: limit,
            conflicting_activity: actKey
          });
        }
      });
    });
  });

  // Check B's boundaries vs A's interests
  const limitsB = playerB.boundaries?.hard_limits || [];
  limitsB.forEach(limit => {
    const activityKeys = boundaryMap[limit] || [];
    activityKeys.forEach(actKey => {
      Object.values(playerA.activities || {}).forEach(category => {
        if (category[actKey] !== undefined && category[actKey] >= 0.5) {
          conflicts.push({
            player: playerB.user_id,
            boundary: limit,
            conflicting_activity: actKey
          });
        }
      });
    });
  });

  return conflicts;
}

/**
 * Identify activities both players are open to
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {Object} - Mutual activities by category
 */
function identifyMutualActivities(activitiesA, activitiesB) {
  const result = {};
  const categories = ['physical_touch', 'oral', 'anal', 'power_exchange', 'verbal_roleplay', 'display_performance'];

  categories.forEach(category => {
    const mutualKeys = [];
    const catA = activitiesA[category] || {};
    const catB = activitiesB[category] || {};
    const keys = Object.keys(catA);

    keys.forEach(key => {
      const valA = catA[key] || 0;
      const valB = catB[key] || 0;

      // Both Y or M (>= 0.5)
      if (valA >= 0.5 && valB >= 0.5) {
        mutualKeys.push(key);
      }
    });

    result[category] = mutualKeys;
  });

  return result;
}

/**
 * Identify growth opportunities (one Y, one M)
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {Array} - Growth opportunities
 */
function identifyGrowthOpportunities(activitiesA, activitiesB) {
  const opportunities = [];
  const categories = ['physical_touch', 'oral', 'anal', 'power_exchange', 'verbal_roleplay', 'display_performance'];

  categories.forEach(category => {
    const catA = activitiesA[category] || {};
    const catB = activitiesB[category] || {};
    const keys = Object.keys(catA);

    keys.forEach(key => {
      const valA = catA[key] || 0;
      const valB = catB[key] || 0;

      if (
        (valA === 1.0 && valB === 0.5) ||
        (valA === 0.5 && valB === 1.0)
      ) {
        opportunities.push({
          activity: `${category}.${key}`,
          playerA: valA === 1.0 ? 'yes' : 'maybe',
          playerB: valB === 1.0 ? 'yes' : 'maybe'
        });
      }
    });
  });

  return opportunities;
}

/**
 * Interpret compatibility score
 * @param {number} score - Score 0-100
 * @returns {string} - Interpretation
 */
function interpretCompatibility(score) {
  if (score >= 85) return 'Exceptional compatibility';
  if (score >= 70) return 'High compatibility';
  if (score >= 55) return 'Moderate compatibility';
  if (score >= 40) return 'Lower compatibility';
  return 'Challenging compatibility';
}

/**
 * Calculate compatibility between two players (DETAILED VERSION)
 * Implements v0.4 algorithm with weighted factors and asymmetric Top/Bottom matching
 * @param {Object} powerA - First player's power dynamic
 * @param {Object} powerB - Second player's power dynamic
 * @param {Object} domainsA - First player's domain scores
 * @param {Object} domainsB - Second player's domain scores
 * @param {Object} activitiesA - First player's activities
 * @param {Object} activitiesB - Second player's activities
 * @param {Object} truthTopicsA - First player's truth topics
 * @param {Object} truthTopicsB - Second player's truth topics
 * @param {Object} boundariesA - First player's boundaries
 * @param {Object} boundariesB - Second player's boundaries
 * @param {Object} weights - Optional custom weights
 * @returns {Object} - Complete compatibility result
 */
export function calculateCompatibilityDetailed(
  powerA,
  powerB,
  domainsA,
  domainsB,
  activitiesA,
  activitiesB,
  truthTopicsA,
  truthTopicsB,
  boundariesA,
  boundariesB,
  weights = { power: 0.15, domain: 0.25, activity: 0.40, truth: 0.20 }
) {
  // 1. Power Complement (0-1)
  const powerComplement = calculatePowerComplement(powerA, powerB);

  // 2. Domain Similarity (0-1) - UPDATED: Pass power dynamics for complementary logic
  const domainSimilarity = calculateDomainSimilarity(domainsA, domainsB, powerA, powerB);

  // 3. Activity Overlap (0-1) - UPDATED: Pass power dynamics for asymmetric matching
  const activityOverlap = calculateActivityOverlap(activitiesA, activitiesB, powerA, powerB);

  // 4. Truth Overlap (0-1)
  const truthOverlap = calculateTruthOverlap(truthTopicsA, truthTopicsB);

  // 5. Boundary Conflicts
  const playerAProxy = { 
    user_id: 'playerA', 
    activities: activitiesA, 
    boundaries: boundariesA 
  };
  const playerBProxy = { 
    user_id: 'playerB', 
    activities: activitiesB, 
    boundaries: boundariesB 
  };
  const boundaryConflicts = checkBoundaryConflicts(playerAProxy, playerBProxy);

  // Debug logging
  console.log('Compatibility Calculation Debug:');
  console.log('  Power Complement:   ', powerComplement.toFixed(3), '× 0.15 =', (powerComplement * weights.power).toFixed(3));
  console.log('  Domain Similarity:  ', domainSimilarity.toFixed(3), '× 0.25 =', (domainSimilarity * weights.domain).toFixed(3));
  console.log('  Activity Overlap:   ', activityOverlap.toFixed(3), '× 0.40 =', (activityOverlap * weights.activity).toFixed(3));
  console.log('  Truth Overlap:      ', truthOverlap.toFixed(3), '× 0.20 =', (truthOverlap * weights.truth).toFixed(3));
  console.log('  Boundary Conflicts: ', boundaryConflicts.length);

  // Calculate weighted overall score
  let overallScore = (
    weights.power * powerComplement +
    weights.domain * domainSimilarity +
    weights.activity * activityOverlap +
    weights.truth * truthOverlap
  );

  // Apply boundary penalty (0.2 per conflict)
  const boundaryPenalty = boundaryConflicts.length * 0.20;
  overallScore = Math.max(0, overallScore - boundaryPenalty);
  
  console.log('  Boundary Penalty:   ', '-' + boundaryPenalty.toFixed(3));
  console.log('  Final Score:        ', overallScore.toFixed(3), '→', Math.round(overallScore * 100) + '%');

  return {
    compatibility_version: '0.4-fixed',
    overall_compatibility: {
      score: Math.round(overallScore * 100),
      interpretation: interpretCompatibility(Math.round(overallScore * 100))
    },
    breakdown: {
      power_complement: Math.round(powerComplement * 100),
      domain_similarity: Math.round(domainSimilarity * 100),
      activity_overlap: Math.round(activityOverlap * 100),
      truth_overlap: Math.round(truthOverlap * 100),
      boundary_conflicts: boundaryConflicts
    }
  };
}

/**
 * Calculate compatibility between two players (CONVENIENCE WRAPPER)
 * Extracts components from full profiles and calls detailed version
 * @param {Object} playerA - First player's complete profile
 * @param {Object} playerB - Second player's complete profile
 * @returns {Object} - Complete compatibility result
 */
export function calculateCompatibility(playerA, playerB) {
  // Extract components from profiles
  const powerA = playerA.power_dynamic;
  const powerB = playerB.power_dynamic;
  const domainsA = playerA.domain_scores;
  const domainsB = playerB.domain_scores;
  const activitiesA = playerA.activities;
  const activitiesB = playerB.activities;
  const truthTopicsA = playerA.truth_topics;
  const truthTopicsB = playerB.truth_topics;
  const boundariesA = playerA.boundaries;
  const boundariesB = playerB.boundaries;

  // Call detailed version
  const detailedResult = calculateCompatibilityDetailed(
    powerA, powerB,
    domainsA, domainsB,
    activitiesA, activitiesB,
    truthTopicsA, truthTopicsB,
    boundariesA, boundariesB
  );

  // Identify mutual activities and growth opportunities
  const mutualActivities = identifyMutualActivities(activitiesA, activitiesB);
  const growthOpportunities = identifyGrowthOpportunities(activitiesA, activitiesB);

  // Identify mutual truth topics
  const mutualTruthTopics = [];
  const topicKeys = ['past_experiences', 'fantasies', 'turn_ons', 'turn_offs', 'insecurities', 'boundaries', 'future_fantasies', 'feeling_desired'];
  topicKeys.forEach(key => {
    if (truthTopicsA[key] >= 0.5 && truthTopicsB[key] >= 0.5) {
      mutualTruthTopics.push(key);
    }
  });

  // Blocked activities
  const allHardLimits = [
    ...(boundariesA?.hard_limits || []),
    ...(boundariesB?.hard_limits || [])
  ];
  const uniqueLimits = Array.from(new Set(allHardLimits));

  return {
    players: [playerA.user_id, playerB.user_id],
    timestamp: new Date().toISOString(),
    ...detailedResult,
    mutual_activities: mutualActivities,
    growth_opportunities: growthOpportunities,
    mutual_truth_topics: mutualTruthTopics,
    blocked_activities: {
      reason: 'hard_boundaries',
      activities: uniqueLimits
    }
  };
}

