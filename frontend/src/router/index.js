import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import SkiAssistantView from '../views/SkiAssistantView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/ski',
    name: 'SkiAssistant',
    component: SkiAssistantView
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
  }
]

// Use hash history on GitHub Pages (no server-side routing); web history elsewhere
const history = import.meta.env.VITE_USE_HASH_ROUTER
  ? createWebHashHistory(import.meta.env.BASE_URL)
  : createWebHistory(import.meta.env.BASE_URL)

const router = createRouter({ history, routes })

export default router
