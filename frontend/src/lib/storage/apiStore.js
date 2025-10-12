/**
 * API-based storage for survey submissions
 * Replaces localStorage with server-side persistence
 */

const API_BASE =
  `${(import.meta.env?.VITE_API_URL ?? 'https://attuned-backend.onrender.com')}/api/survey`;
/**
 * Get all submissions from server
 */
export async function getAllSubmissions() {
  try {
    const response = await fetch(`${API_BASE}/submissions`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return {
      submissions: data.submissions || [],
      baseline: data.baseline
    };
  } catch (error) {
    console.error('Error fetching submissions:', error);
    return { submissions: [], baseline: null };
  }
}

/**
 * Get a specific submission by ID
 */
export async function getSubmission(id) {
  try {
    const response = await fetch(`${API_BASE}/submissions/${id}`);
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching submission:', error);
    return null;
  }
}

/**
 * Save a new submission to server
 */
export async function saveSubmission(submission) {
  try {
    const response = await fetch(`${API_BASE}/submissions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(submission),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error saving submission:', error);
    throw error;
  }
}

/**
 * Get baseline submission ID
 */
export async function getBaseline() {
  try {
    const response = await fetch(`${API_BASE}/baseline`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data.baseline;
  } catch (error) {
    console.error('Error fetching baseline:', error);
    return null;
  }
}

/**
 * Set baseline submission
 */
export async function setBaseline(submissionId) {
  try {
    const response = await fetch(`${API_BASE}/baseline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id: submissionId }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.baseline;
  } catch (error) {
    console.error('Error setting baseline:', error);
    throw error;
  }
}

/**
 * Clear baseline submission
 */
export async function clearBaseline() {
  try {
    const response = await fetch(`${API_BASE}/baseline`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return true;
  } catch (error) {
    console.error('Error clearing baseline:', error);
    throw error;
  }
}

/**
 * Export all data
 */
export async function exportData() {
  try {
    const response = await fetch(`${API_BASE}/export`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error exporting data:', error);
    throw error;
  }
}

// Keep localStorage functions for session management (temporary data)
const SESSION_KEY = 'attuned_current_session';

export function saveCurrentSession(sessionData) {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
  } catch (error) {
    console.error('Error saving session:', error);
  }
}

export function getCurrentSession() {
  try {
    const data = localStorage.getItem(SESSION_KEY);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.error('Error loading session:', error);
    return null;
  }
}

export function clearCurrentSession() {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (error) {
    console.error('Error clearing session:', error);
  }
}

