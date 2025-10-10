/**
 * Survey Data Processor
 * Organizes questions from schema into chapters
 */

import schema from '../data/schema.json';

/**
 * Get all survey items organized by chapter
 * @returns {Array<Chapter>}
 */
export function getSurveyChapters() {
  const items = schema.items.full;
  const chapterDefinitions = schema.items.chapters;
  
  // Create a map of item ID to item object
  const itemMap = new Map();
  for (const item of items) {
    itemMap.set(item.id, item);
  }
  
  // Build chapters from schema definition
  const chapters = [];
  
  for (const [chapterTitle, itemIds] of Object.entries(chapterDefinitions)) {
    const chapterItems = [];
    
    for (const itemId of itemIds) {
      const item = itemMap.get(itemId);
      if (item) {
        chapterItems.push(item);
      }
    }
    
    if (chapterItems.length > 0) {
      chapters.push({
        id: chapterTitle.replace(/[^a-zA-Z0-9]/g, '_'),
        title: chapterTitle,
        description: getChapterDescription(chapterTitle),
        items: chapterItems
      });
    }
  }
  
  return chapters;
}

/**
 * Get chapter description - exact text from user-facing survey document
 */
function getChapterDescription(chapterTitle) {
  const descriptions = {
    'Arousal (SES/SIS)': 'How much do you agree with the statement? (1 = Strongly disagree … 7 = Strongly agree)',
    'Preferences': 'Would you do the following with your partner? Choose one: Y = Yes, M = Maybe, N = No',
    'Boundaries & Context': 'Set your limits and rules below. We\'ll never suggest something outside what you mark here.',
    'Role & Logistics': 'How much do you agree with the statement? (1 = Strongly disagree … 7 = Strongly agree)',
    'Ipsative (Current Tilt)': 'Choose the option you\'d prefer right now (A or B). Go with your first instinct.'
  };
  return descriptions[chapterTitle] || '';
}

/**
 * Get schema data
 */
export function getSchema() {
  return schema;
}

/**
 * Get trait definitions
 */
export function getTraits() {
  return schema.traits;
}

/**
 * Get dimension formulas
 */
export function getDimensions() {
  return schema.dimensions;
}

/**
 * Get archetype definitions
 */
export function getArchetypes() {
  return schema.archetypes;
}

/**
 * Validate answers for a chapter
 * @param {Array} items - Chapter items
 * @param {Record<string, any>} answers - Current answers
 * @returns {Array<string>} - Array of error messages
 */
export function validateChapter(items, answers) {
  const errors = [];
  
  for (const item of items) {
    const answer = answers[item.id];
    
    // Check if required (all questions are required except boundaries)
    if (item.type !== 'boundary' && (answer === undefined || answer === null || answer === '')) {
      errors.push(`Please answer: ${item.text}`);
    }
    
    // Validate likert7 range
    if (item.type === 'likert7' && answer !== undefined && answer !== '') {
      const num = Number(answer);
      if (isNaN(num) || num < 1 || num > 7) {
        errors.push(`Invalid answer for: ${item.text}`);
      }
    }
    
    // Validate YMN
    if (item.type === 'ymn' && answer !== undefined && answer !== '') {
      const val = String(answer).trim().toUpperCase();
      if (!['Y', 'M', 'N'].includes(val)) {
        errors.push(`Invalid answer for: ${item.text}`);
      }
    }
  }
  
  return errors;
}

