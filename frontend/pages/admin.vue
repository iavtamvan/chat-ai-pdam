<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-800">PDAM Chatbot</h1>
              <p class="text-xs text-gray-500">Tirta Moedal Semarang</p>
            </div>
          </div>

          <nav class="flex items-center space-x-6">
            <NuxtLink to="/" class="text-gray-600 hover:text-blue-600 font-medium">Chat</NuxtLink>
            <NuxtLink to="/admin" class="text-blue-600 font-medium">Admin</NuxtLink>
          </nav>

          <div class="flex items-center space-x-4">
            <!-- Enterprise Settings Button -->
            <NuxtLink
                to="/enterprise"
                class="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all shadow-md"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <span class="font-medium">Enterprise Settings</span>
              <span class="text-xs bg-white/20 px-2 py-0.5 rounded">AI, API, Tokens</span>
            </NuxtLink>

            <div class="flex items-center space-x-2 text-gray-600">
              <span class="text-sm font-medium">{{ auth.userName }}</span>
              <span class="text-xs bg-gray-100 px-2 py-1 rounded">{{ userRole }}</span>
            </div>
            <button @click="handleLogout" class="p-2 text-gray-400 hover:text-red-500">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-gray-800">Admin Dashboard</h2>
        <p class="text-gray-600">Kelola dokumen dan training AI chatbot</p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-gray-800">{{ stats.documents }}</p>
              <p class="text-sm text-gray-500">Dokumen</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-gray-800">{{ stats.chunks }}</p>
              <p class="text-sm text-gray-500">Chunks</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-gray-800">{{ stats.models }}</p>
              <p class="text-sm text-gray-500">Model AI</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div class="flex items-center space-x-4">
            <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-gray-800">{{ stats.storage }}</p>
              <p class="text-sm text-gray-500">Storage</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100">
        <div class="border-b border-gray-200">
          <nav class="flex space-x-8 px-6">
            <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                'py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2',
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              ]"
            >
              <span>{{ tab.icon }}</span>
              <span>{{ tab.name }}</span>
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="p-6">
          <!-- Documents Tab -->
          <div v-if="activeTab === 'documents'">
            <div class="flex justify-between items-center mb-6">
              <h3 class="text-lg font-semibold">Dokumen Training</h3>
              <button
                  @click="refreshDocuments"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                <span>Refresh</span>
              </button>
            </div>

            <div v-if="documents.length === 0" class="text-center py-12 text-gray-500">
              <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <p>Belum ada dokumen. Upload dokumen di tab Upload.</p>
            </div>

            <div v-else class="space-y-3">
              <div
                  v-for="doc in documents"
                  :key="doc.id"
                  class="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ doc.title || doc.filename }}</p>
                    <p class="text-sm text-gray-500">{{ doc.chunks || 0 }} chunks • {{ formatDate(doc.created_at || doc.uploaded_at) }}</p>
                  </div>
                </div>
                <button
                    @click="deleteDocument(doc.id)"
                    class="p-2 text-red-500 hover:bg-red-50 rounded"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Upload Tab -->
          <div v-if="activeTab === 'upload'">
            <h3 class="text-lg font-semibold mb-6">Upload Dokumen</h3>

            <div
                @drop.prevent="handleDrop"
                @dragover.prevent="isDragging = true"
                @dragleave="isDragging = false"
                :class="[
                'border-2 border-dashed rounded-xl p-12 text-center transition-colors',
                isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              ]"
            >
              <input
                  type="file"
                  ref="fileInput"
                  @change="handleFileSelect"
                  accept=".pdf,.txt,.docx,.doc,.md"
                  class="hidden"
                  multiple
              />

              <svg class="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>

              <p class="text-gray-600 mb-2">Drag & drop file atau</p>
              <button
                  @click="$refs.fileInput.click()"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Pilih File
              </button>
              <p class="text-sm text-gray-500 mt-2">PDF, TXT, DOCX, MD (Max 10MB)</p>
            </div>

            <!-- Upload Progress -->
            <div v-if="uploadProgress > 0" class="mt-4">
              <div class="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{{ uploadProgress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                    class="bg-blue-600 h-2 rounded-full transition-all"
                    :style="{ width: uploadProgress + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Model AI Tab -->
          <div v-if="activeTab === 'models'">
            <div class="flex justify-between items-center mb-6">
              <h3 class="text-lg font-semibold">Model AI</h3>
              <button
                  @click="checkOllamaModels"
                  class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                <span>Check Status</span>
              </button>
            </div>

            <div class="space-y-4">
              <div
                  v-for="model in availableModels"
                  :key="model.name"
                  class="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <div class="flex items-center space-x-2">
                    <p class="font-medium text-gray-800">{{ model.name }}</p>
                    <span
                        v-if="model.installed"
                        class="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full"
                    >
                      Installed
                    </span>
                  </div>
                  <p class="text-sm text-gray-500">{{ model.description }}</p>
                  <p class="text-xs text-gray-400">Size: {{ model.size }} | {{ model.features }}</p>
                </div>
                <button
                    v-if="!model.installed"
                    @click="downloadModel(model.name)"
                    :disabled="downloadingModel === model.name"
                    class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 flex items-center space-x-2"
                >
                  <svg v-if="downloadingModel === model.name" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{{ downloadingModel === model.name ? 'Downloading...' : 'Download' }}</span>
                </button>
                <span v-else class="text-green-600 flex items-center space-x-1">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>
                  <span>Installed</span>
                </span>
              </div>
            </div>
          </div>

          <!-- Training Tab -->
          <div v-if="activeTab === 'training'">
            <h3 class="text-lg font-semibold mb-6">Training Status</h3>

            <div class="bg-gray-50 rounded-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <div>
                  <p class="font-medium text-gray-800">Vector Database</p>
                  <p class="text-sm text-gray-500">Status embedding dokumen</p>
                </div>
                <span
                    :class="[
                    'px-3 py-1 rounded-full text-sm',
                    trainingStatus.ready ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  ]"
                >
                  {{ trainingStatus.ready ? 'Ready' : 'Processing' }}
                </span>
              </div>

              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-500">Total Dokumen:</span>
                  <span class="font-medium">{{ trainingStatus.documents }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">Total Chunks:</span>
                  <span class="font-medium">{{ trainingStatus.chunks }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">Last Updated:</span>
                  <span class="font-medium">{{ trainingStatus.lastUpdated || 'Never' }}</span>
                </div>
              </div>

              <button
                  @click="retrainAll"
                  :disabled="isRetraining"
                  class="mt-4 w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {{ isRetraining ? 'Retraining...' : 'Retrain All Documents' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Toast Notification -->
    <div
        v-if="toast.show"
        :class="[
        'fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white transition-all z-50',
        toast.type === 'success' ? 'bg-green-600' : toast.type === 'error' ? 'bg-red-600' : 'bg-blue-600'
      ]"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '~/composables/useAuth'

// =============================================
// FIX: Disable default layout (no double header)
// =============================================
definePageMeta({
  layout: false
})

const router = useRouter()
const auth = useAuth()

// Computed for user role
const userRole = computed(() => {
  return auth.user?.jabatan || auth.user?.satker || 'Staf'
})

// Check auth on mount
onMounted(() => {
  if (!auth.isLoggedIn) {
    router.push('/login')
    return
  }
  loadDashboardData()
})

// State
const activeTab = ref('documents')
const isDragging = ref(false)
const uploadProgress = ref(0)
const downloadingModel = ref(null)
const isRetraining = ref(false)

const tabs = [
  { id: 'documents', name: 'Dokumen', icon: '📄' },
  { id: 'upload', name: 'Upload', icon: '📁' },
  { id: 'models', name: 'Model AI', icon: '🤖' },
  { id: 'training', name: 'Training', icon: '🎯' }
]

const stats = ref({
  documents: 0,
  chunks: 0,
  models: 0,
  storage: '0 MB'
})

const documents = ref([])

const availableModels = ref([
  { name: 'llama3.2:3b', description: 'Recommended - Fast and good quality', size: '2GB', features: 'Multilingual (termasuk Indonesia)', installed: false },
  { name: 'llama3.2:1b', description: 'Very fast, good for limited resources', size: '1.3GB', features: 'Multilingual', installed: false },
  { name: 'mistral:7b', description: 'High quality, needs more RAM', size: '4.1GB', features: 'Multilingual', installed: false },
  { name: 'gemma2:2b', description: "Google's efficient model", size: '1.6GB', features: 'Multilingual', installed: false },
  { name: 'qwen2.5:3b', description: 'Good for Asian languages', size: '1.9GB', features: 'Multilingual (bagus untuk Indonesia)', installed: false },
  { name: 'phi3:mini', description: "Microsoft's efficient model", size: '2.3GB', features: 'Multilingual', installed: false },
  { name: 'nomic-embed-text', description: 'Embedding model for RAG', size: '274MB', features: 'Multilingual', installed: false }
])

const trainingStatus = ref({
  ready: false,
  documents: 0,
  chunks: 0,
  lastUpdated: null
})

const toast = ref({
  show: false,
  message: '',
  type: 'info'
})

// API helpers
const API_URL = 'http://localhost:8000/api'

function getAuthHeaders() {
  return {
    'Authorization': `Bearer ${auth.accessToken}`,
    'Content-Type': 'application/json'
  }
}

function showToast(message, type = 'info') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    })
  } catch (e) {
    return '-'
  }
}

// Load dashboard data
async function loadDashboardData() {
  await Promise.all([
    refreshDocuments(),
    checkOllamaModels(),
    loadTrainingStatus()
  ])
}

// =============================================
// FIX: Changed endpoint from /api/documents/ to /api/training/documents
// =============================================
async function refreshDocuments() {
  try {
    // Ambil daftar file dari database dokumen utama
    const listResponse = await fetch(`${API_URL}/documents/list?limit=100`, {
      headers: getAuthHeaders()
    })

    if (listResponse.ok) {
      const listData = await listResponse.json()
      documents.value = listData.documents || []
    }

    // Ambil statistik (Total Chunks, Storage, dll)
    const statsResponse = await fetch(`${API_URL}/documents/stats`, {
      headers: getAuthHeaders()
    })

    if (statsResponse.ok) {
      const statsData = await statsResponse.json()
      stats.value.documents = statsData.unique_documents || documents.value.length
      stats.value.chunks = statsData.total_chunks || 0
      stats.value.storage = `${statsData.storage_used_mb || 0} MB`
    }
  } catch (error) {
    console.error('Failed to load documents:', error)
  }
}

async function checkOllamaModels() {
  try {
    const response = await fetch(`${API_URL}/training/models`)
    if (response.ok) {
      const data = await response.json()
      const installedModels = data.models || []

      availableModels.value.forEach(model => {
        model.installed = installedModels.some(m =>
            m.name === model.name ||
            m.name === `${model.name}:latest` ||
            (m.name && m.name.startsWith(model.name.split(':')[0]))
        )
      })

      stats.value.models = installedModels.length
    }
  } catch (error) {
    console.error('Failed to check Ollama models:', error)
  }
}

async function loadTrainingStatus() {
  try {
    const response = await fetch(`${API_URL}/training/status`, {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      trainingStatus.value = {
        ready: data.status === 'completed' || data.status === 'idle',
        documents: data.total_documents || stats.value.documents,
        chunks: data.total_chunks || stats.value.chunks,
        lastUpdated: data.last_updated || data.lastUpdated
      }
    }
  } catch (error) {
    console.error('Failed to load training status:', error)
  }
}

// =============================================
// FIX: Changed to send JSON body properly
// =============================================
async function downloadModel(modelName) {
  downloadingModel.value = modelName
  showToast(`Downloading ${modelName}... This may take a few minutes.`, 'info')

  try {
    const response = await fetch(`${API_URL}/training/pull-model`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ model_name: modelName })
    })

    if (!response.ok) {
      let errorMessage = `HTTP Error: ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData?.detail || errorData?.message || errorData?.error || errorMessage
      } catch (e) {}
      throw new Error(errorMessage)
    }

    const data = await response.json()

    if (data?.error) {
      throw new Error(data.error)
    }

    showToast(`${modelName} berhasil di-download!`, 'success')

    const model = availableModels.value.find(m => m.name === modelName)
    if (model) {
      model.installed = true
    }
    stats.value.models++

    await checkOllamaModels()

  } catch (error) {
    const errorMsg = error?.message || String(error) || 'Unknown error'
    console.error('Download model error:', error)
    showToast(`Gagal download ${modelName}: ${errorMsg}`, 'error')
  } finally {
    downloadingModel.value = null
  }
}

// File upload
async function handleFileSelect(event) {
  const files = event.target?.files
  if (files && files.length > 0) {
    await uploadFiles(files)
  }
}

function handleDrop(event) {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    uploadFiles(files)
  }
}

async function uploadFiles(files) {
  for (const file of files) {
    await uploadSingleFile(file)
  }
  await refreshDocuments()
}

// =============================================
// FIX: Changed endpoint from /api/documents/upload to /api/training/documents/upload
// =============================================
async function uploadSingleFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  uploadProgress.value = 10

  try {
    const response = await fetch(`${API_URL}/training/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${auth.accessToken}`
      },
      body: formData
    })

    uploadProgress.value = 90

    if (response.ok) {
      showToast(`${file.name} berhasil diupload!`, 'success')
    } else {
      let errorMsg = 'Upload failed'
      try {
        const error = await response.json()
        errorMsg = error?.detail || error?.message || errorMsg
      } catch (e) {}
      throw new Error(errorMsg)
    }
  } catch (error) {
    showToast(`Gagal upload ${file.name}: ${error?.message || error}`, 'error')
  } finally {
    uploadProgress.value = 0
  }
}

// =============================================
// FIX: Changed endpoint from /api/documents/{id} to /api/training/documents/{id}
// =============================================
async function deleteDocument(docId) {
  if (!confirm('Hapus dokumen ini? File fisik dan memori AI akan dihapus permanen.')) return

  try {
    // FIX: Menggunakan endpoint /documents/, BUKAN /training/documents/
    const response = await fetch(`${API_URL}/documents/${docId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })

    if (response.ok) {
      showToast('Dokumen dan memori AI berhasil dihapus', 'success')
      await refreshDocuments()
      await loadTrainingStatus() // Refresh tab training agar sinkron
    } else {
      throw new Error('Delete failed')
    }
  } catch (error) {
    showToast('Gagal menghapus dokumen', 'error')
  }
}

async function retrainAll() {
  isRetraining.value = true
  showToast('Memulai retraining...', 'info')

  try {
    const response = await fetch(`${API_URL}/training/retrain`, {
      method: 'POST',
      headers: getAuthHeaders()
    })

    if (response.ok) {
      showToast('Retraining selesai!', 'success')
      await loadTrainingStatus()
    } else {
      throw new Error('Retrain failed')
    }
  } catch (error) {
    showToast('Gagal melakukan retraining', 'error')
  } finally {
    isRetraining.value = false
  }
}

function handleLogout() {
  auth.logout()
}
</script>