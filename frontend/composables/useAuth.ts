/**
 * Auth Store using Pinia
 * Handles authentication with PDAM API
 */

import { defineStore } from 'pinia'

export interface User {
  npp: string
  name: string
  jabatan?: string
  satker?: string
  roles?: string[]
}

export interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    isLoading: false,
    error: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.accessToken && !!state.user,
    isAdmin: (state) => state.user?.roles?.includes('admin') || state.user?.roles?.includes('developer'),
    userName: (state) => state.user?.name || 'Guest'
  },

  actions: {
    // Initialize from localStorage
    init() {
      if (process.client) {
        const token = localStorage.getItem('pdam_access_token')
        const refresh = localStorage.getItem('pdam_refresh_token')
        const userData = localStorage.getItem('pdam_user')

        if (token && userData) {
          this.accessToken = token
          this.refreshToken = refresh
          try {
            this.user = JSON.parse(userData)
          } catch {
            this.user = null
          }
        }
      }
    },

    // Login with PDAM credentials
    async login(npp: string, password: string) {
      const config = useRuntimeConfig()
      this.isLoading = true
      this.error = null

      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            npp,
            password,
            hwid: `chatbot-web-${Date.now()}`
          })
        })

        const data = await response.json()

        if (data.success) {
          this.accessToken = data.access_token
          this.refreshToken = data.refresh_token
          this.user = data.user

          // Save to localStorage
          if (process.client) {
            localStorage.setItem('pdam_access_token', data.access_token)
            if (data.refresh_token) {
              localStorage.setItem('pdam_refresh_token', data.refresh_token)
            }
            localStorage.setItem('pdam_user', JSON.stringify(data.user))
          }

          return { success: true }
        } else {
          this.error = data.message || 'Login gagal'
          return { success: false, message: this.error }
        }
      } catch (error: any) {
        this.error = error.message || 'Terjadi kesalahan'
        return { success: false, message: this.error }
      } finally {
        this.isLoading = false
      }
    },

    // Get guest token for public access
    async getGuestToken() {
      const config = useRuntimeConfig()
      this.isLoading = true

      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/guest-token`, {
          method: 'POST'
        })

        const data = await response.json()

        if (data.success) {
          this.accessToken = data.access_token
          this.user = {
            npp: data.guest_id,
            name: 'Guest',
            roles: ['guest']
          }

          if (process.client) {
            localStorage.setItem('pdam_access_token', data.access_token)
            localStorage.setItem('pdam_user', JSON.stringify(this.user))
          }

          return { success: true }
        }
        return { success: false }
      } catch (error: any) {
        return { success: false, message: error.message }
      } finally {
        this.isLoading = false
      }
    },

    // Validate current token
    async validateToken() {
      if (!this.accessToken) return false

      const config = useRuntimeConfig()

      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/validate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            access_token: this.accessToken
          })
        })

        const data = await response.json()
        return data.valid === true
      } catch {
        return false
      }
    },

    // Refresh token
    async refreshAccessToken() {
      if (!this.refreshToken) return false

      const config = useRuntimeConfig()

      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            refresh_token: this.refreshToken
          })
        })

        const data = await response.json()

        if (data.success) {
          this.accessToken = data.access_token
          if (data.refresh_token) {
            this.refreshToken = data.refresh_token
          }

          if (process.client) {
            localStorage.setItem('pdam_access_token', data.access_token)
            if (data.refresh_token) {
              localStorage.setItem('pdam_refresh_token', data.refresh_token)
            }
          }

          return true
        }
        return false
      } catch {
        return false
      }
    },

    // Logout
    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.error = null

      if (process.client) {
        localStorage.removeItem('pdam_access_token')
        localStorage.removeItem('pdam_refresh_token')
        localStorage.removeItem('pdam_user')
      }

      // Redirect to home
      navigateTo('/')
    }
  }
})

// Composable wrapper
export function useAuth() {
  const store = useAuthStore()
  
  // Initialize on client
  if (process.client) {
    store.init()
  }

  return store
}
