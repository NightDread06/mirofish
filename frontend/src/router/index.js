import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'

// Agency module — lazy loaded to keep initial bundle small
const AgencyLanding    = () => import('../views/agency/AgencyLanding.vue')
const AgencyPricing    = () => import('../views/agency/AgencyPricing.vue')
const AgencyOnboarding = () => import('../views/agency/AgencyOnboarding.vue')
const AgencyPortal     = () => import('../views/agency/AgencyPortal.vue')
const AgencyContent    = () => import('../views/agency/AgencyContent.vue')
const AgencyAdmin      = () => import('../views/agency/AgencyAdmin.vue')
const AgencyPrivacy    = () => import('../views/agency/AgencyPrivacy.vue')

const routes = [
  // ── Existing MiroFish simulation routes (unchanged) ─────────────────────
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: SimulationView,
    props: true
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true
  },

  // ── Agency module routes ──────────────────────────────────────────────────
  {
    path: '/agency',
    name: 'AgencyLanding',
    component: AgencyLanding,
  },
  {
    path: '/agency/pricing',
    name: 'AgencyPricing',
    component: AgencyPricing,
  },
  {
    path: '/agency/onboarding',
    name: 'AgencyOnboarding',
    component: AgencyOnboarding,
  },
  {
    path: '/agency/privacy',
    name: 'AgencyPrivacy',
    component: AgencyPrivacy,
  },
  {
    path: '/agency/portal',
    name: 'AgencyPortal',
    component: AgencyPortal,
    meta: { requiresAuth: true },
  },
  {
    path: '/agency/portal/content/:id',
    name: 'AgencyContent',
    component: AgencyContent,
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/agency/admin',
    name: 'AgencyAdmin',
    component: AgencyAdmin,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ── Auth navigation guard ─────────────────────────────────────────────────────

router.beforeEach((to, _from, next) => {
  if (!to.meta.requiresAuth) {
    next()
    return
  }

  const token = localStorage.getItem('agency_access_token')
  if (!token) {
    next('/agency')
    return
  }

  // Verify token is not expired
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (payload.exp * 1000 < Date.now()) {
      localStorage.removeItem('agency_access_token')
      next('/agency')
      return
    }
    // Admin-only routes
    if (to.meta.requiresAdmin && payload.role !== 'admin') {
      next('/agency/portal')
      return
    }
  } catch {
    localStorage.removeItem('agency_access_token')
    next('/agency')
    return
  }

  next()
})

export default router
