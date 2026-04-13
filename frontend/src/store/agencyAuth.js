/**
 * Agency authentication state store.
 * Uses Vue's reactive() to share state across components without Pinia.
 * Access token: stored in-memory and localStorage (short 1h TTL).
 * Refresh token: httpOnly cookie managed by the server.
 */

import { reactive } from 'vue'
import { agencyLogin, agencyRegister, agencyLogout, agencyRefreshToken } from '../api/agency.js'

const _TOKEN_KEY = 'agency_access_token'

function _parseToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const expired = payload.exp * 1000 < Date.now()
    return expired ? null : payload
  } catch {
    return null
  }
}

const state = reactive({
  accessToken: null,
  user: null,
  isAuthenticated: false,
  isAdmin: false,
})

function _applyToken(token) {
  const payload = _parseToken(token)
  if (!payload) {
    _clearState()
    return false
  }
  state.accessToken     = token
  state.isAuthenticated = true
  state.isAdmin         = payload.role === 'admin'
  localStorage.setItem(_TOKEN_KEY, token)
  return true
}

function _clearState() {
  state.accessToken     = null
  state.user            = null
  state.isAuthenticated = false
  state.isAdmin         = false
  localStorage.removeItem(_TOKEN_KEY)
}

/** Restore session from localStorage on app mount. */
function loadFromStorage() {
  const saved = localStorage.getItem(_TOKEN_KEY)
  if (saved) _applyToken(saved)
}

async function login(email, password) {
  const res = await agencyLogin(email, password)
  _applyToken(res.data.access_token)
  state.user = res.data.user
}

async function register(email, password) {
  const res = await agencyRegister(email, password)
  _applyToken(res.data.access_token)
  state.user = res.data.user
}

async function logout() {
  try { await agencyLogout() } catch { /* ignore */ }
  _clearState()
}

/** Call on 401 responses to try a silent token refresh via refresh cookie. */
async function refreshAccessToken() {
  try {
    const res = await agencyRefreshToken()
    return _applyToken(res.data.access_token)
  } catch {
    _clearState()
    return false
  }
}

// Bootstrap on module load
loadFromStorage()

export function useAgencyAuth() {
  return { state, login, register, logout, refreshAccessToken, loadFromStorage }
}
