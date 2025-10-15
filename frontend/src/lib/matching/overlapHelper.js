/**
 * Overlap Helper (v0.4)
 * Helper functions for calculating activity overlap and compatibility
 */

/**
 * Calculate Jaccard coefficient for a category
 * @param {Object} categoryA - First person's category
 * @param {Object} categoryB - Second person's category
 * @returns {number} - Jaccard coefficient 0-1
 */
export function calculateJaccard(categoryA, categoryB) {
  const keys = new Set([
    ...Object.keys(categoryA || {}),
    ...Object.keys(categoryB || {})
  ]);

  let intersection = 0;
  let union = 0;

  keys.forEach(key => {
    const valA = (categoryA && categoryA[key]) || 0;
    const valB = (categoryB && categoryB[key]) || 0;

    // Both interested (>= 0.5)
    if (valA >= 0.5 && valB >= 0.5) {
      intersection++;
    }

    // At least one interested
    if (valA >= 0.5 || valB >= 0.5) {
      union++;
    }
  });

  if (union === 0) return 0;
  return intersection / union;
}

/**
 * Calculate overall activity overlap
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {number} - Overall overlap 0-1
 */
export function calculateOverallOverlap(activitiesA, activitiesB) {
  const categories = [
    'physical_touch',
    'oral',
    'anal',
    'power_exchange',
    'verbal_roleplay',
    'display_performance'
  ];

  const jaccards = categories.map(cat => 
    calculateJaccard(activitiesA[cat], activitiesB[cat])
  );

  const sum = jaccards.reduce((a, b) => a + b, 0);
  return sum / jaccards.length;
}

/**
 * Get category-level overlap scores
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {Object} - Category scores
 */
export function getCategoryScores(activitiesA, activitiesB) {
  const categories = [
    'physical_touch',
    'oral',
    'anal',
    'power_exchange',
    'verbal_roleplay',
    'display_performance'
  ];

  const scores = {};
  categories.forEach(cat => {
    scores[cat] = calculateJaccard(
      activitiesA[cat] || {},
      activitiesB[cat] || {}
    );
  });

  return scores;
}

/**
 * Find mutual activities (both Y or M)
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {Object} - Mutual activities by category
 */
export function findMutualActivities(activitiesA, activitiesB) {
  const mutual = {};
  const categories = [
    'physical_touch',
    'oral',
    'anal',
    'power_exchange',
    'verbal_roleplay',
    'display_performance'
  ];

  categories.forEach(cat => {
    mutual[cat] = [];
    const catA = activitiesA[cat] || {};
    const catB = activitiesB[cat] || {};
    
    Object.keys(catA).forEach(key => {
      const valA = catA[key] || 0;
      const valB = catB[key] || 0;
      
      if (valA >= 0.5 && valB >= 0.5) {
        mutual[cat].push(key);
      }
    });
  });

  return mutual;
}

/**
 * Find growth opportunities (one Y, one M)
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {Array} - Growth opportunities
 */
export function findGrowthOpportunities(activitiesA, activitiesB) {
  const growth = [];
  const categories = [
    'physical_touch',
    'oral',
    'anal',
    'power_exchange',
    'verbal_roleplay',
    'display_performance'
  ];

  categories.forEach(cat => {
    const catA = activitiesA[cat] || {};
    const catB = activitiesB[cat] || {};
    
    Object.keys(catA).forEach(key => {
      const valA = catA[key] || 0;
      const valB = catB[key] || 0;
      
      // One person Y (1.0), other M (0.5)
      if ((valA === 1.0 && valB === 0.5) || (valA === 0.5 && valB === 1.0)) {
        growth.push({
          category: cat,
          activity: key,
          playerA_interest: valA === 1.0 ? 'yes' : 'maybe',
          playerB_interest: valB === 1.0 ? 'yes' : 'maybe'
        });
      }
    });
  });

  return growth;
}

/**
 * Count mutual interests
 * @param {Object} activitiesA - First person's activities
 * @param {Object} activitiesB - Second person's activities
 * @returns {Object} - Counts by category
 */
export function countMutualInterests(activitiesA, activitiesB) {
  const mutual = findMutualActivities(activitiesA, activitiesB);
  const counts = {};
  
  Object.keys(mutual).forEach(cat => {
    counts[cat] = mutual[cat].length;
  });
  
  counts.total = Object.values(counts).reduce((a, b) => a + b, 0);
  
  return counts;
}

/**
 * Compute overall match (legacy compatibility for existing code)
 * @param {Object} params - Parameters
 * @returns {Object} - Match result
 */
export function computeOverallMatch(params) {
  const { activitiesA, activitiesB, answersA, answersB } = params;
  
  // If we have full activities objects, use them
  if (activitiesA && activitiesB) {
    const catScores = getCategoryScores(activitiesA, activitiesB);
    const overallScore = calculateOverallOverlap(activitiesA, activitiesB);
    
    return {
      score: Math.round(overallScore * 100),
      catScores,
      mutual: findMutualActivities(activitiesA, activitiesB),
      growth: findGrowthOpportunities(activitiesA, activitiesB)
    };
  }
  
  // Fallback: construct activities from raw answers if needed
  // This is for backward compatibility
  return {
    score: 50,
    catScores: {},
    mutual: {},
    growth: []
  };
}

// Categories that are excluded from mean calculations
// (for backward compatibility with existing code)
export const EXCLUDED_FROM_MEAN = new Set([]);
