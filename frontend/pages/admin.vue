<script setup lang="ts">
import { useAuthStore } from '~/composables/useAuth'

definePageMeta({
  title: 'Admin Dashboard',
  middleware: 'auth'
})

const config = useRuntimeConfig()
const authStore = useAuthStore()

// State
const activeTab = ref('documents')
const isLoading = ref(false)
const stats = ref<any>(null)
const documents = ref<any[]>([])
const models = ref<any>(null)
const trainingStatus = ref<any>(null)

// Upload state
const uploadFiles = ref<File[]>([])
const uploadCategory = ref('general')
const uploadProgress = ref(0)
const uploadMessage = ref('')

// Fetch stats
const fetchStats = async () => {
  try {
    const response = await fetch(`${config.public.apiUrl}/api/documents/stats`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    stats.value = await response.json()
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

// Fetch documents
const fetchDocuments = async () => {
  try {
    const response = await fetch(`${config.public.apiUrl}/api/documents/list`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    const data = await response.json()
    documents.value = data.documents || []
  } catch (error) {
    console.error('Error fetching documents:', error)
  }
}

// Fetch models
const fetchModels = async () => {
  try {
    const response = await fetch(`${config.public.apiUrl}/api/training/models/available`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    models.value = await response.json()
  } catch (error) {
    console.error('Error fetching models:', error)
  }
}

// Fetch training status
const fetchTrainingStatus = async () => {
  try {
    const response = await fetch(`${config.public.apiUrl}/api/training/status`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    trainingStatus.value = await response.json()
  } catch (error) {
    console.error('Error fetching training status:', error)
  }
}

// Handle file upload
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    uploadFiles.value = Array.from(target.files)
  }
}

const handleUpload = async () => {
  if (uploadFiles.value.length === 0) return

  isLoading.value = true
  uploadProgress.value = 0
  uploadMessage.value = ''

  try {
    for (let i = 0; i < uploadFiles.value.length; i++) {
      const file = uploadFiles.value[i]
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', uploadCategory.value)

      const response = await fetch(`${config.public.apiUrl}/api/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authStore.accessToken}`
        },
        body: formData
      })

      const result = await response.json()
      uploadProgress.value = Math.round(((i + 1) / uploadFiles.value.length) * 100)
      
      if (!result.success) {
        uploadMessage.value = `❌ Error: ${result.message}`
      }
    }

    uploadMessage.value = `✅ Berhasil upload ${uploadFiles.value.length} file`
    uploadFiles.value = []
    
    // Refresh data
    await fetchStats()
    await fetchDocuments()
  } catch (error: any) {
    uploadMessage.value = `❌ Error: ${error.message}`
  } finally {
    isLoading.value = false
  }
}

// Delete document
const deleteDocument = async (filename: string) => {
  if (!confirm(`Hapus dokumen "${filename}"?`)) return

  try {
    const response = await fetch(`${config.public.apiUrl}/api/documents/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    
    const result = await response.json()
    if (result.success) {
      await fetchStats()
      await fetchDocuments()
    }
  } catch (error) {
    console.error('Error deleting document:', error)
  }
}

// Pull model
const pullModel = async (modelName: string) => {
  if (!confirm(`Download model "${modelName}"? Ini mungkin membutuhkan waktu beberapa menit.`)) return

  try {
    const response = await fetch(`${config.public.apiUrl}/api/training/pull-model`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ model_name: modelName })
    })
    
    const result = await response.json()
    alert(result.message)
    
    // Start polling for status
    const interval = setInterval(async () => {
      await fetchTrainingStatus()
      if (trainingStatus.value?.current_operations?.status !== 'downloading') {
        clearInterval(interval)
        await fetchModels()
      }
    }, 5000)
  } catch (error) {
    console.error('Error pulling model:', error)
  }
}

// Run benchmark
const runBenchmark = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${config.public.apiUrl}/api/training/benchmark?questions=5`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    const result = await response.json()
    alert(`Benchmark selesai!\n\nTotal waktu: ${result.total_time}s\nRata-rata: ${result.average_time}s per pertanyaan`)
  } catch (error) {
    console.error('Error running benchmark:', error)
  } finally {
    isLoading.value = false
  }
}

// Initialize
onMounted(async () => {
  await Promise.all([
    fetchStats(),
    fetchDocuments(),
    fetchModels(),
    fetchTrainingStatus()
  ])
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
      <p class="text-gray-600 mt-1">Kelola dokumen dan training AI chatbot</p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
            <Icon name="heroicons:document-text" class="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats?.unique_documents || 0 }}</p>
            <p class="text-sm text-gray-500">Dokumen</p>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
            <Icon name="heroicons:cube" class="w-6 h-6 text-green-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats?.total_chunks || 0 }}</p>
            <p class="text-sm text-gray-500">Chunks</p>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
            <Icon name="heroicons:cpu-chip" class="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ models?.installed?.length || 0 }}</p>
            <p class="text-sm text-gray-500">Model AI</p>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-cyan-100 flex items-center justify-center">
            <Icon name="heroicons:server" class="w-6 h-6 text-cyan-600" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900">{{ stats?.storage_used_mb || 0 }} MB</p>
            <p class="text-sm text-gray-500">Storage</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="flex gap-8">
        <button
          @click="activeTab = 'documents'"
          :class="[
            'pb-4 px-1 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'documents' 
              ? 'border-primary-500 text-primary-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          📄 Dokumen
        </button>
        <button
          @click="activeTab = 'upload'"
          :class="[
            'pb-4 px-1 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'upload' 
              ? 'border-primary-500 text-primary-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          ⬆️ Upload
        </button>
        <button
          @click="activeTab = 'models'"
          :class="[
            'pb-4 px-1 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'models' 
              ? 'border-primary-500 text-primary-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          🤖 Model AI
        </button>
        <button
          @click="activeTab = 'training'"
          :class="[
            'pb-4 px-1 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'training' 
              ? 'border-primary-500 text-primary-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          🎯 Training
        </button>
      </nav>
    </div>

    <!-- Documents Tab -->
    <div v-if="activeTab === 'documents'" class="card">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">Daftar Dokumen</h2>
      
      <div v-if="documents.length === 0" class="text-center py-12 text-gray-500">
        <Icon name="heroicons:document" class="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>Belum ada dokumen. Upload dokumen untuk training AI.</p>
      </div>
      
      <div v-else class="space-y-3">
        <div 
          v-for="doc in documents" 
          :key="doc"
          class="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
        >
          <div class="flex items-center gap-3">
            <Icon name="heroicons:document-text" class="w-8 h-8 text-primary-500" />
            <div>
              <p class="font-medium text-gray-900">{{ doc }}</p>
            </div>
          </div>
          <button
            @click="deleteDocument(doc)"
            class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
          >
            <Icon name="heroicons:trash" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Tab -->
    <div v-if="activeTab === 'upload'" class="card">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">Upload Dokumen</h2>
      
      <div class="space-y-6">
        <!-- File Input -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Pilih File
          </label>
          <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-400 transition-colors">
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.md,.jpg,.jpeg,.png"
              @change="handleFileSelect"
              class="hidden"
              id="fileInput"
            />
            <label for="fileInput" class="cursor-pointer">
              <Icon name="heroicons:cloud-arrow-up" class="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p class="text-gray-600">Klik untuk upload atau drag & drop</p>
              <p class="text-sm text-gray-400 mt-1">PDF, Word, Excel, Image, Text (Max 50MB)</p>
            </label>
          </div>
          
          <!-- Selected Files -->
          <div v-if="uploadFiles.length > 0" class="mt-4 space-y-2">
            <div 
              v-for="(file, index) in uploadFiles" 
              :key="index"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span class="text-sm text-gray-700">{{ file.name }}</span>
              <span class="text-xs text-gray-500">{{ (file.size / 1024).toFixed(1) }} KB</span>
            </div>
          </div>
        </div>

        <!-- Category -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Kategori
          </label>
          <select
            v-model="uploadCategory"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500"
          >
            <option value="general">Umum</option>
            <option value="tarif">Tarif & Pembayaran</option>
            <option value="pemasangan">Pemasangan Baru</option>
            <option value="pengaduan">Pengaduan</option>
            <option value="prosedur">Prosedur & SOP</option>
            <option value="faq">FAQ</option>
          </select>
        </div>

        <!-- Progress -->
        <div v-if="uploadProgress > 0" class="space-y-2">
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div 
              class="bg-primary-500 h-2 rounded-full transition-all" 
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
          <p class="text-sm text-gray-600">{{ uploadProgress }}%</p>
        </div>

        <!-- Message -->
        <div v-if="uploadMessage" class="p-4 rounded-xl" :class="uploadMessage.startsWith('✅') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'">
          {{ uploadMessage }}
        </div>

        <!-- Upload Button -->
        <button
          @click="handleUpload"
          :disabled="uploadFiles.length === 0 || isLoading"
          class="btn-primary w-full"
        >
          <span v-if="isLoading">Uploading...</span>
          <span v-else>Upload {{ uploadFiles.length }} File</span>
        </button>
      </div>
    </div>

    <!-- Models Tab -->
    <div v-if="activeTab === 'models'" class="card">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">Model AI</h2>
      
      <div class="space-y-4">
        <div 
          v-for="model in models?.recommended" 
          :key="model.name"
          class="flex items-center justify-between p-4 border border-gray-200 rounded-xl"
        >
          <div>
            <div class="flex items-center gap-2">
              <p class="font-semibold text-gray-900">{{ model.name }}</p>
              <span 
                v-if="model.installed" 
                class="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full"
              >
                Installed
              </span>
              <span 
                v-if="models?.current_chat_model === model.name" 
                class="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded-full"
              >
                Active
              </span>
            </div>
            <p class="text-sm text-gray-500 mt-1">{{ model.description }}</p>
            <p class="text-xs text-gray-400">Size: {{ model.size }} | {{ model.language }}</p>
          </div>
          
          <button
            v-if="!model.installed"
            @click="pullModel(model.name)"
            class="btn-secondary text-sm"
          >
            Download
          </button>
        </div>
      </div>
    </div>

    <!-- Training Tab -->
    <div v-if="activeTab === 'training'" class="card">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">Training & Status</h2>
      
      <div class="grid md:grid-cols-2 gap-6">
        <!-- LLM Status -->
        <div class="p-4 bg-gray-50 rounded-xl">
          <h3 class="font-medium text-gray-900 mb-3">Status LLM</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">Server:</span>
              <span :class="trainingStatus?.llm_status?.healthy ? 'text-green-600' : 'text-red-600'">
                {{ trainingStatus?.llm_status?.healthy ? '✅ Online' : '❌ Offline' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Model:</span>
              <span class="text-gray-900">{{ trainingStatus?.settings?.model }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Embedding:</span>
              <span class="text-gray-900">{{ trainingStatus?.settings?.embedding_model }}</span>
            </div>
          </div>
        </div>

        <!-- Vector DB Status -->
        <div class="p-4 bg-gray-50 rounded-xl">
          <h3 class="font-medium text-gray-900 mb-3">Vector Database</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">Dokumen:</span>
              <span class="text-gray-900">{{ trainingStatus?.document_count || 0 }} chunks</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Chunk Size:</span>
              <span class="text-gray-900">{{ trainingStatus?.settings?.chunk_size }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Top K:</span>
              <span class="text-gray-900">{{ trainingStatus?.settings?.top_k_results }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="mt-6 flex flex-wrap gap-4">
        <button @click="runBenchmark" :disabled="isLoading" class="btn-primary">
          🏃 Run Benchmark
        </button>
        <button @click="fetchTrainingStatus" class="btn-secondary">
          🔄 Refresh Status
        </button>
      </div>
    </div>
  </div>
</template>
