// intimacai_scoring_v0.3.ts
// Domain-first scoring with SES/SIS modulators, exploration re-normalization, and refined Power.

export type Traits = {
  SE: number; SIS_P: number; SIS_C: number;
  NOVELTY: number; RISK: number; EXHIBITION: number; VOYEUR: number;
  ROMANTIC: number; SENSUAL: number;
  POWER_TOP: number; POWER_BOTTOM: number;
  BONDAGE: number; IMPACT: number; ROLEPLAY: number; RECORDING: number;
  PUBLIC_EDGE: number; TOYS: number;
  STRUCTURE_PREF?: number;
  AFTERCARE_REQUIRED?: number;
};

export type Boundaries = {
  impact_cap: number;
  genital_barrier: boolean;
  recording_allowed: boolean;
  safeword: boolean;
  checkins: boolean;
  red_lines: string[];
  disallow?: Partial<Record<'visual'|'novelty'|'toys'|'bondage'|'impact'|'public_edge', boolean>>;
};

export type PowerOut = {
  label: 'Top'|'Bottom'|'Switch'|'Undefined';
  confidence: number;
  top: number;
  bottom: number;
};

export type StyleOut = {
  connection: number;
  sensory: number;
  exploration: number;
  structure: number;
  subfacets: Record<'visual'|'novelty'|'toys'|'bondage'|'impact'|'public_edge', number>;
  arousal: { SE:number; SIS_P:number; SIS_C:number };
};

const clamp01 = (x:number) => Math.max(0, Math.min(1, x));
export const toPct = (x:number) => Math.round(clamp01(x)*100);

export function computePower(
  traits: Traits,
  params = { theta: 0.33, delta: 0.10, gamma: 0.15 }
): PowerOut {
  const top = clamp01(traits.POWER_TOP);
  const bottom = clamp01(traits.POWER_BOTTOM);

  if (top < params.theta && bottom < params.theta) {
    return { label: 'Undefined', confidence: 0, top, bottom };
  }
  if (top >= params.theta && bottom >= params.theta && Math.abs(top - bottom) <= params.delta) {
    return { label: 'Switch', confidence: Math.min(top, bottom), top, bottom };
  }
  if (top > bottom) {
    return { label: 'Top', confidence: clamp01(top - params.gamma * bottom), top, bottom };
  }
  return { label: 'Bottom', confidence: clamp01(bottom - params.gamma * top), top, bottom };
}

export function computeConnection(t: Traits): number {
  const romantic = clamp01(t.ROMANTIC);
  const aftercare = clamp01(t.AFTERCARE_REQUIRED ?? 0);
  const structurePref = clamp01(t.STRUCTURE_PREF ?? 0);
  const raw = 0.60*romantic + 0.20*aftercare + 0.20*structurePref;
  return clamp01(raw * (1 + 0.20*t.SE - 0.10*t.SIS_P));
}

export function computeSensory(t: Traits): number {
  const sens = clamp01(t.SENSUAL);
  return clamp01(sens * (1 + 0.10*t.SE - 0.05*t.SIS_P));
}

export function computeExploration(t: Traits, b: Boundaries): { overall:number, subs: StyleOut['subfacets'] } {
  const base = {
    visual: clamp01(0.20*t.EXHIBITION + 0.10*t.VOYEUR),
    novelty: clamp01(t.NOVELTY),
    toys: clamp01(t.TOYS),
    bondage: clamp01(t.BONDAGE),
    impact: clamp01(t.IMPACT),
    public_edge: clamp01(t.PUBLIC_EDGE),
  };
  const weights: Record<keyof typeof base, number> = {
    visual: 0.30, novelty: 0.15, toys: 0.15, bondage: 0.15, impact: 0.15, public_edge: 0.10
  };

  const allowed = (Object.keys(base) as (keyof typeof base)[]).filter(k => !(b.disallow && b.disallow[k]));
  let sum = allowed.reduce((acc, k) => acc + weights[k], 0);
  const wRenorm: Record<keyof typeof base, number> = { ...weights };
  (Object.keys(wRenorm) as (keyof typeof base)[]).forEach(k => {
    wRenorm[k] = allowed.includes(k) && sum > 0 ? weights[k] / sum : 0;
  });

  const modFactor = (1 + 0.15*t.SE - 0.25*t.SIS_C);
  const subs: Record<keyof typeof base, number> = { ...base };
  (Object.keys(subs) as (keyof typeof base)[]).forEach(k => {
    let v = subs[k] * modFactor;
    if (k === 'impact') v *= clamp01(b.impact_cap);
    subs[k] = clamp01(v);
  });

  let overall = 0;
  allowed.forEach(k => { overall += wRenorm[k] * subs[k]; });
  overall = clamp01(overall);

  return { overall, subs };
}

export function computeStructure(t: Traits): number {
  const roleplay = clamp01(t.ROLEPLAY);
  const sp = clamp01(t.STRUCTURE_PREF ?? 0);
  return clamp01(0.50*roleplay + 0.50*sp);
}

export function scoreAll(traits: Traits, bounds: Boundaries) {
  const power = computePower(traits);
  const connection = computeConnection(traits);
  const sensory = computeSensory(traits);
  const { overall: exploration, subs } = computeExploration(traits, bounds);
  const structure = computeStructure(traits);
  const arousal = { SE: toPct(traits.SE), SIS_P: toPct(traits.SIS_P), SIS_C: toPct(traits.SIS_C) };
  return {
    power,
    style: { connection, sensory, exploration, structure, subfacets: subs, arousal }
  };
}
