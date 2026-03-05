/**
 * PDAM Chatbot AI - Embeddable Widget
 * 
 * Cara penggunaan:
 * 1. Tambahkan script ini di website Anda
 * 2. Widget akan muncul di pojok kanan bawah
 * 
 * <script src="https://chatbot.pdamkotasmg.co.id/widget.js"></script>
 * <script>
 *   PDAChatbot.init({
 *     apiUrl: 'https://chatbot.pdamkotasmg.co.id/api'
 *   });
 * </script>
 */

(function() {
  'use strict';

  // Default configuration
  const defaultConfig = {
    apiUrl: 'http://localhost:8000',
    position: 'bottom-right',
    primaryColor: '#0066CC',
    title: 'PDAM Chatbot',
    subtitle: 'Tirta Moedal Semarang',
    placeholder: 'Ketik pertanyaan Anda...',
    welcomeMessage: 'Halo! 👋 Saya asisten PDAM Kota Semarang. Ada yang bisa saya bantu?',
    autoOpen: false,
    zIndex: 9999
  };

  let config = { ...defaultConfig };
  let isOpen = false;
  let messages = [];
  let isLoading = false;

  // Styles
  const styles = `
    #pdam-chatbot-widget {
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
      position: fixed;
      z-index: ${config.zIndex};
    }
    
    #pdam-chatbot-widget.bottom-right {
      bottom: 20px;
      right: 20px;
    }
    
    #pdam-chatbot-widget.bottom-left {
      bottom: 20px;
      left: 20px;
    }
    
    #pdam-chat-button {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, ${config.primaryColor} 0%, #0052A3 100%);
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 20px rgba(0, 102, 204, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
    }
    
    #pdam-chat-button:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 25px rgba(0, 102, 204, 0.5);
    }
    
    #pdam-chat-button svg {
      width: 28px;
      height: 28px;
      fill: white;
    }
    
    #pdam-chat-window {
      display: none;
      position: absolute;
      bottom: 80px;
      right: 0;
      width: 380px;
      height: 550px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
      overflow: hidden;
      flex-direction: column;
    }
    
    #pdam-chat-window.open {
      display: flex;
      animation: slideUp 0.3s ease;
    }
    
    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    #pdam-chat-header {
      background: linear-gradient(135deg, ${config.primaryColor} 0%, #0052A3 100%);
      color: white;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    #pdam-chat-header-icon {
      width: 40px;
      height: 40px;
      background: rgba(255,255,255,0.2);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    #pdam-chat-header-icon svg {
      width: 24px;
      height: 24px;
      fill: white;
    }
    
    #pdam-chat-header-text h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
    
    #pdam-chat-header-text p {
      margin: 2px 0 0;
      font-size: 12px;
      opacity: 0.8;
    }
    
    #pdam-chat-close {
      margin-left: auto;
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      padding: 8px;
      border-radius: 8px;
      transition: background 0.2s;
    }
    
    #pdam-chat-close:hover {
      background: rgba(255,255,255,0.2);
    }
    
    #pdam-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .pdam-message {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
    }
    
    .pdam-message.user {
      background: linear-gradient(135deg, ${config.primaryColor} 0%, #0052A3 100%);
      color: white;
      margin-left: auto;
      border-bottom-right-radius: 4px;
    }
    
    .pdam-message.assistant {
      background: #f1f5f9;
      color: #1e293b;
      margin-right: auto;
      border-bottom-left-radius: 4px;
    }
    
    .pdam-message.assistant a {
      color: ${config.primaryColor};
    }
    
    .pdam-typing {
      display: flex;
      gap: 4px;
      padding: 16px;
      background: #f1f5f9;
      border-radius: 16px;
      width: fit-content;
    }
    
    .pdam-typing span {
      width: 8px;
      height: 8px;
      background: ${config.primaryColor};
      border-radius: 50%;
      animation: typingBounce 1.4s ease-in-out infinite;
    }
    
    .pdam-typing span:nth-child(2) { animation-delay: 0.2s; }
    .pdam-typing span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typingBounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-4px); }
    }
    
    #pdam-chat-input-container {
      padding: 12px 16px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      gap: 8px;
      align-items: flex-end;
    }
    
    #pdam-chat-input {
      flex: 1;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 14px;
      resize: none;
      max-height: 100px;
      outline: none;
      transition: border-color 0.2s;
    }
    
    #pdam-chat-input:focus {
      border-color: ${config.primaryColor};
    }
    
    #pdam-chat-send {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, ${config.primaryColor} 0%, #0052A3 100%);
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.2s;
    }
    
    #pdam-chat-send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    #pdam-chat-send svg {
      width: 20px;
      height: 20px;
      fill: white;
    }
    
    #pdam-chat-footer {
      padding: 8px 16px;
      text-align: center;
      font-size: 11px;
      color: #94a3b8;
    }
    
    #pdam-chat-footer a {
      color: ${config.primaryColor};
      text-decoration: none;
    }
    
    @media (max-width: 480px) {
      #pdam-chat-window {
        width: calc(100vw - 32px);
        height: calc(100vh - 100px);
        bottom: 70px;
        right: -10px;
      }
    }
  `;

  // Icons
  const icons = {
    chat: '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>',
    close: '<svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    send: '<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>',
    bot: '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>'
  };

  // Create widget HTML
  function createWidget() {
    // Add styles
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);

    // Create widget container
    const widget = document.createElement('div');
    widget.id = 'pdam-chatbot-widget';
    widget.className = config.position;

    widget.innerHTML = `
      <div id="pdam-chat-window">
        <div id="pdam-chat-header">
          <div id="pdam-chat-header-icon">${icons.bot}</div>
          <div id="pdam-chat-header-text">
            <h3>${config.title}</h3>
            <p>${config.subtitle}</p>
          </div>
          <button id="pdam-chat-close">${icons.close}</button>
        </div>
        <div id="pdam-chat-messages"></div>
        <div id="pdam-chat-input-container">
          <textarea id="pdam-chat-input" placeholder="${config.placeholder}" rows="1"></textarea>
          <button id="pdam-chat-send">${icons.send}</button>
        </div>
        <div id="pdam-chat-footer">
          Powered by <a href="https://pdamkotasmg.co.id" target="_blank">PDAM Semarang</a>
        </div>
      </div>
      <button id="pdam-chat-button">${icons.chat}</button>
    `;

    document.body.appendChild(widget);

    // Bind events
    document.getElementById('pdam-chat-button').addEventListener('click', toggleChat);
    document.getElementById('pdam-chat-close').addEventListener('click', toggleChat);
    document.getElementById('pdam-chat-send').addEventListener('click', sendMessage);
    document.getElementById('pdam-chat-input').addEventListener('keydown', handleKeydown);
    document.getElementById('pdam-chat-input').addEventListener('input', autoResize);

    // Add welcome message
    if (config.welcomeMessage) {
      addMessage('assistant', config.welcomeMessage);
    }

    // Auto open
    if (config.autoOpen) {
      setTimeout(() => toggleChat(), 1000);
    }
  }

  // Toggle chat window
  function toggleChat() {
    isOpen = !isOpen;
    const chatWindow = document.getElementById('pdam-chat-window');
    chatWindow.classList.toggle('open', isOpen);
    
    if (isOpen) {
      document.getElementById('pdam-chat-input').focus();
    }
  }

  // Add message to chat
  function addMessage(role, content) {
    const messagesContainer = document.getElementById('pdam-chat-messages');
    const messageEl = document.createElement('div');
    messageEl.className = `pdam-message ${role}`;
    messageEl.innerHTML = content;
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    messages.push({ role, content });
  }

  // Show typing indicator
  function showTyping() {
    const messagesContainer = document.getElementById('pdam-chat-messages');
    const typingEl = document.createElement('div');
    typingEl.className = 'pdam-typing';
    typingEl.id = 'pdam-typing-indicator';
    typingEl.innerHTML = '<span></span><span></span><span></span>';
    messagesContainer.appendChild(typingEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Hide typing indicator
  function hideTyping() {
    const typingEl = document.getElementById('pdam-typing-indicator');
    if (typingEl) {
      typingEl.remove();
    }
  }

  // Send message
  async function sendMessage() {
    const input = document.getElementById('pdam-chat-input');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    input.value = '';
    input.style.height = 'auto';
    addMessage('user', escapeHtml(message));
    
    isLoading = true;
    document.getElementById('pdam-chat-send').disabled = true;
    showTyping();

    try {
      const response = await fetch(`${config.apiUrl}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          chat_history: messages.slice(-10)
        })
      });

      const data = await response.json();
      hideTyping();
      
      // Simple markdown-like parsing
      let answer = data.answer || 'Maaf, tidak bisa memproses pesan.';
      answer = answer
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
      
      addMessage('assistant', answer);
    } catch (error) {
      hideTyping();
      addMessage('assistant', '❌ Maaf, terjadi kesalahan. Silakan coba lagi atau hubungi call center (024) 8311113.');
    } finally {
      isLoading = false;
      document.getElementById('pdam-chat-send').disabled = false;
    }
  }

  // Handle keyboard input
  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // Auto resize textarea
  function autoResize() {
    const input = document.getElementById('pdam-chat-input');
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 100) + 'px';
  }

  // Escape HTML
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Public API
  window.PDAChatbot = {
    init: function(userConfig) {
      config = { ...defaultConfig, ...userConfig };
      
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
      } else {
        createWidget();
      }
    },
    open: function() {
      if (!isOpen) toggleChat();
    },
    close: function() {
      if (isOpen) toggleChat();
    },
    sendMessage: function(message) {
      document.getElementById('pdam-chat-input').value = message;
      sendMessage();
    }
  };

  // Auto-init if data attributes present
  const script = document.currentScript;
  if (script && script.dataset.apiUrl) {
    window.PDAChatbot.init({
      apiUrl: script.dataset.apiUrl
    });
  }
})();
