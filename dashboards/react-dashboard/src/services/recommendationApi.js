/**
 * GridPulse - Recommendation & Savings Simulation API Service
 * Member 3 Integration
 *
 * Provides client-side methods to communicate with the local Python REST API (api/main.py).
 * Connects the React dashboard directly to the tested Recommendation Engine
 * and Energy Savings Simulator.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Helper to handle fetch errors and connection drops uniformly.
 *
 * @param {Response} response
 * @returns {Promise<any>}
 */
async function handleResponse(response) {
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      `Server responded with HTTP ${response.status}: ${response.statusText || "Invalid response format"}`
    );
  }

  if (!response.ok) {
    const errorMsg =
      (data && data.error) ||
      `Request failed with status ${response.status} (${response.statusText})`;
    const error = new Error(errorMsg);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

/**
 * Helper to wrap network fetch calls with descriptive connection diagnostics.
 *
 * @param {string} endpoint
 * @param {object} payload
 * @returns {Promise<any>}
 */
async function postJson(endpoint, payload) {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    return await handleResponse(response);
  } catch (error) {
    // If error has a response status, it was an HTTP error from handleResponse
    if (error.status) {
      throw error;
    }
    // Otherwise, it was a network drop, CORS refusal, or offline server
    const networkError = new Error(
      `Unable to connect to GRID_PULSE backend API at ${url}. ` +
      `Ensure the Python API service is running (python -m uvicorn api.main:app).`
    );
    networkError.originalError = error;
    throw networkError;
  }
}

/**
 * Fetches personalised appliance recommendations and energy rankings.
 *
 * @param {Array<object>} appliances - User's registered appliances.
 * @param {number|null|undefined} electricityRate - Active electricity rate in ₹/kWh.
 * @returns {Promise<object>} Complete recommendation report from the backend.
 */
export async function fetchRecommendations(appliances, electricityRate) {
  const payload = {
    appliances: Array.isArray(appliances) ? appliances : [],
    electricity_rate: electricityRate !== undefined ? electricityRate : null,
  };

  return await postJson("/api/recommendations", payload);
}

/**
 * Fetches simulated energy savings based on user scenario adjustments.
 *
 * @param {Array<object>} appliances - Baseline appliance records.
 * @param {Array<object>} adjustments - User-specified adjustments (e.g. proposed_hours_per_day).
 * @param {number|null|undefined} electricityRate - Active electricity rate in ₹/kWh.
 * @returns {Promise<object>} Complete simulation result from the backend.
 */
export async function fetchSimulation(appliances, adjustments, electricityRate) {
  const payload = {
    appliances: Array.isArray(appliances) ? appliances : [],
    adjustments: Array.isArray(adjustments) ? adjustments : [],
    electricity_rate: electricityRate !== undefined ? electricityRate : null,
  };

  return await postJson("/api/simulate", payload);
}
