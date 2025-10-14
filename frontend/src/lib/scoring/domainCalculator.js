// Domain calculator for v0.3.1 presentation (derive directly from traits)

function toPercentage(value) {
  if (value === undefined || value === null || Number.isNaN(value)) return 50;
  const n = Number(value);
  const pct = n <= 1 ? n * 100 : n; // support 0..1 or 0..100 traits
  if (!Number.isFinite(pct)) return 50;
  return Math.max(0, Math.min(100, pct));
}

function mean(values) {
  if (!values || values.length === 0) return 50;
  const nums = values.map((v) => toPercentage(v));
  const sum = nums.reduce((a, b) => a + b, 0);
  return Math.max(0, Math.min(100, sum / nums.length));
}

export function computeDomainsFromTraits(traits = {}) {
  const powerTop = toPercentage(traits.POWER_TOP);
  const powerBottom = toPercentage(traits.POWER_BOTTOM);

  const connection = mean([traits.ROMANTIC, traits.SENSUAL]);

  const sensory = Math.max(
    0,
    Math.min(
      100,
      0.4 * toPercentage(traits.IMPACT) +
        0.4 * toPercentage(traits.BONDAGE) +
        0.2 * toPercentage(traits.TOYS)
    )
  );

  const exploration = mean([
    traits.NOVELTY,
    traits.EXHIBITION,
    traits.VOYEUR,
    traits.PUBLIC_EDGE,
  ]);

  const structure = toPercentage(traits.ROLEPLAY);

  return {
    powerTop,
    powerBottom,
    connection,
    sensory,
    exploration,
    structure,
  };
}


