/**
 * Test Profiles for Compatibility Algorithm Testing
 * Real user data: BBH (Top) vs Quick Check (Bottom)
 * Expected compatibility: ~90%
 */

export const profileBBH = {
  user_id: "1760537681785-vio2041ue",
  profile_version: "0.4",
  timestamp: "2025-10-15T14:14:41.787Z",
  arousal_propensity: {
    sexual_excitation: 0.96,
    inhibition_performance: 0.17,
    inhibition_consequence: 0.04,
    interpretation: {
      se: "High",
      sis_p: "Low",
      sis_c: "Low"
    }
  },
  power_dynamic: {
    orientation: "Top",
    top_score: 100,
    bottom_score: 0,
    confidence: 1,
    interpretation: "Very high confidence Top"
  },
  domain_scores: {
    sensation: 61,
    connection: 82,
    power: 60,
    exploration: 60,
    verbal: 70
  },
  activities: {
    physical_touch: {
      massage_receive: 1,
      massage_give: 1,
      hair_pull_gentle_receive: 0,
      hair_pull_gentle_give: 1,
      biting_moderate_receive: 0.5,
      biting_moderate_give: 1,
      spanking_moderate_receive: 0,
      spanking_moderate_give: 1,
      hands_genitals_receive: 1,
      hands_genitals_give: 1,
      spanking_hard_receive: 0,
      spanking_hard_give: 1,
      slapping_receive: 0,
      slapping_give: 1,
      choking_receive: 0,
      choking_give: 1,
      spitting_receive: 0.5,
      spitting_give: 1,
      watersports_receive: 0.5,
      watersports_give: 1
    },
    oral: {
      oral_sex_receive: 1,
      oral_sex_give: 1,
      oral_body_receive: 1,
      oral_body_give: 1
    },
    anal: {
      anal_fingers_toys_receive: 0,
      anal_fingers_toys_give: 1,
      rimming_receive: 1,
      rimming_give: 1
    },
    power_exchange: {
      restraints_receive: 0,
      restraints_give: 1,
      blindfold_receive: 0,
      blindfold_give: 1,
      orgasm_control_receive: 1,
      orgasm_control_give: 1,
      protocols_receive: 0,
      protocols_give: 1
    },
    verbal_roleplay: {
      dirty_talk: 1,
      moaning: 1,
      roleplay: 0.5,
      commands_receive: 0,
      commands_give: 1,
      begging_receive: 0,
      begging_give: 1
    },
    display_performance: {
      stripping_self: 0,
      watching_strip: 1,
      solo_pleasure_self: 0.5,
      watching_solo_pleasure: 1,
      posing_self: 0,
      posing_watching: 1,
      dancing_self: 0,
      dancing_watching: 0,
      revealing_clothing_self: 0,
      revealing_clothing_watching: 0
    }
  },
  truth_topics: {
    past_experiences: 1,
    fantasies: 1,
    turn_ons: 1,
    turn_offs: 1,
    insecurities: 1,
    boundaries: 1,
    future_fantasies: 1,
    feeling_desired: 1,
    openness_score: 100
  },
  boundaries: {
    hard_limits: ["degradation_humiliation"],
    additional_notes: ""
  },
  activity_tags: {
    open_to_gentle: true,
    open_to_moderate: true,
    open_to_intense: true,
    open_to_oral: true,
    open_to_anal: true,
    open_to_restraints: true,
    open_to_orgasm_control: true,
    open_to_roleplay: true,
    open_to_display: true,
    open_to_group: true
  }
};

export const profileQuickCheck = {
  user_id: "1760539995562-569q6055r",
  profile_version: "0.4",
  timestamp: "2025-10-15T14:53:15.564Z",
  arousal_propensity: {
    sexual_excitation: 1,
    inhibition_performance: 0.17,
    inhibition_consequence: 0.29,
    interpretation: {
      se: "High",
      sis_p: "Low",
      sis_c: "Low"
    }
  },
  power_dynamic: {
    orientation: "Bottom",
    top_score: 0,
    bottom_score: 100,
    confidence: 1,
    interpretation: "Very high confidence Bottom"
  },
  domain_scores: {
    sensation: 64,
    connection: 100,
    power: 70,
    exploration: 95,
    verbal: 100
  },
  activities: {
    physical_touch: {
      massage_receive: 1,
      massage_give: 1,
      hair_pull_gentle_receive: 1,
      hair_pull_gentle_give: 0,
      biting_moderate_receive: 1,
      biting_moderate_give: 0,
      spanking_moderate_receive: 1,
      spanking_moderate_give: 0,
      hands_genitals_receive: 1,
      hands_genitals_give: 1,
      spanking_hard_receive: 1,
      spanking_hard_give: 0,
      slapping_receive: 1,
      slapping_give: 0,
      choking_receive: 1,
      choking_give: 0,
      spitting_receive: 1,
      spitting_give: 1,
      watersports_receive: 1,
      watersports_give: 1
    },
    oral: {
      oral_sex_receive: 1,
      oral_sex_give: 1,
      oral_body_receive: 1,
      oral_body_give: 1
    },
    anal: {
      anal_fingers_toys_receive: 1,
      anal_fingers_toys_give: 1,
      rimming_receive: 1,
      rimming_give: 1
    },
    power_exchange: {
      restraints_receive: 1,
      restraints_give: 0,
      blindfold_receive: 1,
      blindfold_give: 0,
      orgasm_control_receive: 1,
      orgasm_control_give: 1,
      protocols_receive: 1,
      protocols_give: 0
    },
    verbal_roleplay: {
      dirty_talk: 1,
      moaning: 1,
      roleplay: 1,
      commands_receive: 1,
      commands_give: 0,
      begging_receive: 1,
      begging_give: 0
    },
    display_performance: {
      stripping_self: 1,
      watching_strip: 0.5,
      solo_pleasure_self: 1,
      watching_solo_pleasure: 1,
      posing_self: 1,
      posing_watching: 0,
      dancing_self: 1,
      dancing_watching: 0,
      revealing_clothing_self: 1,
      revealing_clothing_watching: 0
    }
  },
  truth_topics: {
    past_experiences: 1,
    fantasies: 1,
    turn_ons: 1,
    turn_offs: 1,
    insecurities: 1,
    boundaries: 1,
    future_fantasies: 1,
    feeling_desired: 1,
    openness_score: 100
  },
  boundaries: {
    hard_limits: ["degradation_humiliation"],
    additional_notes: ""
  },
  activity_tags: {
    open_to_gentle: true,
    open_to_moderate: true,
    open_to_intense: true,
    open_to_oral: true,
    open_to_anal: true,
    open_to_restraints: true,
    open_to_orgasm_control: true,
    open_to_roleplay: true,
    open_to_display: true,
    open_to_group: true
  }
};

// Additional test profiles for edge cases

export const profileSwitchA = {
  user_id: "test-switch-a",
  profile_version: "0.4",
  timestamp: "2025-10-15T00:00:00.000Z",
  arousal_propensity: {
    sexual_excitation: 0.75,
    inhibition_performance: 0.30,
    inhibition_consequence: 0.35,
    interpretation: { se: "High", sis_p: "Moderate-Low", sis_c: "Moderate-Low" }
  },
  power_dynamic: {
    orientation: "Switch",
    top_score: 70,
    bottom_score: 65,
    confidence: 0.65,
    interpretation: "Moderate confidence Switch"
  },
  domain_scores: {
    sensation: 60,
    connection: 75,
    power: 65,
    exploration: 70,
    verbal: 80
  },
  activities: {
    physical_touch: {
      massage_receive: 1, massage_give: 1,
      hair_pull_gentle_receive: 1, hair_pull_gentle_give: 1,
      biting_moderate_receive: 1, biting_moderate_give: 1,
      spanking_moderate_receive: 0.5, spanking_moderate_give: 1,
      hands_genitals_receive: 1, hands_genitals_give: 1,
      spanking_hard_receive: 0.5, spanking_hard_give: 0.5,
      slapping_receive: 0, slapping_give: 0.5,
      choking_receive: 0, choking_give: 0,
      spitting_receive: 0, spitting_give: 0,
      watersports_receive: 0, watersports_give: 0
    },
    oral: {
      oral_sex_receive: 1, oral_sex_give: 1,
      oral_body_receive: 1, oral_body_give: 1
    },
    anal: {
      anal_fingers_toys_receive: 0.5, anal_fingers_toys_give: 0.5,
      rimming_receive: 0, rimming_give: 0
    },
    power_exchange: {
      restraints_receive: 1, restraints_give: 1,
      blindfold_receive: 1, blindfold_give: 1,
      orgasm_control_receive: 0.5, orgasm_control_give: 0.5,
      protocols_receive: 0.5, protocols_give: 0.5
    },
    verbal_roleplay: {
      dirty_talk: 1, moaning: 1, roleplay: 0.5, commands_receive: 0.5, commands_give: 0.5, begging_receive: 0.5, begging_give: 0.5
    },
    display_performance: {
      stripping_self: 1, watching_strip: 1,
      solo_pleasure_self: 0.5, watching_solo_pleasure: 1,
      posing_self: 0.5, posing_watching: 1,
      dancing_self: 0.5, dancing_watching: 0.5,
      revealing_clothing_self: 1, revealing_clothing_watching: 1
    }
  },
  truth_topics: {
    past_experiences: 1, fantasies: 1, turn_ons: 1, turn_offs: 1,
    insecurities: 0.5, boundaries: 1, future_fantasies: 1, feeling_desired: 1,
    openness_score: 88
  },
  boundaries: {
    hard_limits: [],
    additional_notes: ""
  },
  activity_tags: {
    open_to_gentle: true, open_to_moderate: true, open_to_intense: true,
    open_to_oral: true, open_to_anal: true, open_to_restraints: true,
    open_to_orgasm_control: true, open_to_roleplay: true,
    open_to_display: true, open_to_group: true
  }
};

export const profileTopA = {
  ...profileBBH,
  user_id: "test-top-a"
};

export const profileTopB = {
  ...profileBBH,
  user_id: "test-top-b",
  domain_scores: { ...profileBBH.domain_scores, exploration: 55, verbal: 65 }
};

export const profileBottomA = {
  ...profileQuickCheck,
  user_id: "test-bottom-a"
};

export const profileBottomB = {
  ...profileQuickCheck,
  user_id: "test-bottom-b",
  domain_scores: { ...profileQuickCheck.domain_scores, exploration: 90, verbal: 95 }
};

