/**
 * Centralized API client for communicating with the FastAPI backend.
 * Uses Vite's VITE_API_BASE_URL environment variable when provided,
 * or defaults to relative '/api' requests proxied to http://127.0.0.1:8000.
 */

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
// Strip trailing slashes for clean URL concatenation
const API_BASE = RAW_BASE_URL.replace(/\/+$/, '');

/**
 * Standard API error class carrying HTTP status code and server detail.
 */
export class ApiError extends Error {
  constructor(message, status = 500, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Internal generic request handler with error normalization.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    // Parse JSON body if present
    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      data = text ? { detail: text } : null;
    }

    if (!response.ok) {
      const errorMessage =
        (data && (data.detail || data.message)) ||
        `Request failed with HTTP status ${response.status}`;
      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network errors (e.g. connection refused)
    throw new ApiError(
      'Unable to connect to the backend server. Please verify the FastAPI service is running.',
      0,
      { originalError: err.message }
    );
  }
}

/**
 * Health check endpoint.
 * GET /api/health
 */
export async function checkHealth() {
  return request('/api/health');
}

/**
 * Fetch all learning sessions for summary and resumption.
 * GET /api/sessions
 */
export async function getSessions() {
  return request('/api/sessions');
}

/**
 * Fetch details and learning cycles for a specific session.
 * GET /api/sessions/{session_id}
 */
export async function getSession(sessionId) {
  if (!sessionId) throw new Error('sessionId is required');
  return request(`/api/sessions/${encodeURIComponent(sessionId)}`);
}

/**
 * Create a new learning session and generate cycle #1.
 * POST /api/sessions
 * @param {Object} payload
 * @param {string} payload.topic
 * @param {string} [payload.initial_difficulty='Beginner']
 */
export async function createSession({ topic, initial_difficulty = 'Beginner' }) {
  if (!topic || !topic.trim()) {
    throw new Error('Topic is required');
  }

  return request('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({
      topic: topic.trim(),
      initial_difficulty,
    }),
  });
}

/**
 * Submit answers for a specific learning cycle.
 * POST /api/sessions/{session_id}/cycles/{cycle_number}/submit
 * @param {string} sessionId
 * @param {number} cycleNumber
 * @param {Array<string|{question_index: number, selected_option: string}>} answers
 */
export async function submitCycleQuiz(sessionId, cycleNumber, answers) {
  if (!sessionId) throw new Error('sessionId is required');
  if (cycleNumber === undefined || cycleNumber === null) throw new Error('cycleNumber is required');
  if (!Array.isArray(answers) || answers.length !== 12) {
    throw new Error(`Quiz submission requires exactly 12 answers, received ${answers?.length}`);
  }

  // Format as structured AnswerItems with validated indices
  const formattedAnswers = answers.map((ans, idx) => {
    if (typeof ans === 'object' && ans !== null && 'selected_option' in ans) {
      return {
        question_index: ans.question_index ?? idx,
        selected_option: String(ans.selected_option).trim(),
      };
    }
    return {
      question_index: idx,
      selected_option: String(ans).trim(),
    };
  });

  return request(`/api/sessions/${encodeURIComponent(sessionId)}/cycles/${encodeURIComponent(cycleNumber)}/submit`, {
    method: 'POST',
    body: JSON.stringify({ answers: formattedAnswers }),
  });
}

/**
 * Generate the next adaptive learning cycle for a submitted session.
 * POST /api/sessions/{session_id}/cycles
 * @param {string} sessionId
 */
export async function createNextCycle(sessionId) {
  if (!sessionId) throw new Error('sessionId is required');

  return request(`/api/sessions/${encodeURIComponent(sessionId)}/cycles`, {
    method: 'POST',
  });
}
