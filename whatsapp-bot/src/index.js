/**
 * PDAM Chatbot AI - WhatsApp Bot
 * Menggunakan Baileys (FREE, no API cost)
 * 
 * Cara penggunaan:
 * 1. npm install
 * 2. npm start
 * 3. Scan QR code dengan WhatsApp
 */

import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore
} from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

dotenv.config();

// Configuration
const config = {
  apiUrl: process.env.API_URL || 'http://localhost:8000',
  sessionDir: process.env.SESSION_DIR || './sessions',
  botName: 'PDAM Chatbot Semarang',
  welcomeMessage: `Halo! 👋 Saya *PDAM Chatbot AI* Tirta Moedal Kota Semarang.

Saya siap membantu Anda dengan:
• ℹ️ Informasi tagihan air
• 🆕 Pemasangan baru
• 📝 Pengaduan & laporan
• 📍 Lokasi loket pembayaran
• ❓ FAQ layanan PDAM

Silakan ketik pertanyaan Anda!`,
  helpMessage: `*Bantuan PDAM Chatbot* 🤖

Perintah yang tersedia:
• /start - Mulai percakapan
• /help - Tampilkan bantuan ini
• /reset - Reset percakapan
• /info - Informasi kontak PDAM

Atau langsung ketik pertanyaan Anda tentang layanan PDAM.

📞 Call Center: (024) 8311113
🌐 Website: pdamkotasmg.co.id`,
  infoMessage: `*PDAM Tirta Moedal Kota Semarang* 💧

📍 Alamat: Jl. Kelud Raya No.60, Semarang
📞 Call Center: (024) 8311113
📱 WhatsApp: (nomor ini)
🌐 Website: pdamkotasmg.co.id
📧 Email: info@pdamkotasmg.co.id

🕐 Jam Operasional:
Senin - Jumat: 07.30 - 16.00 WIB
Sabtu: 07.30 - 12.00 WIB`
};

// Chat history per user (in-memory, use Redis for production)
const chatHistory = new Map();

// Logger
const logger = pino({ level: 'silent' });

// Create session directory
if (!fs.existsSync(config.sessionDir)) {
  fs.mkdirSync(config.sessionDir, { recursive: true });
}

/**
 * Send message to PDAM Chatbot API
 */
async function sendToAPI(message, userId) {
  try {
    // Get user's chat history
    const history = chatHistory.get(userId) || [];
    
    const response = await axios.post(`${config.apiUrl}/api/chat/send`, {
      message: message,
      chat_history: history.slice(-10), // Last 10 messages
      use_rag: true
    }, {
      timeout: 60000, // 60 second timeout
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const answer = response.data.answer || 'Maaf, tidak bisa memproses pesan.';
    
    // Update history
    history.push({ role: 'user', content: message });
    history.push({ role: 'assistant', content: answer });
    chatHistory.set(userId, history);

    return answer;
  } catch (error) {
    console.error('API Error:', error.message);
    return '❌ Maaf, terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi nanti atau hubungi call center (024) 8311113.';
  }
}

/**
 * Format WhatsApp message (convert markdown to WhatsApp format)
 */
function formatMessage(text) {
  return text
    // Bold: **text** or __text__ -> *text*
    .replace(/\*\*(.*?)\*\*/g, '*$1*')
    .replace(/__(.*?)__/g, '*$1*')
    // Italic: *text* (single) -> _text_
    .replace(/(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)/g, '_$1_')
    // Remove HTML tags
    .replace(/<[^>]*>/g, '')
    // Fix multiple newlines
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/**
 * Handle incoming messages
 */
async function handleMessage(sock, message) {
  try {
    const remoteJid = message.key.remoteJid;
    const isGroup = remoteJid.endsWith('@g.us');
    const userId = remoteJid;
    
    // Get message text
    const text = message.message?.conversation ||
                 message.message?.extendedTextMessage?.text ||
                 message.message?.imageMessage?.caption ||
                 '';
    
    if (!text) return;

    console.log(`📩 Message from ${remoteJid}: ${text}`);

    // Mark as read
    await sock.readMessages([message.key]);

    // Show typing indicator
    await sock.sendPresenceUpdate('composing', remoteJid);

    let response;

    // Handle commands
    const command = text.toLowerCase().trim();
    
    if (command === '/start' || command === 'halo' || command === 'hi' || command === 'hello') {
      response = config.welcomeMessage;
    } else if (command === '/help' || command === 'help' || command === 'bantuan') {
      response = config.helpMessage;
    } else if (command === '/info' || command === 'info' || command === 'kontak') {
      response = config.infoMessage;
    } else if (command === '/reset' || command === 'reset') {
      chatHistory.delete(userId);
      response = '🔄 Percakapan telah direset. Silakan mulai pertanyaan baru.';
    } else {
      // Send to AI API
      response = await sendToAPI(text, userId);
    }

    // Format and send response
    const formattedResponse = formatMessage(response);
    
    await sock.sendMessage(remoteJid, { 
      text: formattedResponse 
    });

    console.log(`📤 Reply sent to ${remoteJid}`);
  } catch (error) {
    console.error('Message handling error:', error);
  }
}

/**
 * Start WhatsApp connection
 */
async function startBot() {
  console.log('🚀 Starting PDAM WhatsApp Bot...');
  
  // Load auth state
  const { state, saveCreds } = await useMultiFileAuthState(config.sessionDir);
  
  // Get latest Baileys version
  const { version } = await fetchLatestBaileysVersion();
  console.log(`📱 Using Baileys v${version.join('.')}`);

  // Create socket connection
  const sock = makeWASocket({
    version,
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, logger)
    },
    printQRInTerminal: false,
    logger,
    generateHighQualityLinkPreview: true,
    getMessage: async () => undefined
  });

  // Handle connection updates
  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;
    
    if (qr) {
      console.log('\n📱 Scan QR Code dengan WhatsApp Anda:\n');
      qrcode.generate(qr, { small: true });
      console.log('\n');
    }

    if (connection === 'close') {
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      
      if (reason === DisconnectReason.loggedOut) {
        console.log('❌ Device logged out. Please delete session folder and restart.');
        process.exit(1);
      } else {
        console.log('🔄 Connection closed. Reconnecting...');
        setTimeout(startBot, 3000);
      }
    } else if (connection === 'open') {
      console.log('✅ WhatsApp Bot connected successfully!');
      console.log(`📞 Bot Name: ${config.botName}`);
      console.log(`🌐 API URL: ${config.apiUrl}`);
      console.log('\n👋 Bot is ready to receive messages!\n');
    }
  });

  // Save credentials on update
  sock.ev.on('creds.update', saveCreds);

  // Handle incoming messages
  sock.ev.on('messages.upsert', async ({ messages: newMessages, type }) => {
    if (type !== 'notify') return;
    
    for (const message of newMessages) {
      // Skip messages from self
      if (message.key.fromMe) continue;
      
      // Skip status updates
      if (message.key.remoteJid === 'status@broadcast') continue;
      
      await handleMessage(sock, message);
    }
  });

  return sock;
}

// Start the bot
startBot().catch(console.error);

// Handle process termination
process.on('SIGINT', () => {
  console.log('\n👋 Shutting down WhatsApp Bot...');
  process.exit(0);
});
