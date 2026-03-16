import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Project from '../views/Project.vue'
import Wiki from '../views/Wiki.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/wiki', name: 'Wiki', component: Wiki },
  { path: '/project/:projectId', name: 'Project', component: Project, props: true },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
