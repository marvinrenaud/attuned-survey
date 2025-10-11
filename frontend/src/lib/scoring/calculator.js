/**
 * IntimacAI Scoring Calculator v0.2.4.2
 * Unified scoring logic for traits and archetypes
 */

const clamp01 = (x) => Math.max(0, Math.min(1, x));

const mapLikert = (v) => {
  const n = Number(v);
  if (!Number.isFinite(n)) return 0;
  return clamp01((n - 1) / 6);
};

const mapYMN = (v) => {
  const s = (v || '').trim().toUpperCase();
  return s === 'Y' ? 1 : s === 'M' ? 0.5 : s === 'N' ? 0 : 0;
};

const mapChoose2 = (v) => {
  const s = (v || '').trim().toUpperCase();
  return s === 'A' ? 1 : s === 'B' ? -1 : 0;
};

/**
 * Compute trait scores from answers
 * @param {Object} schema - Survey schema
 * @param {Object} answers - User answers map
 * @returns {Object} Trait scores (0-1)
 */
export function computeTraits(schema, answers) {
  const vec = {};
  
  // Initialize all traits to 0
  for (const t of schema.traits) {
    vec[t.id] = 0;
  }

  // Accumulate weighted signals
  for (const it of schema.items.full) {
    if (!it.traits || it.traits.length === 0) continue;
    
    const raw = answers[it.id];
    let x = 0;
    
    if (it.type === 'likert7') {
      x = mapLikert(raw || '');
    } else if (it.type === 'ymn') {
      x = mapYMN(raw || '');
    } else if (it.type === 'choose2') {
      const z = mapChoose2(raw || '');
      // Convert z from [-1,1] to [0,1] for A direction
      x = (z + 1) / 2;
    } else {
      continue;
    }

    // Apply weighted contributions
    for (const m of it.traits) {
      vec[m.trait] = (vec[m.trait] || 0) + m.weight * x;
    }
  }

  // Normalize by max theoretical weight per trait
  const denom = {};
  for (const t of schema.traits) {
    denom[t.id] = 0;
  }
  
  for (const it of schema.items.full) {
    if (!it.traits) continue;
    const maxx = 1; // All types mapped to 0..1
    for (const m of it.traits) {
      denom[m.trait] += Math.abs(m.weight) * maxx;
    }
  }
  
  for (const t of schema.traits) {
    const d = denom[t.id] || 1e-9;
    vec[t.id] = clamp01(vec[t.id] / d);
  }
  
  return vec;
}

/**
 * Score archetypes based on trait scores
 * @param {Object} schema - Survey schema
 * @param {Object} traits - Trait scores
 * @returns {Object} Archetype scores
 */
export function scoreArchetypes(schema, traits) {
  const out = {};
  
  for (const a of schema.archetypes) {
    let s = 0;
    for (const [k, w] of Object.entries(a.formula)) {
      s += (traits[k] || 0) * w;
    }
    out[a.id] = s;
  }
  
  return out;
}

/**
 * Calculate balanced uniformity score
 * @param {Object} traits - Trait scores
 * @param {Array} keys - Trait keys to consider
 * @returns {number} Uniformity score
 */
export function balancedUniformity(traits, keys) {
  const vals = keys.map(k => traits[k] || 0);
  if (vals.length === 0) return 0;
  
  const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
  const varr = vals.reduce((a, b) => a + (b - mean) * (b - mean), 0) / vals.length;
  const std = Math.sqrt(varr);
  
  return mean - 0.75 * std;
}

/**
 * Get top N archetypes
 * @param {Object} archetypeScores - Archetype scores
 * @param {Object} schema - Survey schema
 * @param {number} n - Number of top archetypes to return
 * @returns {Array} Top N archetypes with scores
 */
export function getTopArchetypes(archetypeScores, schema, n = 3) {
  const sorted = Object.entries(archetypeScores)
    .map(([id, score]) => {
      const archetype = schema.archetypes.find(a => a.id === id);
      return {
        id,
        name: archetype?.name || id,
        score
      };
    })
    .sort((a, b) => b.score - a.score);
  
  return sorted.slice(0, n);
}

