import axios from './index'

const BASE = '/api/ski'

function buildParams(opts = {}) {
  const p = {}
  if (opts.time)           p.time            = opts.time
  if (opts.difficulty)     p.difficulty      = opts.difficulty
  if (opts.prioritizeSnow !== undefined) p.prioritize_snow = opts.prioritizeSnow
  if (opts.avoidCrowds !== undefined)    p.avoid_crowds    = opts.avoidCrowds
  if (opts.tourists !== undefined)       p.tourists        = opts.tourists
  if (opts.seed !== undefined)           p.seed            = opts.seed
  return p
}

export const skiApi = {
  getDashboard: (opts) =>
    axios.get(`${BASE}/dashboard`, { params: buildParams(opts) }).then(r => r.data),

  getStrategy: (opts) =>
    axios.get(`${BASE}/strategy`, { params: buildParams(opts) }).then(r => r.data),

  getItinerary: (opts) =>
    axios.get(`${BASE}/itinerary`, { params: buildParams(opts) }).then(r => r.data),

  getGems: (opts) =>
    axios.get(`${BASE}/gems`, { params: buildParams(opts) }).then(r => r.data),

  getSensitivity: (opts) =>
    axios.get(`${BASE}/sensitivity`, { params: buildParams(opts) }).then(r => r.data),

  getStress: (opts) =>
    axios.get(`${BASE}/stress`, { params: buildParams(opts) }).then(r => r.data),

  getRules: (opts) =>
    axios.get(`${BASE}/rules`, { params: buildParams(opts) }).then(r => r.data),
}
