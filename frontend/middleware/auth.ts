/**
 * Auth Middleware
 * Protects routes that require authentication
 */

import { useAuthStore } from '~/composables/useAuth'

export default defineNuxtRouteMiddleware((to, from) => {
  const authStore = useAuthStore()
  
  // Initialize auth state
  if (process.client) {
    authStore.init()
  }

  // Check if user is logged in
  if (!authStore.isLoggedIn) {
    // Redirect to login with return URL
    return navigateTo({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  }
})
