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
  "ROMANTIC",
  "POWER_DYNAMICS"
];

// Map of category -> array of question IDs contributing to it
export const CATEGORY_MAP = {
  IMPACT: ["B2a", "B2b", "B4a", "B4b"],
  BONDAGE: ["B1a", "B1b"],
  EXHIBITION: ["B9a", "B9b", "B10b"],
  VOYEUR: ["B10a"],
  ROLEPLAY: ["B5a", "B5b", "B6a", "B6b"],
  RECORDING: ["C4"], // boundary gate
  GROUP_ENM: [], // reserve for future explicit ENM items
  PUBLIC_EDGE: ["B9a", "B10b", "B13a", "B13b"],
  TOYS: ["B3a", "B3b", "B8a", "B8b", "B14a", "B14b", "B15a", "B15b", "B16a", "B16b"],
  SENSUAL: ["B3a", "B3b", "B17a", "B17b"],
  ROMANTIC: ["B9b"],
  POWER_DYNAMICS: ["B5a", "B5b", "B6a", "B6b", "B7a", "B7b"]
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

