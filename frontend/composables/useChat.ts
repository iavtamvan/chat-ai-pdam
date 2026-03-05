/**
 * Chat Composable
 * Handles chat state and API communication
 */

import { ref, reactive } from 'vue'
import { marked } from 'marked'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Array<{
    filename: string
    similarity: number
  }>
}

export interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  suggestions: string[]
  sessionId: string | null
}

// Shared state across components
const chatState = reactive<ChatState>({
  messages: [],
  isLoading: false,
  error: null,
  suggestions: [],
  sessionId: null
})

export function useChat() {
  const config = useRuntimeConfig()
  const apiUrl = config.public.apiUrl

  // Send message to chatbot
  const sendMessage = async (message: string, useRag = true) => {
    if (!message.trim()) return

    // Add user message
    chatState.messages.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    })

    chatState.isLoading = true
    chatState.error = null
    chatState.suggestions = []

    try {
      // Get auth token if available
      const token = localStorage.getItem('pdam_access_token')
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // Prepare chat history (last 10 messages)
      const chatHistory = chatState.messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp
      }))

      const response = await fetch(`${apiUrl}/api/chat/send`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          chat_history: chatHistory.slice(0, -1), // Exclude current message
          use_rag: useRag,
          session_id: chatState.sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Parse markdown content
      const htmlContent = marked.parse(data.answer || 'Maaf, tidak bisa memproses pesan.')

      // Add assistant message
      chatState.messages.push({
        role: 'assistant',
        content: htmlContent as string,
        timestamp: data.timestamp || new Date().toISOString(),
        sources: data.sources || []
      })

      // Update suggestions
      if (data.suggestions) {
        chatState.suggestions = data.suggestions
      }

    } catch (error: any) {
      console.error('Chat error:', error)
      chatState.error = error.message

      // Add error message
      chatState.messages.push({
        role: 'assistant',
        content: `❌ Maaf, terjadi kesalahan: ${error.message}. Silakan coba lagi atau hubungi call center (024) 8311113.`,
        timestamp: new Date().toISOString()
      })
    } finally {
      chatState.isLoading = false
    }
  }

  // Stream message (SSE)
  const sendMessageStream = async (message: string, useRag = true) => {
    if (!message.trim()) return

    chatState.messages.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    })

    chatState.isLoading = true

    try {
      const token = localStorage.getItem('pdam_access_token')
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          chat_history: chatState.messages.slice(0, -1),
          use_rag: useRag
        })
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      // Add placeholder for assistant message
      const assistantIndex = chatState.messages.length
      chatState.messages.push({
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      })

      const decoder = new TextDecoder()
      let fullContent = ''
      let sources: any[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'sources') {
                sources = data.data
              } else if (data.type === 'chunk') {
                fullContent += data.data
                chatState.messages[assistantIndex].content = marked.parse(fullContent) as string
              } else if (data.type === 'done') {
                chatState.messages[assistantIndex].sources = sources
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (error: any) {
      chatState.error = error.message
    } finally {
      chatState.isLoading = false
    }
  }

  // Clear chat
  const clearChat = () => {
    chatState.messages = []
    chatState.suggestions = []
    chatState.error = null
    chatState.sessionId = null
  }

  // Get suggestions
  const getSuggestions = async (context?: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/chat/suggestions?context=${encodeURIComponent(context || '')}`)
      const data = await response.json()
      chatState.suggestions = data.suggestions || []
    } catch (error) {
      console.error('Error getting suggestions:', error)
    }
  }

  return {
    messages: computed(() => chatState.messages),
    isLoading: computed(() => chatState.isLoading),
    error: computed(() => chatState.error),
    suggestions: computed(() => chatState.suggestions),
    sendMessage,
    sendMessageStream,
    clearChat,
    getSuggestions
  }
}
