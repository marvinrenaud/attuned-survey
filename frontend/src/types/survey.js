// Survey data types

/**
 * @typedef {Object} TraitWeight
 * @property {string} trait
 * @property {number} weight
 */

/**
 * @typedef {Object} QuestionItem
 * @property {string} id
 * @property {string} text
 * @property {string} type - 'likert7' | 'ymn' | 'slider' | 'boundary'
 * @property {TraitWeight[]} traits
 * @property {string} [chapter]
 */

/**
 * @typedef {Object} Chapter
 * @property {string} id
 * @property {string} title
 * @property {string} description
 * @property {QuestionItem[]} items
 */

/**
 * @typedef {Object} DerivedData
 * @property {Record<string, number>} traits
 * @property {Object} dials
 * @property {number} dials.Adventure
 * @property {number} dials.Connection
 * @property {number} dials.Intensity
 * @property {number} dials.Confidence
 * @property {Array<{id: string, name: string, score: number}>} archetypes
 * @property {Object} boundaryFlags
 * @property {string[]} boundaryFlags.hardNos
 * @property {number} [boundaryFlags.impactCap]
 * @property {boolean} [boundaryFlags.noRecording]
 * @property {string[]} warnings
 */

/**
 * @typedef {Object} Submission
 * @property {string} id
 * @property {string} name
 * @property {string} createdAt
 * @property {Record<string, string | number>} answers
 * @property {DerivedData} derived
 */

/**
 * @typedef {Object} MatchingResult
 * @property {number} overall
 * @property {Record<string, number>} catScores
 * @property {number} meanJ
 * @property {number} powerComplement
 */

export {};

