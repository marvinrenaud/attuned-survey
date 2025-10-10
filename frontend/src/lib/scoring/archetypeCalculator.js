/**
 * Archetype Calculator - determines user archetypes from traits
 */

/**
 * Calculate archetype scores from traits
 * @param {Record<string, number>} traits - Trait scores (0-100)
 * @param {Array} archetypeDefinitions - Archetype definitions from schema
 * @returns {Array<{id: string, name: string, score: number, desc: string}>} - Sorted by score descending
 */
export function calculateArchetypes(traits, archetypeDefinitions) {
  const archetypeScores = [];

  for (const archetype of archetypeDefinitions) {
    const { id, name, formula, desc } = archetype;
    let score = 0;

    for (const trait in formula) {
      const weight = formula[trait];
      const traitValue = traits[trait] !== undefined ? traits[trait] : 50;
      score += traitValue * weight;
    }

    archetypeScores.push({
      id,
      name,
      score: Math.max(0, score), // Clip to non-negative
      desc
    });
  }

  // Sort by score descending
  archetypeScores.sort((a, b) => b.score - a.score);

  return archetypeScores;
}

/**
 * Get top archetypes with tie-breaking
 * Returns top 1-3 archetypes depending on score proximity
 * @param {Array<{id: string, name: string, score: number}>} archetypes - Sorted archetypes
 * @returns {Array<{id: string, name: string, score: number}>} - Top archetype(s)
 */
export function getTopArchetypes(archetypes) {
  if (archetypes.length === 0) return [];

  const top = [archetypes[0]];
  const topScore = archetypes[0].score;

  // Include ties within 5% of top score
  const tieThreshold = topScore * 0.05;

  for (let i = 1; i < Math.min(3, archetypes.length); i++) {
    if (topScore - archetypes[i].score <= tieThreshold) {
      top.push(archetypes[i]);
    } else {
      break;
    }
  }

  return top;
}

/**
 * Check if "Balanced" archetype should be displayed
 * Balanced is shown when it's in top 3 AND dials show uniformity
 * @param {Array} topArchetypes
 * @param {boolean} isBalancedProfile
 * @returns {boolean}
 */
export function shouldShowBalanced(topArchetypes, isBalancedProfile) {
  const hasBalanced = topArchetypes.some(a => a.id === 'BALANCED');
  return hasBalanced && isBalancedProfile;
}

