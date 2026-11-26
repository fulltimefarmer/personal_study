<template>
  <div class="chat-container">
    <header class="chat-header">
      <h1>🧱 乐高智能导购助手 · 小砖家</h1>
      <span class="session-id">会话: {{ sessionId }}</span>
    </header>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0 && !connected" class="welcome">
        <div class="welcome-icon">🧱</div>
        <h2>欢迎来到乐高旗舰店！</h2>
        <p>我是导购助手小砖家，有什么可以帮您？</p>
      </div>
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['message', msg.role]"
      >
        <div class="message-avatar">{{ avatar(msg.role) }}</div>
        <div class="message-bubble">
          <div class="message-content">{{ msg.content }}</div>
          <div v-if="msg.tool_calls?.length" class="tool-calls">
            <div v-for="(tc, i) in msg.tool_calls" :key="i" class="tool-tag">
              ⚙ {{ tc.name }}
            </div>
          </div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
      <div v-if="thinking" class="message agent">
        <div class="message-avatar">🧱</div>
        <div class="message-bubble thinking">
          <span class="dot-pulse"></span>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <input
        v-model="input"
        @keyup.enter="send"
        placeholder="输入您的问题..."
        :disabled="!connected"
      />
      <button @click="send" :disabled="!connected || !input.trim()">发送</button>
    </div>
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

// 开发环境走 Vite 的 /ws 代理；部署时可用 VITE_WS_URL 覆盖。
const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/chat`

export default {
  name: 'App',
  setup() {
    const messages = ref([])
    const input = ref('')
    const thinking = ref(false)
    const connected = ref(false)
    const sessionId = ref('')
    const messagesContainer = ref(null)
    let ws = null

    function genSessionId() {
      const stored = sessionStorage.getItem('lego_session_id')
      if (stored) return stored
      const id = 'cli_' + Math.random().toString(36).substring(2, 10)
      sessionStorage.setItem('lego_session_id', id)
      return id
    }

    function connect() {
      sessionId.value = genSessionId()
      ws = new WebSocket(`${WS_URL}/${sessionId.value}`)

      ws.onopen = () => {
        connected.value = true
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'history') {
          messages.value = data.messages.map((m) => ({
            role: m.role,
            content: m.content,
            tool_calls: m.tool_calls,
            timestamp: m.timestamp,
          }))
          scrollBottom()
        } else if (data.type === 'response') {
          thinking.value = false
          messages.value.push({
            role: 'agent',
            content: data.answer,
            tool_calls: data.tool_calls_log,
            timestamp: new Date().toISOString(),
          })
          scrollBottom()
        } else if (data.type === 'error') {
          thinking.value = false
          messages.value.push({
            role: 'agent',
            content: '抱歉，出了点问题，请重试。',
            timestamp: new Date().toISOString(),
          })
        }
      }

      ws.onclose = () => {
        connected.value = false
        setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        connected.value = false
      }
    }

    function send() {
      const text = input.value.trim()
      if (!text || !ws) return

      messages.value.push({
        role: 'client',
        content: text,
        timestamp: new Date().toISOString(),
      })
      input.value = ''
      thinking.value = true
      scrollBottom()

      ws.send(JSON.stringify({ message: text }))
    }

    function scrollBottom() {
      nextTick(() => {
        const el = messagesContainer.value
        if (el) el.scrollTop = el.scrollHeight
      })
    }

    function avatar(role) {
      return role === 'client' ? '👤' : role === 'agent' ? '🧱' : '👤'
    }

    function formatTime(ts) {
      if (!ts) return ''
      return new Date(ts).toLocaleTimeString()
    }

    onMounted(connect)
    onUnmounted(() => ws?.close())

    return {
      messages,
      input,
      thinking,
      connected,
      sessionId,
      messagesContainer,
      send,
      avatar,
      formatTime,
    }
  },
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  height: 100vh;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

.chat-header {
  padding: 16px 24px;
  background: linear-gradient(135deg, #ffda44, #ff6d00);
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h1 {
  font-size: 18px;
  font-weight: 600;
}

.session-id {
  font-size: 12px;
  opacity: 0.8;
  font-family: monospace;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.welcome h2 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 80%;
}

.message.client {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.agent {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.client .message-bubble {
  background: #007aff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.agent .message-bubble {
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-bubble.thinking {
  padding: 16px 20px;
}

.dot-pulse {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  animation: pulse 1.4s infinite ease-in-out;
}

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

.message-time {
  font-size: 11px;
  opacity: 0.5;
  margin-top: 4px;
}

.tool-calls {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.tool-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.08);
  color: #666;
}

.chat-input {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 10px;
}

.chat-input input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input input:focus {
  border-color: #ff6d00;
}

.chat-input button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #ffda44, #ff6d00);
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.chat-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input button:not(:disabled):hover {
  opacity: 0.9;
}
</style>
