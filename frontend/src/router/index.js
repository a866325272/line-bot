/**
 * Vue Router 設定
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'accounting',
        name: 'Accounting',
        component: () => import('../views/AccountingView.vue'),
      },
      {
        path: 'detail',
        name: 'Detail',
        component: () => import('../views/DetailView.vue'),
      },
      {
        path: 'monthly',
        name: 'Monthly',
        component: () => import('../views/MonthlyView.vue'),
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('../views/StatisticsView.vue'),
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('../views/CategoryView.vue'),
      },
      {
        path: 'budget',
        name: 'Budget',
        component: () => import('../views/BudgetView.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/SettingsView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory('/line-bot/'),
  routes,
})

// Navigation Guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 首次載入時嘗試恢復登入狀態
  if (!authStore.isAuthenticated && to.meta.requiresAuth !== false) {
    await authStore.tryRestore()
  }

  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
