// intimacai_scoring_v0.4.ts
// Simplified domain-based scoring with streamlined arousal integration

export type ArousalFactors = {
  SE: number;          // Sexual Excitation (0-1)
  SIS_P: number;       // Inhibition - Performance (0-1)
  SIS_C: number;       // Inhibition - Consequence (0-1)
};

export type PowerDynamic = {
  label: 'Top' | 'Bottom' | 'Switch' | 'Versatile/Undefined';
  confidence: number;  // 0-1
  top_score: number;   // 0-100
  bottom_score: number; // 0-100
};

export type DomainScores = {
  sensation: number;    // 0-100
  connection: number;   // 0-100
  power: number;        // 0-100
  exploration: number;  // 0-100
  verbal: number;       // 0-100
};

export type ActivityMap = {
  physical_touch: Record<string, number>;
  oral: Record<string, number>;
  anal: Record<string, number>;
  power_exchange: Record<string, number>;
  verbal_roleplay: Record<string, number>;
  display_performance: Record<string, number>;
};

export type TruthTopics = Record<string, number> & {
  openness_score: number;
};

export type Boundaries = {
  hard_limits: string[];
  additional_notes: string;
};

export type ActivityTags = {
  open_to_gentle: boolean;
  open_to_moderate: boolean;
  open_to_intense: boolean;
  open_to_oral: boolean;
  open_to_anal: boolean;
  open_to_restraints: boolean;
  open_to_orgasm_control: boolean;
  open_to_roleplay: boolean;
  open_to_display: boolean;
  open_to_group: boolean;
};

export type IntimacyProfile = {
  user_id: string;
  profile_version: string;
  timestamp: string;
  arousal_propensity: ArousalFactors & {
    interpretation: {
      se: InterpretationBand;
      sis_p: InterpretationBand;
      sis_c: InterpretationBand;
    };
  };
  power_dynamic: PowerDynamic & {
    interpretation: string;
  };
  domain_scores: DomainScores;
  activities: ActivityMap;
  truth_topics: TruthTopics;
  boundaries: Boundaries;
  activity_tags: ActivityTags;
};

type InterpretationBand = 'Low' | 'Moderate-Low' | 'Moderate-High' | 'High';

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const mean = (arr: number[]) => arr.length === 0 ? 0 : arr.reduce((sum, v) => sum + v, 0) / arr.length;

/**
 * Calculate arousal propensity from Section A (Q1-Q12)
 * SE: Q1-Q4, SIS_P: Q5-Q8, SIS_C: Q9-Q12
 */
export function computeArousalPropensity(responses: number[]): ArousalFactors & { interpretation: any } {
  // SE items (Q1-Q4): indices 0-3
  const se_items = responses.slice(0, 4);
  const se_raw = mean(se_items);
  const se_normalized = clamp01((se_raw - 1) / 6);

  // SIS-P items (Q5-Q8): indices 4-7
  const sis_p_items = responses.slice(4, 8);
  const sis_p_raw = mean(sis_p_items);
  const sis_p_normalized = clamp01((sis_p_raw - 1) / 6);

  // SIS-C items (Q9-Q12): indices 8-12
  const sis_c_items = responses.slice(8, 12);
  const sis_c_raw = mean(sis_c_items);
  const sis_c_normalized = clamp01((sis_c_raw - 1) / 6);

  const interpretBand = (score: number): InterpretationBand => {
    if (score <= 0.30) return 'Low';
    if (score <= 0.55) return 'Moderate-Low';
    if (score <= 0.75) return 'Moderate-High';
    return 'High';
  };

  return {
    SE: Math.round(se_normalized * 100) / 100,
    SIS_P: Math.round(sis_p_normalized * 100) / 100,
    SIS_C: Math.round(sis_c_normalized * 100) / 100,
    interpretation: {
      se: interpretBand(se_normalized),
      sis_p: interpretBand(sis_p_normalized),
      sis_c: interpretBand(sis_c_normalized)
    }
  };
}

/**
 * Calculate power dynamic from Section A (Q13-Q16)
 * Top items: Q13, Q15
 * Bottom items: Q14, Q16
 */
export function computePowerDynamic(
  responses: number[],
  params = { theta_floor: 30, delta_band: 15 }
): PowerDynamic & { interpretation: string } {
  // Top items: indices 12, 14 (Q13, Q15 in 0-indexed array)
  const top_items = [responses[12], responses[14]];
  const top_raw = mean(top_items);
  const top_score = ((top_raw - 1) / 6) * 100;

  // Bottom items: indices 13, 15 (Q14, Q16)
  const bottom_items = [responses[13], responses[15]];
  const bottom_raw = mean(bottom_items);
  const bottom_score = ((bottom_raw - 1) / 6) * 100;

  let label: PowerDynamic['label'];
  let confidence: number;
  let interpretation: string;

  if (top_score < params.theta_floor && bottom_score < params.theta_floor) {
    label = 'Versatile/Undefined';
    confidence = Math.max(top_score, bottom_score) / 100;
    interpretation = 'Low engagement - still exploring preferences';
  } else if (
    Math.abs(top_score - bottom_score) <= params.delta_band &&
    Math.min(top_score, bottom_score) >= params.theta_floor
  ) {
    label = 'Switch';
    confidence = Math.min(top_score, bottom_score) / 100;
    interpretation = interpretConfidence(confidence) + ' Switch';
  } else if (top_score > bottom_score) {
    label = 'Top';
    confidence = (top_score / 100) * (1 - 0.3 * (bottom_score / 100));
    interpretation = interpretConfidence(confidence) + ' Top';
  } else {
    label = 'Bottom';
    confidence = (bottom_score / 100) * (1 - 0.3 * (top_score / 100));
    interpretation = interpretConfidence(confidence) + ' Bottom';
  }

  return {
    label,
    confidence: Math.round(confidence * 100) / 100,
    top_score: Math.round(top_score),
    bottom_score: Math.round(bottom_score),
    interpretation
  };
}

function interpretConfidence(confidence: number): string {
  if (confidence <= 0.30) return 'Low confidence';
  if (confidence <= 0.60) return 'Moderate confidence';
  if (confidence <= 0.85) return 'High confidence';
  return 'Very high confidence';
}

/**
 * Convert Y/M/N responses to numeric values
 * Y = 1.0, M = 0.5, N = 0.0
 */
export function convertYMN(response: 'Y' | 'M' | 'N'): number {
  if (response === 'Y') return 1.0;
  if (response === 'M') return 0.5;
  return 0.0;
}

/**
 * Calculate domain scores from activity responses
 */
export function computeDomainScores(
  activities: ActivityMap,
  truthTopics: Record<string, number>
): DomainScores {
  // SENSATION: Physical intensity
  const sensation_items = [
    activities.physical_touch['biting_moderate_receive'],
    activities.physical_touch['biting_moderate_give'],
    activities.physical_touch['spanking_moderate_receive'],
    activities.physical_touch['spanking_moderate_give'],
    activities.physical_touch['spanking_hard_receive'],
    activities.physical_touch['spanking_hard_give'],
    activities.physical_touch['slapping_receive'],
    activities.physical_touch['slapping_give'],
    activities.physical_touch['choking_receive'],
    activities.physical_touch['choking_give'],
    activities.physical_touch['spitting_receive'],
    activities.physical_touch['spitting_give'],
    activities.physical_touch['watersports_receive'],
    activities.physical_touch['watersports_give']
  ].filter(v => v !== undefined);
  
  const sensation = Math.round(mean(sensation_items) * 100);

  // CONNECTION: Emotional intimacy
  const connection_items = [
    activities.physical_touch['massage_receive'],
    activities.physical_touch['massage_give'],
    activities.oral['oral_body_receive'],
    activities.oral['oral_body_give'],
    activities.verbal_roleplay['moaning'],
    activities.display_performance['posing'],
    activities.display_performance['revealing_clothing'],
    truthTopics['fantasies'],
    truthTopics['insecurities'],
    truthTopics['future_fantasies'],
    truthTopics['feeling_desired']
  ].filter(v => v !== undefined);
  
  const connection = Math.round(mean(connection_items) * 100);

  // POWER: Control and structure
  const power_items = [
    activities.power_exchange['restraints_receive'],
    activities.power_exchange['restraints_give'],
    activities.power_exchange['blindfold_receive'],
    activities.power_exchange['blindfold_give'],
    activities.power_exchange['orgasm_control_receive'],
    activities.power_exchange['orgasm_control_give'],
    activities.power_exchange['protocols_follow'],
    activities.power_exchange['protocols_give'],
    activities.verbal_roleplay['commands'],
    activities.verbal_roleplay['begging']
  ].filter(v => v !== undefined);
  
  const power = Math.round(mean(power_items) * 100);

  // EXPLORATION: Novelty and risk
  const exploration_items = [
    activities.verbal_roleplay['roleplay'],
    activities.display_performance['stripping_me'],
    activities.display_performance['watching_strip'],
    activities.display_performance['watched_solo_pleasure'],
    activities.display_performance['watching_solo_pleasure'],
    activities.display_performance['dancing'],
    activities.physical_touch['spitting_receive'],
    activities.physical_touch['spitting_give'],
    activities.physical_touch['watersports_receive'],
    activities.physical_touch['watersports_give']
  ].filter(v => v !== undefined);
  
  const exploration = Math.round(mean(exploration_items) * 100);

  // VERBAL: Communication
  const verbal_items = [
    activities.verbal_roleplay['dirty_talk'],
    activities.verbal_roleplay['moaning'],
    activities.verbal_roleplay['roleplay'],
    activities.verbal_roleplay['commands'],
    activities.verbal_roleplay['begging']
  ].filter(v => v !== undefined);
  
  const verbal = Math.round(mean(verbal_items) * 100);

  return {
    sensation,
    connection,
    power,
    exploration,
    verbal
  };
}

/**
 * Generate activity tags for AI engine content gating
 */
export function generateActivityTags(
  activities: ActivityMap,
  boundaries: Boundaries
): ActivityTags {
  const hasInterest = (value: number | undefined) => value !== undefined && value >= 0.5;

  const gentle = hasInterest(activities.physical_touch['massage_receive']) ||
                 hasInterest(activities.physical_touch['massage_give']);

  const moderate = hasInterest(activities.physical_touch['biting_moderate_receive']) ||
                   hasInterest(activities.physical_touch['spanking_moderate_receive']);

  const intense = hasInterest(activities.physical_touch['spanking_hard_receive']) ||
                  hasInterest(activities.physical_touch['slapping_receive']) ||
                  hasInterest(activities.physical_touch['choking_receive']) ||
                  hasInterest(activities.physical_touch['watersports_receive']);

  const oral = hasInterest(activities.oral['oral_sex_receive']) ||
               hasInterest(activities.oral['oral_sex_give']);

  const anal = hasInterest(activities.anal['anal_fingers_toys_receive']) ||
               hasInterest(activities.anal['anal_fingers_toys_give']) ||
               hasInterest(activities.anal['rimming_receive']) ||
               hasInterest(activities.anal['rimming_give']);

  const restraints = hasInterest(activities.power_exchange['restraints_receive']) ||
                     hasInterest(activities.power_exchange['restraints_give']);

  const orgasm_control = hasInterest(activities.power_exchange['orgasm_control_receive']) ||
                         hasInterest(activities.power_exchange['orgasm_control_give']);

  const roleplay = hasInterest(activities.verbal_roleplay['roleplay']);

  const display = hasInterest(activities.display_performance['stripping_me']) ||
                  hasInterest(activities.display_performance['watching_strip']) ||
                  hasInterest(activities.display_performance['watched_solo_pleasure']);

  const group = !boundaries.hard_limits.includes('multi_partner');

  return {
    open_to_gentle: gentle,
    open_to_moderate: moderate,
    open_to_intense: intense,
    open_to_oral: oral,
    open_to_anal: anal,
    open_to_restraints: restraints,
    open_to_orgasm_control: orgasm_control,
    open_to_roleplay: roleplay,
    open_to_display: display,
    open_to_group: group
  };
}

/**
 * Generate complete intimacy profile from survey responses
 */
export function generateProfile(
  userId: string,
  arousalResponses: number[],  // A1-A16 (16 items)
  activityResponses: Record<string, 'Y' | 'M' | 'N'>,  // B1-B36
  boundariesHardLimits: string[],
  boundariesNotes: string
): IntimacyProfile {
  // Calculate arousal and power
  const arousalPropensity = computeArousalPropensity(arousalResponses);
  const powerDynamic = computePowerDynamic(arousalResponses);

  // Convert activities
  const activities: ActivityMap = {
    physical_touch: {},
    oral: {},
    anal: {},
    power_exchange: {},
    verbal_roleplay: {},
    display_performance: {}
  };

  // Map B responses to activity structure
  Object.keys(activityResponses).forEach(key => {
    const value = convertYMN(activityResponses[key]);
    // Parse key to determine category and activity name
    // This would be populated based on the question bank mapping
  });

  const truthTopics: TruthTopics = {
    openness_score: 0
  };

  const boundaries: Boundaries = {
    hard_limits: boundariesHardLimits,
    additional_notes: boundariesNotes
  };

  const domainScores = computeDomainScores(activities, truthTopics);
  const activityTags = generateActivityTags(activities, boundaries);

  return {
    user_id: userId,
    profile_version: '0.4',
    timestamp: new Date().toISOString(),
    arousal_propensity: arousalPropensity,
    power_dynamic: powerDynamic,
    domain_scores: domainScores,
    activities: activities,
    truth_topics: truthTopics,
    boundaries: boundaries,
    activity_tags: activityTags
  };
}
