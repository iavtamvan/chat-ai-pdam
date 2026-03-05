// ============================================
// PDAM Chatbot AI - Nuxt.js 3 Configuration
// ============================================

export default defineNuxtConfig({
  // Application metadata
  app: {
    head: {
      title: 'PDAM Chatbot AI - Tirta Moedal Kota Semarang',
      titleTemplate: '%s | PDAM Semarang',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Chatbot AI PDAM Tirta Moedal Kota Semarang - Layanan informasi 24/7' },
        { name: 'theme-color', content: '#0066CC' },
        { property: 'og:title', content: 'PDAM Chatbot AI Semarang' },
        { property: 'og:description', content: 'Asisten virtual untuk layanan PDAM Kota Semarang' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { 
          rel: 'stylesheet', 
          href: 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap'
        }
      ]
    }
  },

  // Runtime config
  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8000',
      appName: 'PDAM Chatbot AI'
    }
  },

  // CSS
  css: [
    '~/assets/css/main.css'
  ],

  // Modules
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    'nuxt-icon'
  ],

  // Tailwind CSS
  tailwindcss: {
    cssPath: '~/assets/css/tailwind.css',
    configPath: 'tailwind.config.js',
  },

  // Build configuration
  build: {
    transpile: []
  },

  // SSR configuration - Set to false for SPA mode
  ssr: false,

  // Dev tools
  devtools: { enabled: true },

  // TypeScript
  typescript: {
    strict: true
  },

  // Compatibility
  compatibilityDate: '2024-01-01'
})
