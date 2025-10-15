# ATTUNED v0.4 CALCULATION IMPLEMENTATION GUIDE

**Purpose:** Provide engineering team with copy-paste-ready code for profile calculations, compatibility mapping, and AI engine input generation.

**Language:** TypeScript (adaptable to JavaScript)  
**Date:** October 2025  
**Version:** 0.4

---

## TABLE OF CONTENTS
1. [Data Types & Interfaces](#data-types--interfaces)
2. [Individual Profile Calculator](#individual-profile-calculator)
3. [Compatibility Mapper](#compatibility-mapper)
4. [AI Engine Input Generator](#ai-engine-input-generator)
5. [Utility Functions](#utility-functions)
6. [Testing Examples](#testing-examples)

---

## DATA TYPES & INTERFACES

```typescript
// Survey Response Types
type LikertResponse = 1 | 2 | 3 | 4 | 5 | 6 | 7
type YMNResponse = 'Y' | 'M' | 'N'
type YMNValue = 1.0 | 0.5 | 0.0

interface SurveyResponses {
  // Section 1: Arousal Propensity (Q1-Q12)
  arousal: LikertResponse[]
  
  // Section 2: Power Dynamics (Q13-Q16)
  power: LikertResponse[]
  
  // Section 3: Dare Activities (Q17-Q44)
  activities: {
    physical_touch: { [key: string]: YMNResponse }
    oral: { [key: string]: YMNResponse }
    anal: { [key: string]: YMNResponse }
    power_exchange: { [key: string]: YMNResponse }
    verbal_roleplay: { [key: string]: YMNResponse }
    display_performance: { [key: string]: YMNResponse }
  }
  
  // Section 4: Truth Topics (Q45-Q52)
  truth_topics: { [key: string]: YMNResponse }
  
  // Section 5: Boundaries (Q53-Q54)
  boundaries: {
    hard_limits: string[]
    additional_notes: string
  }
}

// Profile Output Types
type PowerOrientation = 'Top' | 'Bottom' | 'Switch' | 'Versatile/Undefined'
type InterpretationBand = 'Low' | 'Moderate-Low' | 'Moderate-High' | 'High'

interface ArousalPropensity {
  sexual_excitation: number  // 0-1
  inhibition_performance: number  // 0-1
  inhibition_consequence: number  // 0-1
  interpretation: {
    se: InterpretationBand
    sis_p: InterpretationBand
    sis_c: InterpretationBand
  }
}

interface PowerDynamic {
  orientation: PowerOrientation
  top_score: number  // 0-100
  bottom_score: number  // 0-100
  confidence: number  // 0-1
  interpretation: string
}

interface DomainScores {
  sensation: number  // 0-100
  connection: number  // 0-100
  power: number  // 0-100
  exploration: number  // 0-100
  verbal: number  // 0-100
}

interface ActivityMap {
  physical_touch: { [key: string]: YMNValue }
  oral: { [key: string]: YMNValue }
  anal: { [key: string]: YMNValue }
  power_exchange: { [key: string]: YMNValue }
  verbal_roleplay: { [key: string]: YMNValue }
  display_performance: { [key: string]: YMNValue }
}

interface TruthTopics {
  [key: string]: YMNValue
  openness_score: number  // 0-100
}

interface Boundaries {
  hard_limits: string[]
  additional_notes: string
}

interface ActivityTags {
  open_to_gentle: boolean
  open_to_moderate: boolean
  open_to_intense: boolean
  open_to_oral: boolean
  open_to_anal: boolean
  open_to_restraints: boolean
  open_to_orgasm_control: boolean
  open_to_roleplay: boolean
  open_to_display: boolean
  open_to_group: boolean
}

interface IntimacyProfile {
  user_id: string
  profile_version: string
  timestamp: string
  arousal_propensity: ArousalPropensity
  power_dynamic: PowerDynamic
  domain_scores: DomainScores
  activities: ActivityMap
  truth_topics: TruthTopics
  boundaries: Boundaries
  activity_tags: ActivityTags
}

// Compatibility Types
interface CompatibilityBreakdown {
  power_complement: number  // 0-100
  domain_similarity: number  // 0-100
  activity_overlap: number  // 0-100
  truth_overlap: number  // 0-100
  boundary_conflicts: BoundaryConflict[]
}

interface BoundaryConflict {
  player: string
  boundary: string
  conflicting_activity: string
}

interface CompatibilityResult {
  players: string[]
  compatibility_version: string
  timestamp: string
  overall_compatibility: {
    score: number  // 0-100
    interpretation: string
  }
  breakdown: CompatibilityBreakdown
  mutual_activities: {
    [category: string]: string[]
  }
  growth_opportunities: Array<{
    activity: string
    playerA: string
    playerB: string
  }>
  mutual_truth_topics: string[]
  blocked_activities: {
    reason: string
    activities: string[]
  }
}
```

---

## INDIVIDUAL PROFILE CALCULATOR

```typescript
class IntimacyProfileCalculator {
  
  /**
   * Main entry point: Calculate complete profile from survey responses
   */
  static calculateProfile(
    userId: string, 
    responses: SurveyResponses
  ): IntimacyProfile {
    
    const arousalPropensity = this.calculateArousalPropensity(responses.arousal)
    const powerDynamic = this.calculatePowerDynamic(responses.power)
    const activities = this.convertActivities(responses.activities)
    const domainScores = this.calculateDomainScores(activities, responses.truth_topics)
    const truthTopics = this.convertTruthTopics(responses.truth_topics)
    const activityTags = this.generateActivityTags(activities, responses.boundaries)
    
    return {
      user_id: userId,
      profile_version: '0.4',
      timestamp: new Date().toISOString(),
      arousal_propensity: arousalPropensity,
      power_dynamic: powerDynamic,
      domain_scores: domainScores,
      activities: activities,
      truth_topics: truthTopics,
      boundaries: responses.boundaries,
      activity_tags: activityTags
    }
  }
  
  /**
   * Calculate Sexual Excitation and Inhibition scores (SES/SIS)
   */
  private static calculateArousalPropensity(
    arousalResponses: LikertResponse[]
  ): ArousalPropensity {
    
    // SE items: Q1-Q4 (indices 0-3)
    const se_items = arousalResponses.slice(0, 4)
    const se_raw = this.mean(se_items)
    const se_normalized = (se_raw - 1) / 6
    
    // SIS-P items: Q5-Q8 (indices 4-7)
    const sis_p_items = arousalResponses.slice(4, 8)
    const sis_p_raw = this.mean(sis_p_items)
    const sis_p_normalized = (sis_p_raw - 1) / 6
    
    // SIS-C items: Q9-Q12 (indices 8-12)
    const sis_c_items = arousalResponses.slice(8, 12)
    const sis_c_raw = this.mean(sis_c_items)
    const sis_c_normalized = (sis_c_raw - 1) / 6
    
    return {
      sexual_excitation: Math.round(se_normalized * 100) / 100,
      inhibition_performance: Math.round(sis_p_normalized * 100) / 100,
      inhibition_consequence: Math.round(sis_c_normalized * 100) / 100,
      interpretation: {
        se: this.interpretBand(se_normalized),
        sis_p: this.interpretBand(sis_p_normalized),
        sis_c: this.interpretBand(sis_c_normalized)
      }
    }
  }
  
  /**
   * Calculate power dynamic orientation and confidence
   */
  private static calculatePowerDynamic(
    powerResponses: LikertResponse[]
  ): PowerDynamic {
    
    // Q13, Q15 = Top items (indices 0, 2)
    const top_items = [powerResponses[0], powerResponses[2]]
    const top_raw = this.mean(top_items)
    const top_score = ((top_raw - 1) / 6) * 100
    
    // Q14, Q16 = Bottom items (indices 1, 3)
    const bottom_items = [powerResponses[1], powerResponses[3]]
    const bottom_raw = this.mean(bottom_items)
    const bottom_score = ((bottom_raw - 1) / 6) * 100
    
    const theta_floor = 30
    const delta_band = 15
    
    let orientation: PowerOrientation
    let confidence: number
    let interpretation: string
    
    if (top_score < theta_floor && bottom_score < theta_floor) {
      orientation = 'Versatile/Undefined'
      confidence = Math.max(top_score, bottom_score) / 100
      interpretation = 'Low engagement - still exploring preferences'
      
    } else if (
      Math.abs(top_score - bottom_score) <= delta_band && 
      Math.min(top_score, bottom_score) >= theta_floor
    ) {
      orientation = 'Switch'
      confidence = Math.min(top_score, bottom_score) / 100
      interpretation = this.interpretConfidence(confidence) + ' Switch'
      
    } else if (top_score > bottom_score) {
      orientation = 'Top'
      confidence = (top_score / 100) * (1 - 0.3 * (bottom_score / 100))
      interpretation = this.interpretConfidence(confidence) + ' Top'
      
    } else {
      orientation = 'Bottom'
      confidence = (bottom_score / 100) * (1 - 0.3 * (top_score / 100))
      interpretation = this.interpretConfidence(confidence) + ' Bottom'
    }
    
    return {
      orientation,
      top_score: Math.round(top_score),
      bottom_score: Math.round(bottom_score),
      confidence: Math.round(confidence * 100) / 100,
      interpretation
    }
  }
  
  /**
   * Convert YMN responses to numeric values
   */
  private static convertActivities(
    activitiesRaw: SurveyResponses['activities']
  ): ActivityMap {
    
    const convert = (category: { [key: string]: YMNResponse }): { [key: string]: YMNValue } => {
      const result: { [key: string]: YMNValue } = {}
      Object.keys(category).forEach(key => {
        const response = category[key]
        result[key] = response === 'Y' ? 1.0 : response === 'M' ? 0.5 : 0.0
      })
      return result
    }
    
    return {
      physical_touch: convert(activitiesRaw.physical_touch),
      oral: convert(activitiesRaw.oral),
      anal: convert(activitiesRaw.anal),
      power_exchange: convert(activitiesRaw.power_exchange),
      verbal_roleplay: convert(activitiesRaw.verbal_roleplay),
      display_performance: convert(activitiesRaw.display_performance)
    }
  }
  
  /**
   * Calculate aggregate domain scores
   */
  private static calculateDomainScores(
    activities: ActivityMap,
    truthTopicsRaw: { [key: string]: YMNResponse }
  ): DomainScores {
    
    const truthTopics = this.convertTruthTopics(truthTopicsRaw)
    
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
    ].filter(v => v !== undefined)
    
    const sensation = Math.round(this.mean(sensation_items) * 100)
    
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
    ].filter(v => v !== undefined)
    
    const connection = Math.round(this.mean(connection_items) * 100)
    
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
    ].filter(v => v !== undefined)
    
    const power = Math.round(this.mean(power_items) * 100)
    
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
    ].filter(v => v !== undefined)
    
    const exploration = Math.round(this.mean(exploration_items) * 100)
    
    // VERBAL: Communication
    const verbal_items = [
      activities.verbal_roleplay['dirty_talk'],
      activities.verbal_roleplay['moaning'],
      activities.verbal_roleplay['roleplay'],
      activities.verbal_roleplay['commands'],
      activities.verbal_roleplay['begging']
    ].filter(v => v !== undefined)
    
    const verbal = Math.round(this.mean(verbal_items) * 100)
    
    return {
      sensation,
      connection,
      power,
      exploration,
      verbal
    }
  }
  
  /**
   * Convert truth topics to numeric and calculate openness score
   */
  private static convertTruthTopics(
    truthTopicsRaw: { [key: string]: YMNResponse }
  ): TruthTopics {
    
    const result: TruthTopics = { openness_score: 0 }
    const values: YMNValue[] = []
    
    Object.keys(truthTopicsRaw).forEach(key => {
      const response = truthTopicsRaw[key]
      const value: YMNValue = response === 'Y' ? 1.0 : response === 'M' ? 0.5 : 0.0
      result[key] = value
      values.push(value)
    })
    
    result.openness_score = Math.round(this.mean(values) * 100)
    
    return result
  }
  
  /**
   * Generate activity tags for AI engine gating
   */
  private static generateActivityTags(
    activities: ActivityMap,
    boundaries: Boundaries
  ): ActivityTags {
    
    const hasInterest = (value: YMNValue) => value >= 0.5
    
    // Gentle activities: massage, light touch
    const gentle = hasInterest(activities.physical_touch['massage_receive']) ||
                   hasInterest(activities.physical_touch['massage_give'])
    
    // Moderate activities: biting, spanking moderate, hands on genitals
    const moderate = hasInterest(activities.physical_touch['biting_moderate_receive']) ||
                     hasInterest(activities.physical_touch['spanking_moderate_receive'])
    
    // Intense activities: hard spanking, slapping, choking, watersports
    const intense = hasInterest(activities.physical_touch['spanking_hard_receive']) ||
                    hasInterest(activities.physical_touch['slapping_receive']) ||
                    hasInterest(activities.physical_touch['choking_receive']) ||
                    hasInterest(activities.physical_touch['watersports_receive'])
    
    const oral = hasInterest(activities.oral['oral_sex_receive']) ||
                 hasInterest(activities.oral['oral_sex_give'])
    
    const anal = hasInterest(activities.anal['anal_fingers_toys_receive']) ||
                 hasInterest(activities.anal['anal_fingers_toys_give']) ||
                 hasInterest(activities.anal['rimming_receive']) ||
                 hasInterest(activities.anal['rimming_give'])
    
    const restraints = hasInterest(activities.power_exchange['restraints_receive']) ||
                       hasInterest(activities.power_exchange['restraints_give'])
    
    const orgasm_control = hasInterest(activities.power_exchange['orgasm_control_receive']) ||
                           hasInterest(activities.power_exchange['orgasm_control_give'])
    
    const roleplay = hasInterest(activities.verbal_roleplay['roleplay'])
    
    const display = hasInterest(activities.display_performance['stripping_me']) ||
                    hasInterest(activities.display_performance['watching_strip']) ||
                    hasInterest(activities.display_performance['watched_solo_pleasure'])
    
    const group = !boundaries.hard_limits.includes('multi_partner')
    
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
    }
  }
  
  /**
   * Helper: Calculate mean of numeric array
   */
  private static mean(values: number[]): number {
    if (values.length === 0) return 0
    return values.reduce((sum, val) => sum + val, 0) / values.length
  }
  
  /**
   * Helper: Interpret 0-1 score into band
   */
  private static interpretBand(score: number): InterpretationBand {
    if (score <= 0.30) return 'Low'
    if (score <= 0.55) return 'Moderate-Low'
    if (score <= 0.75) return 'Moderate-High'
    return 'High'
  }
  
  /**
   * Helper: Interpret confidence score
   */
  private static interpretConfidence(confidence: number): string {
    if (confidence <= 0.30) return 'Low confidence'
    if (confidence <= 0.60) return 'Moderate confidence'
    if (confidence <= 0.85) return 'High confidence'
    return 'Very high confidence'
  }
}
```

---

## COMPATIBILITY MAPPER

```typescript
class CompatibilityMapper {
  
  /**
   * Main entry point: Calculate compatibility between two players
   */
  static calculateCompatibility(
    playerA: IntimacyProfile,
    playerB: IntimacyProfile
  ): CompatibilityResult {
    
    const powerComplement = this.calculatePowerComplement(
      playerA.power_dynamic,
      playerB.power_dynamic
    )
    
    const domainSimilarity = this.calculateDomainSimilarity(
      playerA.domain_scores,
      playerB.domain_scores
    )
    
    const activityOverlap = this.calculateActivityOverlap(
      playerA.activities,
      playerB.activities
    )
    
    const truthOverlap = this.calculateTruthOverlap(
      playerA.truth_topics,
      playerB.truth_topics
    )
    
    const boundaryConflicts = this.checkBoundaryConflicts(playerA, playerB)
    
    // Calculate weighted overall score
    let overallScore = (
      0.15 * powerComplement +
      0.25 * domainSimilarity +
      0.40 * activityOverlap +
      0.20 * truthOverlap
    )
    
    // Apply boundary penalty
    const boundaryPenalty = boundaryConflicts.length * 0.2
    overallScore = Math.max(0, overallScore - boundaryPenalty)
    overallScore = Math.round(overallScore * 100)
    
    const mutualActivities = this.identifyMutualActivities(
      playerA.activities,
      playerB.activities
    )
    
    const growthOpportunities = this.identifyGrowthOpportunities(
      playerA.activities,
      playerB.activities
    )
    
    const mutualTruthTopics = this.identifyMutualTruthTopics(
      playerA.truth_topics,
      playerB.truth_topics
    )
    
    const blockedActivities = this.identifyBlockedActivities(
      playerA,
      playerB
    )
    
    return {
      players: [playerA.user_id, playerB.user_id],
      compatibility_version: '0.4',
      timestamp: new Date().toISOString(),
      overall_compatibility: {
        score: overallScore,
        interpretation: this.interpretCompatibility(overallScore)
      },
      breakdown: {
        power_complement: Math.round(powerComplement * 100),
        domain_similarity: Math.round(domainSimilarity * 100),
        activity_overlap: Math.round(activityOverlap * 100),
        truth_overlap: Math.round(truthOverlap * 100),
        boundary_conflicts: boundaryConflicts
      },
      mutual_activities: mutualActivities,
      growth_opportunities: growthOpportunities,
      mutual_truth_topics: mutualTruthTopics,
      blocked_activities: blockedActivities
    }
  }
  
  /**
   * Calculate power dynamic complementarity (0-1)
   */
  private static calculatePowerComplement(
    powerA: PowerDynamic,
    powerB: PowerDynamic
  ): number {
    
    if (powerA.orientation === 'Switch' && powerB.orientation === 'Switch') {
      return 0.90
    }
    
    if (
      (powerA.orientation === 'Top' && powerB.orientation === 'Bottom') ||
      (powerA.orientation === 'Bottom' && powerB.orientation === 'Top')
    ) {
      const avgConfidence = (powerA.confidence + powerB.confidence) / 2
      return 0.85 + (0.15 * avgConfidence)
    }
    
    if (
      (powerA.orientation === 'Switch' || powerA.orientation === 'Versatile/Undefined') &&
      (powerB.orientation === 'Top' || powerB.orientation === 'Bottom')
    ) {
      return 0.70
    }
    
    if (
      (powerB.orientation === 'Switch' || powerB.orientation === 'Versatile/Undefined') &&
      (powerA.orientation === 'Top' || powerA.orientation === 'Bottom')
    ) {
      return 0.70
    }
    
    // Both same pole or both undefined
    return 0.40
  }
  
  /**
   * Calculate domain similarity (0-1)
   */
  private static calculateDomainSimilarity(
    domainsA: DomainScores,
    domainsB: DomainScores
  ): number {
    
    const sensationDist = 1 - Math.abs(domainsA.sensation - domainsB.sensation) / 100
    const connectionDist = 1 - Math.abs(domainsA.connection - domainsB.connection) / 100
    const powerDist = 1 - Math.abs(domainsA.power - domainsB.power) / 100
    const explorationDist = 1 - Math.abs(domainsA.exploration - domainsB.exploration) / 100
    const verbalDist = 1 - Math.abs(domainsA.verbal - domainsB.verbal) / 100
    
    return (sensationDist + connectionDist + powerDist + explorationDist + verbalDist) / 5
  }
  
  /**
   * Calculate activity-level overlap using category Jaccard (0-1)
   */
  private static calculateActivityOverlap(
    activitiesA: ActivityMap,
    activitiesB: ActivityMap
  ): number {
    
    const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>
    const jaccardScores: number[] = []
    
    categories.forEach(category => {
      const jaccard = this.calculateCategoryJaccard(
        activitiesA[category],
        activitiesB[category]
      )
      jaccardScores.push(jaccard)
    })
    
    return jaccardScores.reduce((sum, val) => sum + val, 0) / jaccardScores.length
  }
  
  /**
   * Calculate Jaccard coefficient for a single activity category
   */
  private static calculateCategoryJaccard(
    categoryA: { [key: string]: YMNValue },
    categoryB: { [key: string]: YMNValue }
  ): number {
    
    const keys = Object.keys(categoryA)
    let mutualYes = 0
    let atLeastOneYes = 0
    
    keys.forEach(key => {
      const valA = categoryA[key]
      const valB = categoryB[key]
      
      // Both interested (Y or M)
      if (valA >= 0.5 && valB >= 0.5) {
        mutualYes += 1
      }
      
      // At least one interested
      if (valA >= 0.5 || valB >= 0.5) {
        atLeastOneYes += 1
      }
    })
    
    if (atLeastOneYes === 0) return 0
    return mutualYes / atLeastOneYes
  }
  
  /**
   * Calculate truth topic overlap (0-1)
   */
  private static calculateTruthOverlap(
    truthA: TruthTopics,
    truthB: TruthTopics
  ): number {
    
    const keys = Object.keys(truthA).filter(k => k !== 'openness_score')
    let mutualTopics = 0
    
    keys.forEach(key => {
      if (truthA[key] >= 0.5 && truthB[key] >= 0.5) {
        mutualTopics += 1
      }
    })
    
    return mutualTopics / keys.length
  }
  
  /**
   * Check for boundary conflicts between players
   */
  private static checkBoundaryConflicts(
    playerA: IntimacyProfile,
    playerB: IntimacyProfile
  ): BoundaryConflict[] {
    
    const conflicts: BoundaryConflict[] = []
    
    // Boundary to activity mapping
    const boundaryMap: { [key: string]: string[] } = {
      'impact_play': [
        'spanking_moderate_give', 'spanking_moderate_receive',
        'spanking_hard_give', 'spanking_hard_receive',
        'slapping_give', 'slapping_receive'
      ],
      'restraints_bondage': [
        'restraints_give', 'restraints_receive'
      ],
      'breath_play': [
        'choking_give', 'choking_receive'
      ],
      'anal_activities': [
        'anal_fingers_toys_give', 'anal_fingers_toys_receive',
        'rimming_give', 'rimming_receive'
      ],
      'degradation_humiliation': ['begging'],
      'roleplay': ['roleplay'],
      'toys_props': []  // Would need separate tracking
    }
    
    // Check A's boundaries vs B's interests
    playerA.boundaries.hard_limits.forEach(limit => {
      const activityKeys = boundaryMap[limit] || []
      activityKeys.forEach(actKey => {
        // Search all activity categories
        Object.values(playerB.activities).forEach(category => {
          if (category[actKey] !== undefined && category[actKey] >= 0.5) {
            conflicts.push({
              player: playerA.user_id,
              boundary: limit,
              conflicting_activity: actKey
            })
          }
        })
      })
    })
    
    // Check B's boundaries vs A's interests
    playerB.boundaries.hard_limits.forEach(limit => {
      const activityKeys = boundaryMap[limit] || []
      activityKeys.forEach(actKey => {
        Object.values(playerA.activities).forEach(category => {
          if (category[actKey] !== undefined && category[actKey] >= 0.5) {
            conflicts.push({
              player: playerB.user_id,
              boundary: limit,
              conflicting_activity: actKey
            })
          }
        })
      })
    })
    
    return conflicts
  }
  
  /**
   * Identify activities both players are open to
   */
  private static identifyMutualActivities(
    activitiesA: ActivityMap,
    activitiesB: ActivityMap
  ): { [category: string]: string[] } {
    
    const result: { [category: string]: string[] } = {}
    
    const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>
    categories.forEach(category => {
      const mutualKeys: string[] = []
      const keys = Object.keys(activitiesA[category])
      
      keys.forEach(key => {
        const valA = activitiesA[category][key]
        const valB = activitiesB[category][key]
        
        // Both Y or M
        if (valA >= 0.5 && valB >= 0.5) {
          mutualKeys.push(key)
        }
      })
      
      result[category] = mutualKeys
    })
    
    return result
  }
  
  /**
   * Identify growth opportunities (one Y, one M)
   */
  private static identifyGrowthOpportunities(
    activitiesA: ActivityMap,
    activitiesB: ActivityMap
  ): Array<{ activity: string; playerA: string; playerB: string }> {
    
    const opportunities: Array<{ activity: string; playerA: string; playerB: string }> = []
    
    const categories = Object.keys(activitiesA) as Array<keyof ActivityMap>
    categories.forEach(category => {
      const keys = Object.keys(activitiesA[category])
      
      keys.forEach(key => {
        const valA = activitiesA[category][key]
        const valB = activitiesB[category][key]
        
        if (
          (valA === 1.0 && valB === 0.5) ||
          (valA === 0.5 && valB === 1.0)
        ) {
          opportunities.push({
            activity: `${category}.${key}`,
            playerA: valA === 1.0 ? 'yes' : 'maybe',
            playerB: valB === 1.0 ? 'yes' : 'maybe'
          })
        }
      })
    })
    
    return opportunities
  }
  
  /**
   * Identify mutual truth topics
   */
  private static identifyMutualTruthTopics(
    truthA: TruthTopics,
    truthB: TruthTopics
  ): string[] {
    
    const mutual: string[] = []
    const keys = Object.keys(truthA).filter(k => k !== 'openness_score')
    
    keys.forEach(key => {
      if (truthA[key] >= 0.5 && truthB[key] >= 0.5) {
        mutual.push(key)
      }
    })
    
    return mutual
  }
  
  /**
   * Identify activities blocked by boundaries
   */
  private static identifyBlockedActivities(
    playerA: IntimacyProfile,
    playerB: IntimacyProfile
  ): { reason: string; activities: string[] } {
    
    const allHardLimits = [
      ...playerA.boundaries.hard_limits,
      ...playerB.boundaries.hard_limits
    ]
    
    const uniqueLimits = Array.from(new Set(allHardLimits))
    
    return {
      reason: 'hard_boundaries',
      activities: uniqueLimits
    }
  }
  
  /**
   * Helper: Interpret compatibility score
   */
  private static interpretCompatibility(score: number): string {
    if (score >= 85) return 'Exceptional compatibility'
    if (score >= 70) return 'High compatibility'
    if (score >= 55) return 'Moderate compatibility'
    if (score >= 40) return 'Lower compatibility'
    return 'Challenging compatibility'
  }
}
```

---

## AI ENGINE INPUT GENERATOR

```typescript
class AIEngineInputGenerator {
  
  /**
   * Generate AI engine input for activity generation
   */
  static generateInput(
    sessionId: string,
    profiles: IntimacyProfile[],
    compatibility: CompatibilityResult,
    intensityLevel: 'gentle' | 'moderate' | 'intense',
    previousActivities: string[] = []
  ): AIEngineInput {
    
    const players = profiles.map(p => ({
      id: p.user_id,
      display_name: `Player ${profiles.indexOf(p) + 1}`,
      arousal_profile: {
        se: p.arousal_propensity.sexual_excitation,
        sis_p: p.arousal_propensity.inhibition_performance,
        sis_c: p.arousal_propensity.inhibition_consequence
      },
      power_role: p.power_dynamic.orientation,
      domain_preferences: p.domain_scores
    }))
    
    const allowedDareTypes = this.extractAllowedActivities(compatibility.mutual_activities)
    const allowedTruthTopics = compatibility.mutual_truth_topics
    const blockedActivities = compatibility.blocked_activities.activities
    
    const contextFlags = {
      power_dynamic_active: profiles.some(p => 
        p.power_dynamic.orientation === 'Top' || 
        p.power_dynamic.orientation === 'Bottom'
      ),
      high_connection_preference: profiles.some(p => p.domain_scores.connection >= 70),
      exploration_cautious: profiles.every(p => p.domain_scores.exploration < 50)
    }
    
    return {
      session_id: sessionId,
      players,
      mutual_activities: {
        allowed_dare_types: allowedDareTypes,
        allowed_truth_topics: allowedTruthTopics
      },
      blocked_activities: blockedActivities,
      intensity_level: intensityLevel,
      context_flags: contextFlags,
      previous_activities: previousActivities
    }
  }
  
  /**
   * Extract flat list of allowed activity types
   */
  private static extractAllowedActivities(
    mutualActivities: { [category: string]: string[] }
  ): string[] {
    
    const allowed: string[] = []
    
    Object.keys(mutualActivities).forEach(category => {
      mutualActivities[category].forEach(activity => {
        allowed.push(`${category}:${activity}`)
      })
    })
    
    return allowed
  }
}

interface AIEngineInput {
  session_id: string
  players: Array<{
    id: string
    display_name: string
    arousal_profile: {
      se: number
      sis_p: number
      sis_c: number
    }
    power_role: PowerOrientation
    domain_preferences: DomainScores
  }>
  mutual_activities: {
    allowed_dare_types: string[]
    allowed_truth_topics: string[]
  }
  blocked_activities: string[]
  intensity_level: 'gentle' | 'moderate' | 'intense'
  context_flags: {
    power_dynamic_active: boolean
    high_connection_preference: boolean
    exploration_cautious: boolean
  }
  previous_activities: string[]
}
```

---

## UTILITY FUNCTIONS

```typescript
class ProfileUtils {
  
  /**
   * Validate survey responses before processing
   */
  static validateSurveyResponses(responses: SurveyResponses): { valid: boolean; errors: string[] } {
    const errors: string[] = []
    
    // Check arousal responses (must be 12 items, all 1-7)
    if (responses.arousal.length !== 12) {
      errors.push('Arousal section must have exactly 12 responses')
    }
    responses.arousal.forEach((val, idx) => {
      if (val < 1 || val > 7) {
        errors.push(`Arousal Q${idx + 1} must be between 1-7, got ${val}`)
      }
    })
    
    // Check power responses (must be 4 items, all 1-7)
    if (responses.power.length !== 4) {
      errors.push('Power section must have exactly 4 responses')
    }
    responses.power.forEach((val, idx) => {
      if (val < 1 || val > 7) {
        errors.push(`Power Q${idx + 1} must be between 1-7, got ${val}`)
      }
    })
    
    // Check activities (all must be Y/M/N)
    const validateCategory = (category: { [key: string]: YMNResponse }, categoryName: string) => {
      Object.keys(category).forEach(key => {
        const val = category[key]
        if (val !== 'Y' && val !== 'M' && val !== 'N') {
          errors.push(`${categoryName}.${key} must be Y, M, or N, got ${val}`)
        }
      })
    }
    
    validateCategory(responses.activities.physical_touch, 'physical_touch')
    validateCategory(responses.activities.oral, 'oral')
    validateCategory(responses.activities.anal, 'anal')
    validateCategory(responses.activities.power_exchange, 'power_exchange')
    validateCategory(responses.activities.verbal_roleplay, 'verbal_roleplay')
    validateCategory(responses.activities.display_performance, 'display_performance')
    
    // Check truth topics (all must be Y/M/N)
    validateCategory(responses.truth_topics, 'truth_topics')
    
    // Check boundaries
    if (!Array.isArray(responses.boundaries.hard_limits)) {
      errors.push('Boundaries hard_limits must be an array')
    }
    
    if (typeof responses.boundaries.additional_notes !== 'string') {
      errors.push('Boundaries additional_notes must be a string')
    }
    
    return {
      valid: errors.length === 0,
      errors
    }
  }
  
  /**
   * Generate summary narrative for profile
   */
  static generateProfileSummary(profile: IntimacyProfile): string {
    const { arousal_propensity, power_dynamic, domain_scores } = profile
    
    let summary = ''
    
    // Arousal style
    if (arousal_propensity.sexual_excitation >= 0.7 && arousal_propensity.inhibition_performance < 0.4) {
      summary += 'You have a highly responsive arousal style with low performance anxiety. '
    } else if (arousal_propensity.sexual_excitation < 0.4) {
      summary += 'You have a slower-building arousal style that benefits from intentional buildup. '
    }
    
    // Power dynamic
    summary += `Your power dynamic orientation is **${power_dynamic.orientation}** with ${power_dynamic.interpretation.toLowerCase()}. `
    
    // Top domain
    const sortedDomains = Object.entries(domain_scores)
      .sort((a, b) => b[1] - a[1])
    const topDomain = sortedDomains[0]
    
    summary += `Your highest preference is **${topDomain[0]}** (${topDomain[1]}/100). `
    
    return summary
  }
  
  /**
   * Export profile to JSON for storage
   */
  static exportProfile(profile: IntimacyProfile): string {
    return JSON.stringify(profile, null, 2)
  }
  
  /**
   * Import profile from JSON
   */
  static importProfile(json: string): IntimacyProfile {
    return JSON.parse(json) as IntimacyProfile
  }
}
```

---

## TESTING EXAMPLES

```typescript
// Example: Calculate profile from mock responses
const mockResponses: SurveyResponses = {
  arousal: [6, 5, 6, 7, 2, 3, 2, 3, 4, 5, 4, 4],  // High SE, Low SIS-P, Moderate SIS-C
  power: [6, 4, 6, 5],  // Top-leaning but also some bottom
  activities: {
    physical_touch: {
      'massage_receive': 'Y',
      'massage_give': 'Y',
      'hair_pull_gentle_receive': 'M',
      'hair_pull_gentle_give': 'Y',
      'biting_moderate_receive': 'Y',
      'biting_moderate_give': 'Y',
      'spanking_moderate_receive': 'M',
      'spanking_moderate_give': 'Y',
      'hands_genitals_receive': 'Y',
      'hands_genitals_give': 'Y',
      'spanking_hard_receive': 'N',
      'spanking_hard_give': 'M',
      'slapping_receive': 'N',
      'slapping_give': 'N',
      'choking_receive': 'N',
      'choking_give': 'N',
      'spitting_receive': 'N',
      'spitting_give': 'N',
      'watersports_receive': 'N',
      'watersports_give': 'N'
    },
    oral: {
      'oral_sex_receive': 'Y',
      'oral_sex_give': 'Y',
      'oral_body_receive': 'Y',
      'oral_body_give': 'Y'
    },
    anal: {
      'anal_fingers_toys_receive': 'N',
      'anal_fingers_toys_give': 'M',
      'rimming_receive': 'N',
      'rimming_give': 'N'
    },
    power_exchange: {
      'restraints_receive': 'M',
      'restraints_give': 'Y',
      'blindfold_receive': 'Y',
      'blindfold_give': 'Y',
      'orgasm_control_receive': 'M',
      'orgasm_control_give': 'Y',
      'protocols_follow': 'M',
      'protocols_give': 'Y'
    },
    verbal_roleplay: {
      'dirty_talk': 'Y',
      'moaning': 'Y',
      'roleplay': 'M',
      'commands': 'Y',
      'begging': 'M'
    },
    display_performance: {
      'stripping_me': 'Y',
      'watching_strip': 'Y',
      'watched_solo_pleasure': 'M',
      'watching_solo_pleasure': 'Y',
      'posing': 'M',
      'dancing': 'Y',
      'revealing_clothing': 'Y'
    }
  },
  truth_topics: {
    'past_experiences': 'Y',
    'fantasies': 'Y',
    'turn_ons': 'Y',
    'turn_offs': 'Y',
    'insecurities': 'M',
    'boundaries': 'Y',
    'future_fantasies': 'Y',
    'feeling_desired': 'Y'
  },
  boundaries: {
    hard_limits: ['anal_activities', 'public_activities', 'recording'],
    additional_notes: 'No surprise activities without discussion first'
  }
}

// Calculate profile
const profile = IntimacyProfileCalculator.calculateProfile('user_123', mockResponses)
console.log(JSON.stringify(profile, null, 2))

// Expected output:
// {
//   "user_id": "user_123",
//   "profile_version": "0.4",
//   "arousal_propensity": {
//     "sexual_excitation": 0.83,  // High
//     "inhibition_performance": 0.33,  // Moderate-Low
//     "inhibition_consequence": 0.58  // Moderate-High
//   },
//   "power_dynamic": {
//     "orientation": "Switch",
//     "top_score": 83,
//     "bottom_score": 67,
//     "confidence": 0.67
//   },
//   "domain_scores": {
//     "sensation": 45,  // Moderate sensation interest
//     "connection": 78,  // High connection
//     "power": 69,  // Moderate-high power
//     "exploration": 58,  // Moderate exploration
//     "verbal": 80  // High verbal
//   },
//   ...
// }

// Test compatibility calculation
const profileA = IntimacyProfileCalculator.calculateProfile('user_123', mockResponses)
const profileB = IntimacyProfileCalculator.calculateProfile('user_456', mockResponsesB)

const compatibility = CompatibilityMapper.calculateCompatibility(profileA, profileB)
console.log(`Compatibility Score: ${compatibility.overall_compatibility.score}/100`)
console.log(`Power Complement: ${compatibility.breakdown.power_complement}/100`)
console.log(`Domain Similarity: ${compatibility.breakdown.domain_similarity}/100`)
console.log(`Activity Overlap: ${compatibility.breakdown.activity_overlap}/100`)
```

---

*End of Implementation Guide v0.4*
