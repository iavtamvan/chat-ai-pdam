<script setup lang="ts">
import { useAuthStore } from '~/composables/useAuth'

definePageMeta({
  layout: 'default',
  title: 'Login'
})

const authStore = useAuthStore()
const router = useRouter()

const form = reactive({
  npp: '',
  password: ''
})

const showPassword = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  errorMessage.value = ''
  
  if (!form.npp || !form.password) {
    errorMessage.value = 'NPP dan Password harus diisi'
    return
  }

  const result = await authStore.login(form.npp, form.password)
  
  if (result.success) {
    router.push('/admin')
  } else {
    errorMessage.value = result.message || 'Login gagal'
  }
}

const handleGuestAccess = async () => {
  const result = await authStore.getGuestToken()
  if (result.success) {
    router.push('/')
  }
}

// Redirect if already logged in
onMounted(() => {
  if (authStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-primary-600 via-primary-700 to-cyan-700">
    <!-- Background Pattern -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-400/10 rounded-full blur-3xl"></div>
    </div>

    <div class="relative w-full max-w-md">
      <!-- Logo Card -->
      <div class="text-center mb-8">
        <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-2xl">
          <Icon name="heroicons:chat-bubble-left-right" class="w-10 h-10 text-white" />
        </div>
        <h1 class="text-3xl font-bold text-white mb-2">PDAM Chatbot AI</h1>
        <p class="text-white/70">Tirta Moedal Kota Semarang</p>
      </div>

      <!-- Login Card -->
      <div class="bg-white rounded-3xl shadow-2xl p-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Selamat Datang</h2>
        <p class="text-gray-500 mb-6">Masuk untuk mengakses fitur admin</p>

        <!-- Error Message -->
        <div 
          v-if="errorMessage" 
          class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm flex items-center gap-2"
        >
          <Icon name="heroicons:exclamation-circle" class="w-5 h-5 flex-shrink-0" />
          {{ errorMessage }}
        </div>

        <!-- Login Form -->
        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- NPP Input -->
          <div>
            <label for="npp" class="block text-sm font-medium text-gray-700 mb-2">
              Nomor Pokok Pegawai (NPP)
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Icon name="heroicons:identification" class="w-5 h-5 text-gray-400" />
              </div>
              <input
                id="npp"
                v-model="form.npp"
                type="text"
                placeholder="Masukkan NPP"
                class="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                :disabled="authStore.isLoading"
              />
            </div>
          </div>

          <!-- Password Input -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Icon name="heroicons:lock-closed" class="w-5 h-5 text-gray-400" />
              </div>
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Masukkan password"
                class="w-full pl-12 pr-12 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                :disabled="authStore.isLoading"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-4 flex items-center"
              >
                <Icon 
                  :name="showPassword ? 'heroicons:eye-slash' : 'heroicons:eye'" 
                  class="w-5 h-5 text-gray-400 hover:text-gray-600" 
                />
              </button>
            </div>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="authStore.isLoading"
            class="w-full py-3 px-4 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-semibold rounded-xl hover:from-primary-600 hover:to-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary-500/30"
          >
            <span v-if="authStore.isLoading" class="flex items-center justify-center gap-2">
              <Icon name="heroicons:arrow-path" class="w-5 h-5 animate-spin" />
              Memproses...
            </span>
            <span v-else>Masuk</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="relative my-6">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-200"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-4 bg-white text-gray-500">atau</span>
          </div>
        </div>

        <!-- Guest Access -->
        <button
          @click="handleGuestAccess"
          :disabled="authStore.isLoading"
          class="w-full py-3 px-4 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-all disabled:opacity-50"
        >
          Lanjutkan sebagai Tamu
        </button>

        <!-- Help Text -->
        <p class="mt-6 text-center text-sm text-gray-500">
          Butuh bantuan? Hubungi 
          <a href="tel:+62248311113" class="text-primary-600 hover:underline">(024) 8311113</a>
        </p>
      </div>

      <!-- Back to Chat -->
      <div class="text-center mt-6">
        <NuxtLink to="/" class="text-white/80 hover:text-white text-sm flex items-center justify-center gap-1">
          <Icon name="heroicons:arrow-left" class="w-4 h-4" />
          Kembali ke Chat
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
