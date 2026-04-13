/**
 * Agency API client — extends the existing axios instance.
 * All requests that require auth inject the Bearer token from localStorage.
 */

import service from './index.js'

function authHeader() {
  const token = localStorage.getItem('agency_access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const agencyRegister = (email, password) =>
  service.post('/api/agency/auth/register', { email, password }, { withCredentials: true })

export const agencyLogin = (email, password) =>
  service.post('/api/agency/auth/login', { email, password }, { withCredentials: true })

export const agencyLogout = () =>
  service.post('/api/agency/auth/logout', {}, { withCredentials: true })

export const agencyRefreshToken = () =>
  service.post('/api/agency/auth/refresh', {}, { withCredentials: true })

export const agencyDeleteAccount = () =>
  service.delete('/api/agency/auth/account', {
    headers: authHeader(),
    withCredentials: true,
  })

// ── Clients ───────────────────────────────────────────────────────────────────

export const getClients = (params = {}) =>
  service.get('/api/agency/clients', { headers: authHeader(), params })

export const getMyProfile = () =>
  service.get('/api/agency/clients/me', { headers: authHeader() })

export const submitOnboarding = (data) =>
  service.post('/api/agency/clients/onboarding', data, { headers: authHeader() })

export const getClient = (id) =>
  service.get(`/api/agency/clients/${id}`, { headers: authHeader() })

export const updateClient = (id, data) =>
  service.patch(`/api/agency/clients/${id}`, data, { headers: authHeader() })

export const exportClientData = (id) =>
  service.get(`/api/agency/clients/${id}/export`, { headers: authHeader() })

export const gdprDeleteClient = (id) =>
  service.delete(`/api/agency/clients/${id}/gdpr-delete`, { headers: authHeader() })

export const getDashboardMetrics = () =>
  service.get('/api/agency/clients/dashboard/metrics', { headers: authHeader() })

// ── Content ───────────────────────────────────────────────────────────────────

export const generateContent = (data) =>
  service.post('/api/agency/content/generate', data, { headers: authHeader() })

export const getContentPackage = (id) =>
  service.get(`/api/agency/content/${id}`, { headers: authHeader() })

export const getClientPackages = (clientId) =>
  service.get(`/api/agency/content/client/${clientId}`, { headers: authHeader() })

export const updatePost = (packageId, postId, data) =>
  service.patch(`/api/agency/content/${packageId}/posts/${postId}`, data, {
    headers: authHeader(),
  })

export const downloadContentPackage = (id) =>
  service.get(`/api/agency/content/${id}/download`, { headers: authHeader() })

// ── Outreach ──────────────────────────────────────────────────────────────────

export const createCampaign = (data) =>
  service.post('/api/agency/outreach/campaign', data, { headers: authHeader() })

export const getCampaign = (id) =>
  service.get(`/api/agency/outreach/campaign/${id}`, { headers: authHeader() })

export const listCampaigns = () =>
  service.get('/api/agency/outreach/campaigns', { headers: authHeader() })

export const updateCampaign = (id, data) =>
  service.patch(`/api/agency/outreach/campaign/${id}`, data, { headers: authHeader() })

export const importLeads = (campaignId, leads) =>
  service.post(`/api/agency/outreach/campaign/${campaignId}/leads`,
    { leads }, { headers: authHeader() })

export const listLeads = (campaignId, params = {}) =>
  service.get(`/api/agency/outreach/campaign/${campaignId}/leads`, {
    headers: authHeader(), params,
  })

export const updateLead = (leadId, data) =>
  service.patch(`/api/agency/outreach/leads/${leadId}`, data, { headers: authHeader() })

export const personaliseOpener = (data) =>
  service.post('/api/agency/outreach/personalise', data, { headers: authHeader() })
