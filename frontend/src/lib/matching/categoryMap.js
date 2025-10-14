/**
 * Category Map for couple overlap matching (v0.3.1)
 * Includes directional A/B items and new B13–B17 items.
 */

// Active categories used by breakdowns
export const CATEGORIES = [
  "IMPACT",
  "BONDAGE",
  "EXHIBITION",
  "VOYEUR",
  "ROLEPLAY",
  "RECORDING",
  "GROUP_ENM",
  "PUBLIC_EDGE",
  "TOYS",
  "SENSUAL",
  "ROMANTIC"
];

// Map of category -> array of question IDs contributing to it (single-category assignment)
export const CATEGORY_MAP = {
  // Striking/force sensations
  IMPACT: ["B2a","B2b","B4a","B4b"],

  // Rope/restraints/immobilization (B3 moved here; remove from any other category)
  BONDAGE: ["B1a","B1b"],

  // Being seen / performing; public-ish display
  EXHIBITION: ["B9a","B10b"],

  // Watching others
  VOYEUR: ["B10a"],

  // Scenes/characters/commands (non-implement)
  ROLEPLAY: ["B5a","B5b","B6a","B6b"],

  // Gates (no direct items here; overlap will be 0 if gated off)
  RECORDING: ["C4"],
  GROUP_ENM: [],

  // Risk/fluids edge conditions (keep watersports only to avoid duplication with EXHIBITION)
  PUBLIC_EDGE: ["B13a","B13b"],

  // Implements/devices/insertables
  TOYS: ["B8a","B8b","B14a","B14b","B15a","B15b","B16a","B16b"],

  // Pure sensual touch/massage/feet (not restraints)
  SENSUAL: ["B3a","B3b","B17a","B17b"],

  // Affection/aftercare rituals (legacy single item)
  ROMANTIC: ["B9b"],

  // Not used for Jaccard; power complement is computed from traits in overlapHelper
  POWER_DYNAMICS: []
};

// Optional item tags for gating/analytics
export const ITEM_TAGS = {
  B13a: ["EXPLICIT_FLUIDS"], B13b: ["EXPLICIT_FLUIDS"],
  B14a: ["ANAL_STIM"], B14b: ["ANAL_STIM"],
  B15a: ["RIMMING"], B15b: ["RIMMING"],
  B16a: ["PEGGING"], B16b: ["PEGGING"],
  B17a: ["FOOT"], B17b: ["FOOT"]
};

// Direction map: a = on_me, b = i_do
export const DIRECTION_MAP = {
  a: "on_me",
  b: "i_do"
};

// Categories included in mean (sanity echo for debug UIs)
export const CATEGORIES_FOR_MEAN = CATEGORIES.filter(c => c !== 'RECORDING' && c !== 'GROUP_ENM');

