/**
 * Submission Store - LocalStorage wrapper for survey submissions
 */

const SUBMISSIONS_KEY = 'attuned_submissions';
const BASELINE_KEY = 'attuned_baseline_id';
const SESSION_KEY = 'attuned_current_session';

/**
 * Get all submissions
 * @returns {Array<Submission>}
 */
export function getAllSubmissions() {
  try {
    const data = localStorage.getItem(SUBMISSIONS_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Error reading submissions:', error);
    return [];
  }
}

/**
 * Save a submission
 * @param {Submission} submission
 */
export function saveSubmission(submission) {
  try {
    const submissions = getAllSubmissions();
    
    // Check if updating existing
    const existingIndex = submissions.findIndex(s => s.id === submission.id);
    if (existingIndex >= 0) {
      submissions[existingIndex] = submission;
    } else {
      submissions.push(submission);
    }

    localStorage.setItem(SUBMISSIONS_KEY, JSON.stringify(submissions));
  } catch (error) {
    console.error('Error saving submission:', error);
  }
}

/**
 * Get submission by ID
 * @param {string} id
 * @returns {Submission | null}
 */
export function getSubmissionById(id) {
  const submissions = getAllSubmissions();
  return submissions.find(s => s.id === id) || null;
}

/**
 * Delete submission by ID
 * @param {string} id
 */
export function deleteSubmission(id) {
  try {
    const submissions = getAllSubmissions();
    const filtered = submissions.filter(s => s.id !== id);
    localStorage.setItem(SUBMISSIONS_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Error deleting submission:', error);
  }
}

/**
 * Get baseline submission ID
 * @returns {string | null}
 */
export function getBaselineId() {
  return localStorage.getItem(BASELINE_KEY);
}

/**
 * Set baseline submission ID
 * @param {string} id
 */
export function setBaselineId(id) {
  localStorage.setItem(BASELINE_KEY, id);
}

/**
 * Get current session data (for resume)
 * @returns {Object | null}
 */
export function getCurrentSession() {
  try {
    const data = localStorage.getItem(SESSION_KEY);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.error('Error reading session:', error);
    return null;
  }
}

/**
 * Save current session data
 * @param {Object} session - {answers, currentChapter, name}
 */
export function saveCurrentSession(session) {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch (error) {
    console.error('Error saving session:', error);
  }
}

/**
 * Clear current session
 */
export function clearCurrentSession() {
  localStorage.removeItem(SESSION_KEY);
}

/**
 * Export submissions as JSON
 * @returns {string}
 */
export function exportSubmissionsJSON() {
  const submissions = getAllSubmissions();
  return JSON.stringify(submissions, null, 2);
}

/**
 * Export submissions as CSV
 * @returns {string}
 */
export function exportSubmissionsCSV() {
  const submissions = getAllSubmissions();
  if (submissions.length === 0) return '';

  // Headers
  const headers = [
    'ID',
    'Name',
    'Created At',
    'Adventure',
    'Connection',
    'Intensity',
    'Confidence',
    'Top Archetype',
    'Archetype Score'
  ];

  const rows = submissions.map(sub => {
    const topArchetype = sub.derived?.archetypes?.[0];
    return [
      sub.id,
      sub.name,
      sub.createdAt,
      sub.derived?.dials?.Adventure?.toFixed(1) || '',
      sub.derived?.dials?.Connection?.toFixed(1) || '',
      sub.derived?.dials?.Intensity?.toFixed(1) || '',
      sub.derived?.dials?.Confidence?.toFixed(1) || '',
      topArchetype?.name || '',
      topArchetype?.score?.toFixed(1) || ''
    ];
  });

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n');

  return csvContent;
}

