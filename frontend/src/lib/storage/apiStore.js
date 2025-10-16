/**
 * API-based storage for survey submissions
 * Replaces localStorage with server-side persistence
 */

// Determine API base URL
// DEBUG: Log environment info at module load
console.log('🔧 API Store Module Loading...');
console.log('  - import.meta.env.MODE:', import.meta.env?.MODE);
console.log('  - import.meta.env.VITE_API_URL:', import.meta.env?.VITE_API_URL);
console.log('  - window.location.hostname:', typeof window !== 'undefined' ? window.location.hostname : 'undefined');

function getApiRoot() {
  // Priority 1: Explicit environment variable
  if (import.meta.env?.VITE_API_URL) {
    console.log('📍 [getApiRoot] Using VITE_API_URL:', import.meta.env.VITE_API_URL);
    return import.meta.env.VITE_API_URL;
  }
  
  // Priority 2: Development mode → localhost
  // This is more reliable than hostname detection because Vite sets MODE explicitly
  if (import.meta.env?.MODE === 'development') {
    console.log('✅ [getApiRoot] MODE=development → Using localhost:5001');
    return 'http://localhost:5001';
  }
  
  // Priority 3: Runtime hostname detection (fallback)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    console.log('🔍 [getApiRoot] Checking hostname:', hostname);
    
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
      console.log('✅ [getApiRoot] Hostname is localhost → Using localhost:5001');
      return 'http://localhost:5001';
    }
  }
  
  // Priority 4: Production backend
  console.log('🌐 [getApiRoot] Defaulting to PRODUCTION backend');
  return 'https://attuned-backend.onrender.com';
}

// Call function to get the API root
const API_ROOT = getApiRoot();
const API_BASE = `${API_ROOT}/api/survey`;

console.log('✅ API Store configured:');
console.log('  - API_ROOT:', API_ROOT);
console.log('  - API_BASE:', API_BASE);
/**
 * Get all submissions from server
 */
export async function getAllSubmissions() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    const response = await fetch(`${API_BASE}/submissions`, {
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return {
      submissions: data.submissions || [],
      baseline: data.baseline
    };
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('Request timeout: getAllSubmissions took longer than 15 seconds');
    } else {
      console.error('Error fetching submissions:', error);
    }
    return { submissions: [], baseline: null };
  }
}

/**
 * Get a specific submission by ID
 */
export async function getSubmission(id) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    const response = await fetch(`${API_BASE}/submissions/${id}`, {
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('Request timeout: Submission fetch took longer than 15 seconds');
    } else {
      console.error('Error fetching submission:', error);
    }
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
      body: JSON.stringify({
        version: '0.4',
        ...submission,
      }),
    });
    
    if (!response.ok) {
      let message = `HTTP error! status: ${response.status}`;
      try {
        const text = await response.text();
        if (text) message += ` - ${text}`;
      } catch {}
      throw new Error(message);
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

// ============================================================================
// RECOMMENDATIONS & COMPATIBILITY API
// ============================================================================

/**
 * Generate activity recommendations for a game session
 * @param {Object} payload - Recommendation request
 * @param {Object} payload.player_a - Player A data (with submission_id or full profile)
 * @param {Object} payload.player_b - Player B data (with submission_id or full profile)
 * @param {Object} payload.session - Session configuration
 * @returns {Promise<Object>} Session with activities array
 */
export async function generateRecommendations(payload) {
  try {
    console.log('Generating recommendations...', { 
      player_a: payload.player_a?.submission_id, 
      player_b: payload.player_b?.submission_id,
      target: payload.session?.target_activities 
    });
    
    const response = await fetch(`${API_ROOT}/api/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Recommendations error:', errorText);
      throw new Error(`Failed to generate recommendations: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✅ Recommendations generated:', {
      session_id: data.session_id,
      activity_count: data.activities?.length,
      stats: data.stats
    });
    
    return data;
  } catch (error) {
    console.error('Error generating recommendations:', error);
    throw error;
  }
}

/**
 * Get activities for a specific session
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Session with activities
 */
export async function getSessionActivities(sessionId) {
  try {
    const response = await fetch(`${API_ROOT}/api/recommendations/${sessionId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching session activities:', error);
    throw error;
  }
}

/**
 * Calculate and store compatibility between two players
 * @param {string} submissionIdA - First player's submission ID
 * @param {string} submissionIdB - Second player's submission ID
 * @returns {Promise<Object>} Compatibility result
 */
export async function calculateCompatibility(submissionIdA, submissionIdB) {
  try {
    console.log('Calculating compatibility...', { submissionIdA, submissionIdB });
    
    const response = await fetch(`${API_ROOT}/api/compatibility`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        submission_id_a: submissionIdA,
        submission_id_b: submissionIdB,
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Compatibility calculation error:', errorText);
      throw new Error(`Failed to calculate compatibility: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✅ Compatibility calculated:', {
      score: data.overall_compatibility?.score,
      interpretation: data.overall_compatibility?.interpretation
    });
    
    return data;
  } catch (error) {
    console.error('Error calculating compatibility:', error);
    throw error;
  }
}

/**
 * Get stored compatibility result (or calculate if not exists)
 * @param {string} submissionIdA - First player's submission ID
 * @param {string} submissionIdB - Second player's submission ID
 * @returns {Promise<Object>} Compatibility result
 */
export async function getCompatibility(submissionIdA, submissionIdB) {
  try {
    const response = await fetch(
      `${API_ROOT}/api/compatibility/${submissionIdA}/${submissionIdB}`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching compatibility:', error);
    throw error;
  }
}

// ============================================================================
// SESSION MANAGEMENT (localStorage for temporary data)
// ============================================================================

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

