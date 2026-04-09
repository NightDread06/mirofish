/**
 * Ski Dashboard API client
 * Wraps all /api/ski/* endpoints.
 */

import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
const api = axios.create({ baseURL: `${BASE}/api/ski` })

/**
 * GET /api/ski/conditions
 * Current weather, snow quality, visibility.
 */
export const getConditions = () => api.get('/conditions').then(r => r.data.data)

/**
 * GET /api/ski/recommendations
 * Top-3 runs with scores and reasoning.
 * @param {Object} prefs  { prioritize_snow, avoid_crowds, difficulty_level }
 */
export const getRecommendations = (prefs = {}) =>
  api.get('/recommendations', { params: prefs }).then(r => r.data.data)

/**
 * GET /api/ski/day-plan
 * Hour-by-hour itinerary.
 * @param {Object} prefs  same as getRecommendations
 */
export const getDayPlan = (prefs = {}) =>
  api.get('/day-plan', { params: prefs }).then(r => r.data.data)

/**
 * GET /api/ski/cameras
 * Webcam list with status.
 */
export const getCameras = () => api.get('/cameras').then(r => r.data.data)

/**
 * GET /api/ski/forecast
 * 8-day weather forecast.
 */
export const getForecast = () => api.get('/forecast').then(r => r.data.data)

/**
 * GET /api/ski/stress-tests
 * Adversarial scenario analysis.
 */
export const getStressTests = () => api.get('/stress-tests').then(r => r.data.data)

/**
 * POST /api/ski/refresh
 * Force-refresh all cached data immediately.
 */
export const postRefresh = () => api.post('/refresh').then(r => r.data.data)

/**
 * GET /api/ski/status
 * Scheduler & cache status.
 */
export const getStatus = () => api.get('/status').then(r => r.data.data)
