<script setup lang="ts">
import { useAuthStore } from '~/composables/useAuth'

const authStore = useAuthStore()
const route = useRoute()

const isAuthPage = computed(() => route.path === '/login')
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50">
    <!-- Header -->
    <header 
      v-if="!isAuthPage" 
      class="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-gray-100"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <NuxtLink to="/" class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg shadow-primary-500/20">
              <Icon name="heroicons:chat-bubble-left-right" class="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 class="font-bold text-gray-900 text-lg leading-tight">PDAM Chatbot</h1>
              <p class="text-xs text-gray-500">Tirta Moedal Semarang</p>
            </div>
          </NuxtLink>

          <!-- Navigation -->
          <nav class="hidden md:flex items-center gap-6">
            <NuxtLink 
              to="/" 
              class="text-gray-600 hover:text-primary-600 font-medium transition-colors"
              active-class="text-primary-600"
            >
              Chat
            </NuxtLink>
            <NuxtLink 
              v-if="authStore.isLoggedIn" 
              to="/admin" 
              class="text-gray-600 hover:text-primary-600 font-medium transition-colors"
              active-class="text-primary-600"
            >
              Admin
            </NuxtLink>
          </nav>

          <!-- User Menu -->
          <div class="flex items-center gap-3">
            <template v-if="authStore.isLoggedIn">
              <div class="hidden sm:block text-right">
                <p class="text-sm font-medium text-gray-900">{{ authStore.user?.name }}</p>
                <p class="text-xs text-gray-500">{{ authStore.user?.jabatan }}</p>
              </div>
              <button 
                @click="authStore.logout()"
                class="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                title="Logout"
              >
                <Icon name="heroicons:arrow-right-on-rectangle" class="w-5 h-5" />
              </button>
            </template>
            <template v-else>
              <NuxtLink 
                to="/login" 
                class="btn-primary text-sm"
              >
                Login
              </NuxtLink>
            </template>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main>
      <slot />
    </main>

    <!-- Footer -->
    <footer 
      v-if="!isAuthPage" 
      class="py-6 text-center text-sm text-gray-500 border-t border-gray-100 bg-white/50"
    >
      <p>© {{ new Date().getFullYear() }} PDAM Tirta Moedal Kota Semarang</p>
      <p class="mt-1">
        Hubungi Call Center: 
        <a href="tel:+62248311113" class="text-primary-600 hover:underline">(024) 8311113</a>
      </p>
    </footer>
  </div>
</template>
