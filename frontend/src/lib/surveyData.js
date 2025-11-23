/**
 * Survey Data Processor (v0.4)
 * Loads and organizes questions from CSV and schema
 */

import schema from '../data/schema.json';
import questionsCsvRaw from '../data/questions.csv?raw';

/**
 * Parse CSV to array of objects
 * @param {string} csv - Raw CSV text
 * @returns {Array<Object>} - Parsed questions
 */
function parseCSV(csv) {
  const lines = csv.trim().split('\n');
  const headers = lines[0].split(',');
  const questions = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;

    // Parse CSV line (handle quoted fields)
    const values = [];
    let current = '';
    let inQuotes = false;

    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current);

    // Build question object
    const question = {};
    headers.forEach((header, idx) => {
      const value = values[idx] ? values[idx].replace(/^"|"$/g, '').trim() : '';
      question[header] = value;
    });

    questions.push(question);
  }

  return questions;
}

// Parse questions CSV
const questionsData = parseCSV(questionsCsvRaw);

/**
 * Get chapter descriptions based on v0.4 modules
 */
function getChapterDescription(chapterName) {
  const descriptions = {
    'Arousal & Power': 'How much do you agree with each statement? (1 = Strongly disagree … 7 = Strongly agree)',
    'Physical Touch': 'Would you be open to the following activities with your partner? Choose: Y = Yes, M = Maybe, N = No',
    'Oral Activities': 'Would you be open to these oral activities? Choose: Y = Yes, M = Maybe, N = No',
    'Anal Activities': 'Would you be open to these anal activities? Choose: Y = Yes, M = Maybe, N = No',
    'Power Exchange': 'Would you be open to power exchange activities? Choose: Y = Yes, M = Maybe, N = No',
    'Verbal & Roleplay': 'Would you be open to verbal/roleplay activities? Choose: Y = Yes, M = Maybe, N = No',
    'Display & Performance': 'Would you be open to display/performance activities? Choose: Y = Yes, M = Maybe, N = No',
    'Truth Topics': 'Would you be comfortable discussing these topics with your partner? Choose: Y = Yes, M = Maybe, N = No',
    'Boundaries & Safety': 'Set your boundaries. We\'ll never suggest something outside what you mark here.'
  };
  return descriptions[chapterName] || '';
}

/**
 * Get all survey items organized by chapter
 * @returns {Array<Chapter>}
 */
export function getSurveyChapters() {
  const chapters = [];

  // Group questions by chapter
  const chapterMap = new Map();

  questionsData.forEach(q => {
    const chapterName = q.chapter;
    if (!chapterMap.has(chapterName)) {
      chapterMap.set(chapterName, []);
    }

    // Parse maps JSON if present
    let parsedMaps = {};
    if (q.maps) {
      try {
        parsedMaps = JSON.parse(q.maps);
      } catch (e) {
        console.warn(`Failed to parse maps for ${q.id}:`, e);
      }
    }

    chapterMap.get(chapterName).push({
      id: q.id,
      type: q.type,
      text: q.prompt,
      options: q.options,
      maps: parsedMaps,
      chapter: chapterName
    });
  });

  // Convert map to array of chapters
  chapterMap.forEach((items, chapterName) => {
    chapters.push({
      id: chapterName.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase(),
      title: chapterName,
      name: chapterName,
      description: getChapterDescription(chapterName),
      items: items
    });
  });

  return chapters;
}

/**
 * Get schema data
 */
export function getSchema() {
  return schema;
}

/**
 * Get domain definitions
 */
export function getDomains() {
  return schema.domains || [];
}

/**
 * Get arousal factors
 */
export function getArousalFactors() {
  return schema.arousal_factors || [];
}

/**
 * Get power dynamics configuration
 */
export function getPowerDynamics() {
  return schema.power_dynamics || {};
}

/**
 * Get boundary options
 */
export function getBoundaryOptions() {
  return schema.boundary_options || [];
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

    // Boundaries (C1) can be empty
    if (item.id === 'C1') {
      continue;
    }

    // Check if required (all other questions are required)
    if (answer === undefined || answer === null || answer === '') {
      errors.push(`Please answer: ${item.text}`);
      continue;
    }

    // Validate likert7 range
    if (item.type === 'likert7') {
      const num = Number(answer);
      if (isNaN(num) || num < 1 || num > 7) {
        errors.push(`Please select a value between 1-7 for: ${item.text}`);
      }
    }

    // Validate chooseYMN
    if (item.type === 'chooseYMN') {
      const val = String(answer).trim().toUpperCase();
      if (!['Y', 'M', 'N', 'YES', 'MAYBE', 'NO'].includes(val)) {
        errors.push(`Please select Y, M, or N for: ${item.text}`);
      }
    }
  }

  return errors;
}

/**
 * Get question by ID
 * @param {string} questionId - Question ID
 * @returns {Object|null} - Question object or null
 */
export function getQuestionById(questionId) {
  return questionsData.find(q => q.id === questionId) || null;
}

/**
 * Get all questions
 * @returns {Array<Object>} - All questions
 */
export function getAllQuestions() {
  return questionsData;
}
