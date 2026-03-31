import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import SkiAssistantView from '../views/SkiAssistantView.vue'

const isStaticBuild = !!import.meta.env.VITE_USE_HASH_ROUTER

const routes = [
  {
    path: '/',
    // On the static GitHub Pages build the backend doesn't exist,
    // so redirect straight to the ski assistant.
    component: isStaticBuild ? SkiAssistantView : Home,
    name: isStaticBuild ? 'SkiAssistant' : 'Home',
  },
  {
    path: '/ski',
    name: isStaticBuild ? 'SkiAssistantAlt' : 'SkiAssistant',
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

// Hash history for GitHub Pages (no server routing); web history everywhere else.
// Don't pass BASE_URL to hash history — it only applies to the path, not the hash.
const history = isStaticBuild
  ? createWebHashHistory()
  : createWebHistory(import.meta.env.BASE_URL)

const router = createRouter({ history, routes })

export default router
