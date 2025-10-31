import { createRouter, createWebHistory } from 'vue-router'
import AnalysisView from "@/view/AnalysisView.vue";
import HomeView from "@/view/HomeView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {path: '/analysis', component: AnalysisView},
    {path: '/home', component: HomeView},
    {path: '/', redirect: '/home'}
  ],
})

export default router
