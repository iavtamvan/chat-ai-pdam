<script setup lang="ts">
import { useChat } from '~/composables/useChat'
import { useAuthStore } from '~/composables/useAuth'

definePageMeta({
  title: 'Chat'
})

const authStore = useAuthStore()
const { 
  messages, 
  isLoading, 
  suggestions,
  sendMessage, 
  clearChat 
} = useChat()

const inputMessage = ref('')
const chatContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

// Auto-scroll to bottom
watch(messages, () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}, { deep: true })

// Handle send message
const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return
  
  inputMessage.value = ''
  await sendMessage(message)
  
  // Focus back to input
  inputRef.value?.focus()
}

// Handle suggestion click
const handleSuggestion = (suggestion: string) => {
  inputMessage.value = suggestion
  handleSend()
}

// Handle enter key
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// Auto-resize textarea
const autoResize = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 150) + 'px'
}

// Initial suggestions
const defaultSuggestions = [
  'Bagaimana cara cek tagihan air?',
  'Apa syarat pemasangan baru?',
  'Cara lapor kebocoran pipa',
  'Dimana loket pembayaran terdekat?'
]
</script>

<template>
  <div class="h-[calc(100vh-64px)] flex flex-col max-w-4xl mx-auto px-4">
    <!-- Chat Container -->
    <div 
      ref="chatContainer"
      class="flex-1 overflow-y-auto py-6 space-y-4 chat-container"
    >
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="text-center py-12">
        <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shadow-xl shadow-primary-500/30">
          <Icon name="heroicons:sparkles" class="w-10 h-10 text-white" />
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">
          Selamat Datang di PDAM Chatbot AI
        </h2>
        <p class="text-gray-600 mb-8 max-w-md mx-auto">
          Saya siap membantu menjawab pertanyaan seputar layanan PDAM Tirta Moedal Kota Semarang
        </p>
        
        <!-- Quick Suggestions -->
        <div class="flex flex-wrap justify-center gap-2">
          <button 
            v-for="suggestion in defaultSuggestions" 
            :key="suggestion"
            @click="handleSuggestion(suggestion)"
            class="suggestion-chip"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>

      <!-- Messages -->
      <template v-for="(message, index) in messages" :key="index">
        <div 
          :class="[
            'chat-message px-4 py-3',
            message.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'
          ]"
        >
          <!-- Message Content -->
          <div class="markdown-content" v-html="message.content" />
          
          <!-- Sources (for assistant messages) -->
          <div
              v-if="message.role === 'assistant' && message.sources?.length"
              class="mt-3 pt-3 border-t border-gray-100"
          >
            <p class="text-xs text-gray-500 mb-2">📚 Sumber Dokumen:</p>
            <div class="flex flex-wrap gap-2">
              <span
                  v-for="(source, idx) in message.sources"
                  :key="idx"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium border border-blue-200 shadow-sm max-w-full"
              >
                <Icon name="heroicons:document-text" class="w-4 h-4 flex-shrink-0" />
                <span class="whitespace-normal break-words text-left">{{ source.filename }}</span>
              </span>
            </div>
          </div>
        </div>
      </template>

      <!-- Typing Indicator -->
      <div v-if="isLoading" class="chat-message chat-message-assistant">
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <!-- Suggestions after response -->
      <div 
        v-if="suggestions.length && !isLoading && messages.length > 0" 
        class="flex flex-wrap gap-2 mt-4"
      >
        <button 
          v-for="suggestion in suggestions" 
          :key="suggestion"
          @click="handleSuggestion(suggestion)"
          class="suggestion-chip text-xs"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <!-- Input Area -->
    <div class="sticky bottom-0 py-4 bg-gradient-to-t from-slate-50 via-slate-50">
      <div class="relative flex items-end gap-3 bg-white rounded-2xl shadow-lg border border-gray-100 p-2">
        <!-- Clear Chat Button -->
        <button 
          v-if="messages.length > 0"
          @click="clearChat"
          class="flex-shrink-0 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
          title="Hapus Chat"
        >
          <Icon name="heroicons:trash" class="w-5 h-5" />
        </button>

        <!-- Text Input -->
        <textarea
          ref="inputRef"
          v-model="inputMessage"
          @keydown="handleKeydown"
          @input="autoResize"
          placeholder="Ketik pertanyaan Anda..."
          rows="1"
          class="flex-1 resize-none border-0 focus:ring-0 text-gray-900 placeholder-gray-400 bg-transparent py-2 px-2 max-h-32"
          :disabled="isLoading"
        />

        <!-- Send Button -->
        <button
          @click="handleSend"
          :disabled="!inputMessage.trim() || isLoading"
          class="flex-shrink-0 p-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:from-primary-600 hover:to-primary-700 transition-all shadow-lg shadow-primary-500/30"
        >
          <Icon 
            :name="isLoading ? 'heroicons:arrow-path' : 'heroicons:paper-airplane'" 
            :class="['w-5 h-5', isLoading && 'animate-spin']" 
          />
        </button>
      </div>

      <!-- Disclaimer -->
      <p class="text-xs text-gray-400 text-center mt-3">
        AI dapat membuat kesalahan. Verifikasi informasi penting dengan menghubungi call center.
      </p>
    </div>
  </div>
</template>
