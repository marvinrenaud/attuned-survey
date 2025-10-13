IntimacAI / Attuned — v0.3.1 Update

Scope
- Added three explicit areas to the core (directional Y/M/N, a/b where applicable):
  1) Watersports (on me / I do)
  2) Anal play (anal stimulation, rimming, pegging — each a/b)
  3) Foot worship (on me / I do)

Why in core, not Advanced
- These materially affect activity routing. Keeping them behind an optional module hurts personalization.

Mapping to traits/domains (no changes to scoring math required)
- Watersports -> +NOVELTY (Exploration). Tag: EXPLICIT_FLUIDS.
- Anal stimulation/rimming/pegging -> +TOYS (Exploration). Tags: ANAL_STIM, RIMMING, PEGGING.
- Foot worship -> +SENSUAL (Sensory). Tag: FOOT.

Directional semantics
- a = "on me" (receiving)
- b = "I do" (giving)

Gating (unchanged)
- Suggestions require relevant boundaries/safety: barrier (C3) for anal acts, check-ins (C9), safeword (C7). Watersports only in private settings. Public/illegal acts are never suggested.

Files
- intimacai_survey_schema_v0.3.1.json
- intimacai_question_bank_v0.3.1.csv
- IntimacAI_Full_Survey_UserFacing_v0.3.1.md
- IntimacAI_Full_Survey_Respondent_Template_v0.3.1.tsv
- intimacai_scoring_v0.3.1.ts (copied from v0.3)
- intimacai_matching_helper_v0.3.1.ts (copied from v0.3)
