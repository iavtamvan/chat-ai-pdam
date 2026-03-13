<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-900">Enterprise Settings</h1>
            <p class="text-sm text-gray-500">Kelola AI, API, dan Embed Token</p>
          </div>
        </div>
        <NuxtLink to="/admin" class="text-blue-600 hover:text-blue-700 flex items-center">
          ← Back to Admin
        </NuxtLink>
      </div>
    </header>

    <!-- Tabs -->
    <div class="max-w-7xl mx-auto px-4 mt-6">
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex space-x-8">
          <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'flex items-center py-4 px-1 border-b-2 font-medium text-sm cursor-pointer'
            ]"
          >
            <span class="mr-2">{{ tab.icon }}</span>
            {{ tab.name }}
            <span v-if="tab.count" class="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
              {{ tab.count }}
            </span>
          </button>
        </nav>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 py-6">

      <!-- ==================== AI PROVIDERS TAB ==================== -->
      <div v-if="activeTab === 'ai-providers'" class="space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold">AI Providers</h2>
            <p class="text-sm text-gray-500">Kelola integrasi dengan berbagai AI provider</p>
          </div>
          <button
              @click="openAddProviderModal"
              class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center cursor-pointer"
          >
            + Add Provider
          </button>
        </div>

        <!-- Free Options Info -->
        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
          <div class="flex items-start">
            <span class="text-green-600 mr-3 text-xl">💡</span>
            <div>
              <h3 class="font-medium text-green-800">Free API Options</h3>
              <p class="text-sm text-green-700 mt-1">
                Untuk testing gratis, gunakan:
                <strong>Groq</strong> (14,400 req/day),
                <strong>Gemini</strong> (15 req/min), atau
                <strong>Ollama</strong> (unlimited, local)
              </p>
              <button @click="showFreeOptionsModal = true" class="text-green-600 text-sm mt-2 hover:underline cursor-pointer">
                Lihat semua opsi gratis →
              </button>
            </div>
          </div>
        </div>

        <!-- Providers List -->
        <div class="grid gap-4">
          <div
              v-for="provider in aiProviders"
              :key="provider.id"
              class="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
          >
            <div class="flex justify-between items-start">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-100 text-blue-600">
                  🤖
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <h3 class="font-medium">{{ provider.name }}</h3>
                    <span v-if="provider.is_default" class="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded">
                      Default
                    </span>
                    <span :class="[
                      provider.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600',
                      'text-xs px-2 py-0.5 rounded'
                    ]">
                      {{ provider.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-500">
                    {{ provider.provider_type }} • {{ provider.default_model }}
                  </p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <button @click="testProvider(provider.id)" class="text-blue-600 hover:bg-blue-50 p-2 rounded" title="Test">▶️</button>
                <button @click="toggleProvider(provider.id)" class="text-yellow-600 hover:bg-yellow-50 p-2 rounded" title="Toggle">⚡</button>
                <button @click="setDefaultProvider(provider.id)" class="text-green-600 hover:bg-green-50 p-2 rounded" title="Set Default">⭐</button>
                <button @click="deleteProvider(provider.id)" class="text-red-600 hover:bg-red-50 p-2 rounded" title="Delete">🗑️</button>
              </div>
            </div>
            <div class="mt-3 flex items-center text-sm text-gray-500 space-x-4">
              <span>{{ provider.total_requests || 0 }} requests</span>
            </div>
          </div>

          <div v-if="aiProviders.length === 0" class="text-center py-12 bg-white rounded-lg border">
            <div class="text-4xl mb-2">🤖</div>
            <p class="text-gray-500">Belum ada AI provider</p>
            <button @click="openAddProviderModal" class="mt-4 text-blue-600 hover:underline cursor-pointer">
              + Add your first provider
            </button>
          </div>
        </div>
      </div>

      <!-- ==================== API INTEGRATIONS TAB ==================== -->
      <div v-if="activeTab === 'api-integrations'" class="space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold">API Integrations</h2>
            <p class="text-sm text-gray-500">Konfigurasi API internal PDAM - AI akan otomatis panggil API berdasarkan keyword</p>
          </div>
          <button
              @click="openAddApiModal"
              class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center cursor-pointer"
          >
            + Add API Endpoint
          </button>
        </div>

        <!-- How it works -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 class="font-medium text-blue-800 mb-2">🔄 Cara Kerja</h3>
          <ol class="text-sm text-blue-700 list-decimal list-inside space-y-1">
            <li>User ketik: "cek tagihan 07600026"</li>
            <li>AI deteksi keyword "tagihan" → match dengan API "Cek Tagihan"</li>
            <li>AI extract nomor pelanggan "07600026" dari pesan</li>
            <li>API dipanggil otomatis → hasil ditampilkan ke user</li>
          </ol>
        </div>

        <!-- API Templates -->
        <div class="bg-gray-50 border rounded-lg p-4">
          <h3 class="font-medium text-gray-800 mb-2">Quick Templates</h3>
          <div class="flex flex-wrap gap-2">
            <button
                v-for="template in apiTemplates"
                :key="template.name"
                @click="applyTemplate(template)"
                class="bg-white px-3 py-1 rounded border hover:bg-blue-100 text-sm cursor-pointer"
            >
              {{ template.name }}
            </button>
          </div>
        </div>

        <!-- API Endpoints List -->
        <div class="space-y-3">
          <div
              v-for="endpoint in apiEndpoints"
              :key="endpoint.id"
              class="bg-white rounded-lg border p-4"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center space-x-2 mb-1">
                  <span :class="[getMethodColor(endpoint.method), 'text-xs px-2 py-0.5 rounded font-medium']">
                    {{ endpoint.method }}
                  </span>
                  <h3 class="font-medium">{{ endpoint.name }}</h3>
                  <span :class="[endpoint.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600', 'text-xs px-2 py-0.5 rounded']">
                    {{ endpoint.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 font-mono truncate">{{ endpoint.url }}</p>
                <div class="flex flex-wrap gap-1 mt-2">
                  <span v-for="kw in (endpoint.trigger_keywords || [])" :key="kw" class="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded">
                    {{ kw }}
                  </span>
                </div>
              </div>
              <div class="flex items-center space-x-1">
                <button @click="editApiEndpoint(endpoint)" class="text-blue-600 hover:bg-blue-50 p-2 rounded" title="Edit">✏️</button>
                <button @click="testApiEndpoint(endpoint.id)" class="text-green-600 hover:bg-green-50 p-2 rounded" title="Test">▶️</button>
                <button @click="toggleApiEndpoint(endpoint.id)" class="text-yellow-600 hover:bg-yellow-50 p-2 rounded" title="Toggle">⚡</button>
                <button @click="deleteApiEndpoint(endpoint.id)" class="text-red-600 hover:bg-red-50 p-2 rounded" title="Delete">🗑️</button>
              </div>
            </div>
          </div>

          <div v-if="apiEndpoints.length === 0" class="text-center py-12 bg-white rounded-lg border">
            <div class="text-4xl mb-2">🔗</div>
            <p class="text-gray-500">Belum ada API endpoint</p>
          </div>
        </div>
      </div>

      <!-- ==================== EMBED TOKENS TAB ==================== -->
      <div v-if="activeTab === 'embed-tokens'" class="space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold">Embed Tokens</h2>
            <p class="text-sm text-gray-500">Token untuk widget dan integrasi WhatsApp</p>
          </div>
          <div class="flex space-x-2">
            <button @click="showWidgetModal = true" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 cursor-pointer">
              🌐 Widget Token
            </button>
            <button @click="showWhatsAppModal = true" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 cursor-pointer">
              📱 WhatsApp Token
            </button>
          </div>
        </div>

        <!-- Tokens List -->
        <div class="space-y-3">
          <div v-for="token in embedTokens" :key="token.id" class="bg-white rounded-lg border p-4">
            <div class="flex justify-between items-start">
              <div>
                <div class="flex items-center space-x-2">
                  <span>{{ token.integration_type === 'whatsapp' ? '📱' : '🌐' }}</span>
                  <h3 class="font-medium">{{ token.name }}</h3>
                  <span :class="[token.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600', 'text-xs px-2 py-0.5 rounded']">
                    {{ token.status }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 mt-1 font-mono">{{ token.token_masked || token.token }}</p>
              </div>
              <div class="flex items-center space-x-1">
                <button @click="copyTokenCode(token)" class="text-blue-600 hover:bg-blue-50 p-2 rounded">📋</button>
                <button @click="deleteToken(token.id)" class="text-red-600 hover:bg-red-50 p-2 rounded">🗑️</button>
              </div>
            </div>
          </div>

          <div v-if="embedTokens.length === 0" class="text-center py-12 bg-white rounded-lg border">
            <div class="text-4xl mb-2">🔑</div>
            <p class="text-gray-500">Belum ada embed token</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL: ADD PROVIDER ==================== -->
    <div v-if="showAddProviderModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-lg">
        <h3 class="text-lg font-semibold mb-4">Add AI Provider</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Provider Type</label>
            <select v-model="newProvider.provider_type" @change="onProviderTypeChange" class="w-full border rounded-lg px-3 py-2">
              <option value="groq">Groq (Free, Fast) ⭐</option>
              <option value="gemini">Google Gemini (Free tier)</option>
              <option value="openrouter">OpenRouter</option>
              <option value="deepseek">DeepSeek</option>
              <option value="openai">OpenAI</option>
              <option value="claude">Claude</option>
              <option value="ollama">Ollama (Local)</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Name</label>
            <input v-model="newProvider.name" type="text" class="w-full border rounded-lg px-3 py-2" placeholder="My Provider">
          </div>
          <div v-if="newProvider.provider_type !== 'ollama'">
            <label class="block text-sm font-medium mb-1">API Key</label>
            <input v-model="newProvider.api_key" type="password" class="w-full border rounded-lg px-3 py-2" placeholder="sk-...">
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Default Model</label>
            <select v-model="newProvider.default_model" class="w-full border rounded-lg px-3 py-2">
              <option v-for="model in currentProviderModels" :key="model.id" :value="model.id">
                {{ model.display_name }}
              </option>
            </select>
            <p v-if="newProvider.provider_type === 'ollama' && ollamaModelsLoading" class="text-xs text-gray-500 mt-1">
              Loading installed models...
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <label class="flex items-center cursor-pointer">
              <input type="checkbox" v-model="newProvider.is_active" class="mr-2"> Active
            </label>
            <label class="flex items-center cursor-pointer">
              <input type="checkbox" v-model="newProvider.is_default" class="mr-2"> Set as Default
            </label>
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showAddProviderModal = false" class="px-4 py-2 border rounded-lg cursor-pointer">Cancel</button>
          <button @click="createProvider" class="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer">Add Provider</button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL: ADD/EDIT API ENDPOINT ==================== -->
    <div v-if="showAddApiModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto m-4">
        <div class="p-6 border-b sticky top-0 bg-white">
          <h3 class="text-lg font-semibold">{{ editingEndpoint ? 'Edit' : 'Add' }} API Endpoint</h3>
          <p class="text-sm text-gray-500">Konfigurasi API seperti Postman</p>
        </div>

        <div class="p-6 space-y-5">
          <!-- Row 1: Name & Category -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input v-model="newEndpoint.name" type="text" placeholder="Cek Tagihan"
                     class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"/>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <input v-model="newEndpoint.category" type="text" placeholder="billing"
                     class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"/>
            </div>
          </div>

          <!-- Row 2: Method & URL -->
          <div class="flex gap-4">
            <div class="w-32">
              <label class="block text-sm font-medium text-gray-700 mb-1">Method *</label>
              <select v-model="newEndpoint.method" class="w-full px-3 py-2 border rounded-lg">
                <option>GET</option>
                <option>POST</option>
                <option>PUT</option>
                <option>DELETE</option>
              </select>
            </div>
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">URL *</label>
              <input v-model="newEndpoint.url" type="text"
                     placeholder="https://gateway.pdamkotasmg.co.id/api-gw/pengaduan/api/billing/tagihan/air/{no_pel}"
                     class="w-full px-3 py-2 border rounded-lg font-mono text-sm"/>
              <p class="text-xs text-gray-500 mt-1">Gunakan {param} untuk path parameter dinamis</p>
            </div>
          </div>

          <!-- Keywords -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Trigger Keywords *</label>
            <input v-model="newEndpoint.keywords" type="text"
                   placeholder="tagihan, cek tagihan, bayar, billing"
                   class="w-full px-3 py-2 border rounded-lg"/>
            <p class="text-xs text-gray-500 mt-1">Pisahkan dengan koma. AI akan panggil API ini jika keyword ditemukan di pesan user.</p>
          </div>

          <!-- Parameter Extraction -->
          <div class="border rounded-lg p-4 bg-gray-50">
            <div class="flex justify-between items-center mb-3">
              <div>
                <label class="block text-sm font-medium text-gray-700">Parameter Extraction</label>
                <p class="text-xs text-gray-500">Cara extract parameter dari pesan user</p>
              </div>
              <button @click="addParam" type="button" class="text-blue-600 text-sm hover:underline">+ Add Parameter</button>
            </div>
            <div class="space-y-2">
              <div v-for="(param, idx) in newEndpoint.params" :key="idx" class="flex gap-2 items-center">
                <input v-model="param.name" placeholder="no_pel"
                       class="w-1/4 px-2 py-1.5 border rounded text-sm"/>
                <select v-model="param.type" class="w-1/5 px-2 py-1.5 border rounded text-sm">
                  <option value="path">Path</option>
                  <option value="query">Query</option>
                  <option value="body">Body</option>
                </select>
                <input v-model="param.pattern" placeholder="Regex: \d{6,12}"
                       class="flex-1 px-2 py-1.5 border rounded text-sm font-mono"/>
                <button @click="newEndpoint.params.splice(idx, 1)" type="button" class="text-red-500 px-2 hover:bg-red-50 rounded">✕</button>
              </div>
              <p v-if="newEndpoint.params.length === 0" class="text-xs text-gray-400 italic">
                Belum ada parameter. Default: akan extract angka 6-12 digit sebagai no_pel.
              </p>
            </div>
          </div>

          <!-- Headers -->
          <div class="border rounded-lg p-4 bg-gray-50">
            <div class="flex justify-between items-center mb-3">
              <div>
                <label class="block text-sm font-medium text-gray-700">Headers</label>
                <p class="text-xs text-gray-500">HTTP headers untuk request</p>
              </div>
              <button @click="addHeader" type="button" class="text-blue-600 text-sm hover:underline">+ Add Header</button>
            </div>
            <div class="space-y-2">
              <div v-for="(header, idx) in newEndpoint.headers" :key="idx" class="flex gap-2 items-center">
                <input v-model="header.key" placeholder="Authorization"
                       class="w-1/3 px-2 py-1.5 border rounded text-sm"/>
                <input v-model="header.value" placeholder="Bearer xxx"
                       class="flex-1 px-2 py-1.5 border rounded text-sm font-mono"/>
                <button @click="newEndpoint.headers.splice(idx, 1)" type="button" class="text-red-500 px-2 hover:bg-red-50 rounded">✕</button>
              </div>
              <p v-if="newEndpoint.headers.length === 0" class="text-xs text-gray-400 italic">
                Tidak ada custom headers
              </p>
            </div>
          </div>

          <!-- Request Body Template (for POST/PUT) -->
          <div v-if="['POST', 'PUT'].includes(newEndpoint.method)" class="border rounded-lg p-4 bg-gray-50">
            <label class="block text-sm font-medium text-gray-700 mb-1">Request Body Template (JSON)</label>
            <textarea v-model="newEndpoint.body_template" rows="4"
                      placeholder='{"no_pelanggan": "{no_pel}", "bulan": "{bulan}"}'
                      class="w-full px-3 py-2 border rounded-lg font-mono text-sm"></textarea>
            <p class="text-xs text-gray-500 mt-1">Gunakan {param} untuk value dinamis dari parameter extraction</p>
          </div>

          <!-- Response Template -->
          <div class="border rounded-lg p-4 bg-gray-50">
            <label class="block text-sm font-medium text-gray-700 mb-1">Response Template</label>
            <textarea v-model="newEndpoint.response_template" rows="3"
                      placeholder="📋 Info Tagihan:
- Nama: {nama_pelanggan}
- No. Pelanggan: {no_pel}
- Total Tagihan: Rp {total_tagihan}
- Status: {status}"
                      class="w-full px-3 py-2 border rounded-lg text-sm"></textarea>
            <p class="text-xs text-gray-500 mt-1">Template untuk format response. Gunakan {field} dari JSON response API.</p>
          </div>

          <!-- Active Toggle -->
          <div class="flex items-center gap-2">
            <input type="checkbox" v-model="newEndpoint.is_active" id="api-active" class="rounded"/>
            <label for="api-active" class="text-sm">Active</label>
          </div>
        </div>

        <div class="p-6 border-t flex justify-end gap-3 sticky bottom-0 bg-white">
          <button @click="closeApiModal" class="px-4 py-2 border rounded-lg cursor-pointer hover:bg-gray-50">Cancel</button>
          <button @click="saveApiEndpoint" class="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700">
            {{ editingEndpoint ? 'Update' : 'Add' }} Endpoint
          </button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL: WIDGET TOKEN ==================== -->
    <div v-if="showWidgetModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-lg">
        <h3 class="text-lg font-semibold mb-4">🌐 Create Widget Token</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Token Name</label>
            <input v-model="newWidgetToken.name" type="text" class="w-full border rounded-lg px-3 py-2" placeholder="Website PDAM">
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Allowed Domains</label>
            <input v-model="newWidgetToken.domains" type="text" class="w-full border rounded-lg px-3 py-2" placeholder="*">
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Scope</label>
            <select v-model="newWidgetToken.scope" class="w-full border rounded-lg px-3 py-2">
              <option value="external">External (Public)</option>
              <option value="internal">Internal (Login required)</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showWidgetModal = false" class="px-4 py-2 border rounded-lg cursor-pointer">Cancel</button>
          <button @click="createWidgetToken" class="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer">Create Token</button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL: WHATSAPP TOKEN ==================== -->
    <div v-if="showWhatsAppModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-lg">
        <h3 class="text-lg font-semibold mb-4">📱 Create WhatsApp Token</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Token Name</label>
            <input v-model="newWhatsAppToken.name" type="text" class="w-full border rounded-lg px-3 py-2" placeholder="WhatsApp Bot">
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Webhook URL (optional)</label>
            <input v-model="newWhatsAppToken.webhook_url" type="text" class="w-full border rounded-lg px-3 py-2" placeholder="https://...">
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showWhatsAppModal = false" class="px-4 py-2 border rounded-lg cursor-pointer">Cancel</button>
          <button @click="createWhatsAppToken" class="px-4 py-2 bg-green-600 text-white rounded-lg cursor-pointer">Create Token</button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL: FREE OPTIONS ==================== -->
    <div v-if="showFreeOptionsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">🆓 Free API Options</h3>
        <div class="space-y-4">
          <div v-for="opt in freeOptions" :key="opt.name" class="border rounded-lg p-4">
            <div class="flex justify-between">
              <div>
                <h4 class="font-medium">{{ opt.name }} {{ opt.recommended ? '⭐' : '' }}</h4>
                <p class="text-sm text-gray-600">{{ opt.description }}</p>
                <p class="text-sm text-green-600">Free: {{ opt.free_tier }}</p>
              </div>
              <a :href="opt.url" target="_blank" class="text-blue-600 hover:underline text-sm">Get Key →</a>
            </div>
          </div>
        </div>
        <div class="flex justify-end mt-6">
          <button @click="showFreeOptionsModal = false" class="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer">Close</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="alertMessage" class="fixed bottom-4 right-4 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg z-50">
      {{ alertMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'

// =============================================
// FIX: Disable default layout (no double header)
// =============================================
definePageMeta({
  layout: false
})

// ============ STATE ============
const activeTab = ref('ai-providers')
const alertMessage = ref('')

// Modals
const showAddProviderModal = ref(false)
const showAddApiModal = ref(false)
const showWidgetModal = ref(false)
const showWhatsAppModal = ref(false)
const showFreeOptionsModal = ref(false)

// Data
const aiProviders = ref([])
const apiEndpoints = ref([])
const embedTokens = ref([])
const tokenStats = ref({})

// Ollama models from installed
const ollamaInstalledModels = ref([])
const ollamaModelsLoading = ref(false)

// Edit state
const editingEndpoint = ref(null)

// ============ TABS ============
const tabs = computed(() => [
  { id: 'ai-providers', name: 'AI Providers', icon: '🤖', count: aiProviders.value.length },
  { id: 'api-integrations', name: 'API Integrations', icon: '🔗', count: apiEndpoints.value.length },
  { id: 'embed-tokens', name: 'Embed Tokens', icon: '🔑', count: embedTokens.value.length }
])

// ============ FORMS ============
const newProvider = ref({ name: '', provider_type: 'groq', api_key: '', default_model: 'llama-3.3-70b-versatile', is_active: true, is_default: false })

const newEndpoint = ref({
  name: '',
  method: 'GET',
  url: '',
  category: 'general',
  keywords: '',
  params: [],
  headers: [],
  body_template: '',
  response_template: '',
  is_active: true
})

const newWidgetToken = ref({ name: '', domains: '*', scope: 'external' })
const newWhatsAppToken = ref({ name: '', webhook_url: '' })

// ============ STATIC DATA ============
const apiTemplates = ref([
  {
    name: 'Cek Tagihan',
    method: 'GET',
    url: 'https://gateway.pdamkotasmg.co.id/api-gw/pengaduan/api/billing/tagihan/air/{no_pel}',
    category: 'billing',
    keywords: 'tagihan, cek tagihan, bayar, billing, tunggakan',
    params: [{ name: 'no_pel', type: 'path', pattern: '\\d{6,12}' }],
    response_template: '📋 Info Tagihan:\n- No. Pelanggan: {no_pel}\n- Nama: {nama}\n- Alamat: {alamat}\n- Total Tagihan: Rp {total_tagihan}'
  },
  {
    name: 'Info Pelanggan',
    method: 'GET',
    url: 'https://gateway.pdamkotasmg.co.id/api-gw/pengaduan/api/pelanggan/{no_pel}',
    category: 'customer',
    keywords: 'info pelanggan, data pelanggan, profil',
    params: [{ name: 'no_pel', type: 'path', pattern: '\\d{6,12}' }],
    response_template: '👤 Info Pelanggan:\n- No. Pelanggan: {no_pel}\n- Nama: {nama}\n- Alamat: {alamat}\n- Status: {status}'
  },
])

const freeOptions = ref([
  { name: 'Groq', url: 'https://console.groq.com/keys', description: 'Tercepat!', free_tier: '14,400 req/day', recommended: true },
  { name: 'Google Gemini', url: 'https://aistudio.google.com/app/apikey', description: 'Bagus untuk Indonesia', free_tier: '15 req/min', recommended: true },
  { name: 'OpenRouter', url: 'https://openrouter.ai/keys', description: 'Multi model', free_tier: 'Varies', recommended: false },
  { name: 'Ollama', url: '#', description: 'Local, unlimited', free_tier: 'Unlimited', recommended: true },
])

// Static models for non-Ollama providers
const staticModelsByProvider = {
  groq: [{ id: 'llama-3.3-70b-versatile', display_name: 'Llama 3.3 70B' }, { id: 'mixtral-8x7b-32768', display_name: 'Mixtral 8x7B' }],
  gemini: [{ id: 'gemini-1.5-flash', display_name: 'Gemini 1.5 Flash' }
    , { id: 'gemini-1.5-pro', display_name: 'Gemini 1.5 Pro' }
    , { id: 'gemini-2.5-flash', display_name: 'gemini-2.5-flash' }
    , { id: 'gemini-2.0-flash', display_name: 'gemini-2.0-flash' }
  ],
  openai: [{ id: 'gpt-4o-mini', display_name: 'GPT-4o Mini' }],
  deepseek: [{ id: 'deepseek-chat', display_name: 'DeepSeek Chat' }],
  claude: [{ id: 'claude-3-haiku-20240307', display_name: 'Claude 3 Haiku' }],
  openrouter: [{ id: 'google/gemini-flash-1.5', display_name: 'Gemini Flash' }]
}

// ============ COMPUTED: Models for current provider ============
const currentProviderModels = computed(() => {
  if (newProvider.value.provider_type === 'ollama') {
    // Use installed Ollama models
    if (ollamaInstalledModels.value.length > 0) {
      return ollamaInstalledModels.value.map(m => ({
        id: m.name,
        display_name: m.name
      }))
    }
    // Fallback
    return [{ id: 'llama3.2:3b', display_name: 'Llama 3.2 3B (default)' }]
  }
  return staticModelsByProvider[newProvider.value.provider_type] || []
})

// ============ CONFIG ============
const config = useRuntimeConfig()
const apiUrl = config.public?.apiUrl || 'http://localhost:8000'

// ============ HELPERS ============
const showAlert = (msg) => { alertMessage.value = msg; setTimeout(() => alertMessage.value = '', 3000) }
const getMethodColor = (m) => ({ GET: 'bg-green-100 text-green-700', POST: 'bg-blue-100 text-blue-700', PUT: 'bg-yellow-100 text-yellow-700', DELETE: 'bg-red-100 text-red-700' }[m] || 'bg-gray-100')

// ============ AUTH ============
const getAuthHeaders = () => {
  const token = localStorage.getItem('pdam_access_token')
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

// ============ FETCH OLLAMA MODELS ============
const fetchOllamaModels = async () => {
  ollamaModelsLoading.value = true
  try {
    const res = await fetch(`${apiUrl}/api/training/models`)
    if (res.ok) {
      const data = await res.json()
      ollamaInstalledModels.value = data.models || []
      console.log('Ollama models loaded:', ollamaInstalledModels.value.length)
    }
  } catch (e) {
    console.error('Failed to fetch Ollama models:', e)
  } finally {
    ollamaModelsLoading.value = false
  }
}

// ============ MODAL OPENERS ============
const openAddProviderModal = async () => {
  newProvider.value = { name: '', provider_type: 'groq', api_key: '', default_model: 'llama-3.3-70b-versatile', is_active: true, is_default: false }
  showAddProviderModal.value = true
}

const onProviderTypeChange = async () => {
  // When user selects Ollama, fetch installed models
  if (newProvider.value.provider_type === 'ollama') {
    await fetchOllamaModels()
    // Set default to first installed model
    if (ollamaInstalledModels.value.length > 0) {
      newProvider.value.default_model = ollamaInstalledModels.value[0].name
    }
  } else {
    // Set default model for other providers
    const models = staticModelsByProvider[newProvider.value.provider_type] || []
    if (models.length > 0) {
      newProvider.value.default_model = models[0].id
    }
  }
}

const openAddApiModal = () => {
  editingEndpoint.value = null
  newEndpoint.value = {
    name: '',
    method: 'GET',
    url: '',
    category: 'general',
    keywords: '',
    params: [],
    headers: [],
    body_template: '',
    response_template: '',
    is_active: true
  }
  showAddApiModal.value = true
}

const closeApiModal = () => {
  showAddApiModal.value = false
  editingEndpoint.value = null
}

const addParam = () => { newEndpoint.value.params.push({ name: '', type: 'path', pattern: '' }) }
const addHeader = () => { newEndpoint.value.headers.push({ key: '', value: '' }) }

// ============ FETCH DATA ============
const fetchProviders = async () => {
  try {
    const res = await fetch(`${apiUrl}/api/ai-providers/`, { headers: getAuthHeaders() })
    if (res.ok) aiProviders.value = await res.json()
  } catch (e) { console.error(e) }
}

const fetchEndpoints = async () => {
  try {
    const res = await fetch(`${apiUrl}/api/integrations/`, { headers: getAuthHeaders() })
    if (res.ok) apiEndpoints.value = await res.json()
  } catch (e) { console.error(e) }
}

const fetchTokens = async () => {
  try {
    const res = await fetch(`${apiUrl}/api/embed-tokens/`, { headers: getAuthHeaders() })
    if (res.ok) embedTokens.value = await res.json()
    const statsRes = await fetch(`${apiUrl}/api/embed-tokens/stats/overview`, { headers: getAuthHeaders() })
    if (statsRes.ok) tokenStats.value = await statsRes.json()
  } catch (e) { console.error(e) }
}

// ============ PROVIDER ACTIONS ============
const createProvider = async () => {
  try {
    const res = await fetch(`${apiUrl}/api/ai-providers/`, { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(newProvider.value) })
    if (res.ok) { showAddProviderModal.value = false; await fetchProviders(); showAlert('✅ Provider added!') }
    else { const e = await res.json(); showAlert('❌ ' + (e.detail || 'Error')) }
  } catch (e) { showAlert('❌ ' + e.message) }
}

const testProvider = async (id) => {
  showAlert('⏳ Testing...')
  try {
    const res = await fetch(`${apiUrl}/api/ai-providers/${id}/test`, { method: 'POST', headers: getAuthHeaders() })
    const r = await res.json()
    showAlert(r.success ? '✅ OK!' : '❌ ' + r.error)
  } catch (e) { showAlert('❌ ' + e.message) }
}

const toggleProvider = async (id) => { await fetch(`${apiUrl}/api/ai-providers/${id}/toggle`, { method: 'POST', headers: getAuthHeaders() }); await fetchProviders() }
const setDefaultProvider = async (id) => { await fetch(`${apiUrl}/api/ai-providers/${id}/set-default`, { method: 'POST', headers: getAuthHeaders() }); await fetchProviders(); showAlert('⭐ Default set') }
const deleteProvider = async (id) => { if (!confirm('Delete?')) return; await fetch(`${apiUrl}/api/ai-providers/${id}`, { method: 'DELETE', headers: getAuthHeaders() }); await fetchProviders() }

// ============ API ENDPOINT ACTIONS ============
const applyTemplate = (template) => {
  editingEndpoint.value = null
  newEndpoint.value = {
    name: template.name,
    method: template.method,
    url: template.url,
    category: template.category,
    keywords: template.keywords,
    params: template.params ? [...template.params] : [],
    headers: template.headers ? [...template.headers] : [],
    body_template: template.body_template || '',
    response_template: template.response_template || '',
    is_active: true
  }
  showAddApiModal.value = true
}

const editApiEndpoint = (endpoint) => {
  editingEndpoint.value = endpoint
  newEndpoint.value = {
    name: endpoint.name || '',
    method: endpoint.method || 'GET',
    url: endpoint.url || '',
    category: endpoint.category || 'general',
    keywords: Array.isArray(endpoint.trigger_keywords) ? endpoint.trigger_keywords.join(', ') : (endpoint.keywords || ''),
    params: endpoint.params ? [...endpoint.params] : [],
    headers: endpoint.headers ? Object.entries(endpoint.headers).map(([key, value]) => ({ key, value })) : [],
    body_template: endpoint.body_template || '',
    response_template: endpoint.response_template || '',
    is_active: endpoint.is_active !== false
  }
  showAddApiModal.value = true
}

const saveApiEndpoint = async () => {
  // Validate
  if (!newEndpoint.value.name || !newEndpoint.value.url) {
    showAlert('❌ Name dan URL wajib diisi')
    return
  }

  // Build payload
  const headersObj = {}
  newEndpoint.value.headers.forEach(h => {
    if (h.key) headersObj[h.key] = h.value
  })

  const payload = {
    name: newEndpoint.value.name,
    method: newEndpoint.value.method,
    url: newEndpoint.value.url,
    category: newEndpoint.value.category,
    trigger_keywords: newEndpoint.value.keywords.split(',').map(k => k.trim()).filter(Boolean),
    params: newEndpoint.value.params.filter(p => p.name),
    headers: headersObj,
    body_template: newEndpoint.value.body_template,
    response_template: newEndpoint.value.response_template,
    is_active: newEndpoint.value.is_active
  }

  try {
    let res
    if (editingEndpoint.value) {
      // Update existing
      res = await fetch(`${apiUrl}/api/integrations/${editingEndpoint.value.id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      })
    } else {
      // Create new
      res = await fetch(`${apiUrl}/api/integrations/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      })
    }

    if (res.ok) {
      closeApiModal()
      await fetchEndpoints()
      showAlert(editingEndpoint.value ? '✅ Endpoint updated!' : '✅ Endpoint added!')
    } else {
      const e = await res.json()
      showAlert('❌ ' + (e.detail || 'Error'))
    }
  } catch (e) {
    showAlert('❌ ' + e.message)
  }
}

const testApiEndpoint = async (id) => {
  showAlert('⏳ Testing...')
  try {
    const res = await fetch(`${apiUrl}/api/integrations/${id}/test`, { method: 'POST', headers: getAuthHeaders() })
    const r = await res.json()
    showAlert(r.success ? '✅ OK!' : '❌ Error')
  } catch (e) { showAlert('❌ ' + e.message) }
}

const toggleApiEndpoint = async (id) => {
  await fetch(`${apiUrl}/api/integrations/${id}/toggle`, { method: 'POST', headers: getAuthHeaders() })
  await fetchEndpoints()
}

const deleteApiEndpoint = async (id) => {
  if (!confirm('Delete endpoint ini?')) return
  await fetch(`${apiUrl}/api/integrations/${id}`, { method: 'DELETE', headers: getAuthHeaders() })
  await fetchEndpoints()
}

// ============ TOKEN ACTIONS ============
const createWidgetToken = async () => {
  try {
    const res = await fetch(`${apiUrl}/api/embed-tokens/quick-create/widget?name=${encodeURIComponent(newWidgetToken.value.name)}`, { method: 'POST', headers: getAuthHeaders() })
    if (res.ok) { showWidgetModal.value = false; await fetchTokens(); showAlert('✅ Token created!') }
  } catch (e) { showAlert('❌ ' + e.message) }
}

const createWhatsAppToken = async () => {
  try {
    const res = await fetch(`${apiUrl}/api/embed-tokens/quick-create/whatsapp?name=${encodeURIComponent(newWhatsAppToken.value.name)}`, { method: 'POST', headers: getAuthHeaders() })
    if (res.ok) { showWhatsAppModal.value = false; await fetchTokens(); showAlert('✅ Token created!') }
  } catch (e) { showAlert('❌ ' + e.message) }
}

const copyTokenCode = async (token) => {
  try {
    const res = await fetch(`${apiUrl}/api/embed-tokens/${token.id}/widget-code`, { headers: getAuthHeaders() })
    const r = await res.json()
    await navigator.clipboard.writeText(r.html_code)
    showAlert('📋 Copied!')
  } catch (e) { showAlert('❌ ' + e.message) }
}

const deleteToken = async (id) => { if (!confirm('Delete?')) return; await fetch(`${apiUrl}/api/embed-tokens/${id}`, { method: 'DELETE', headers: getAuthHeaders() }); await fetchTokens() }

// ============ ON MOUNT ============
onMounted(async () => {
  const token = localStorage.getItem('pdam_access_token')
  if (!token) {
    showAlert('❌ Please login first')
    navigateTo('/login')
    return
  }

  await Promise.all([fetchProviders(), fetchEndpoints(), fetchTokens()])
})
</script>