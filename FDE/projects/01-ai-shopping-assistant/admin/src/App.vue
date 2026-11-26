<template>
  <div class="admin-container">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>🧱 客服工作台</h2>
      </div>
      <div class="session-list">
        <div class="list-title">活跃会话</div>
        <div
          v-for="s in sessions"
          :key="s.session_id"
          :class="['session-item', { active: s.session_id === activeSession }]"
          @click="joinSession(s.session_id)"
        >
          <div class="session-info">
            <span class="session-name">{{ s.session_id }}</span>
            <span class="session-count">{{ s.message_count }} 条消息</span>
          </div>
        </div>
        <div v-if="sessions.length === 0" class="empty-list">
          暂无活跃会话
        </div>
      </div>
      <div class="sidebar-footer">
        <span :class="['status-dot', { connected: adminConnected }]"></span>
        {{ adminConnected ? '已连接' : '断开连接' }}
      </div>
    </aside>

    <main class="main-panel">
      <div v-if="!activeSession" class="no-session">
        <div class="no-session-icon">📋</div>
        <p>选择左侧会话查看实时对话</p>
      </div>

      <template v-else>
        <header class="panel-header">
          <h3>会话: {{ activeSession }}</h3>
          <span class="message-count">{{ conversation.length }} 条消息</span>
        </header>

        <div class="conversation-view" ref="convContainer">
          <div
            v-for="(msg, idx) in conversation"
            :key="idx"
            :class="['conv-message', msg.role]"
          >
            <div class="conv-avatar">{{ roleAvatar(msg.role) }}</div>
            <div class="conv-body">
              <div class="conv-role">
                {{ roleLabel(msg.role) }}
                <span class="conv-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="conv-content">{{ msg.content }}</div>
              <div v-if="msg.tool_calls?.length" class="conv-tools">
                <span
                  v-for="(tc, i) in msg.tool_calls"
                  :key="i"
                  class="conv-tool-tag"
                >
                  ⚙ {{ tc.name }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="intervening" class="conv-message agent">
            <div class="conv-avatar">🧱</div>
            <div class="conv-body">
              <div class="conv-role">小砖家</div>
              <div class="conv-content thinking">正在思考...</div>
            </div>
          </div>
        </div>

        <div class="intervene-bar">
          <input
            v-model="interveneText"
            @keyup.enter="intervene"
            placeholder="输入介入消息，以客户身份发送给 Agent..."
            :disabled="!adminConnected"
          />
          <button
            class="intervene-btn"
            @click="intervene"
            :disabled="!adminConnected || !interveneText.trim() || intervening"
          >
            介入发送
          </button>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue'

// 开发环境走 Vite 的 /ws 代理；部署时可用 VITE_WS_URL 覆盖。
const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/admin`

export default {
  name: 'AdminApp',
  setup() {
    const sessions = ref([])
    const activeSession = ref('')
    const conversation = ref([])
    const interveneText = ref('')
    const intervening = ref(false)
    const adminConnected = ref(false)
    const convContainer = ref(null)
    let ws = null

    const allConversations = {}

    function connect() {
      ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        adminConnected.value = true
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.type === 'session_list') {
          sessions.value = data.sessions
        } else if (data.type === 'session_history') {
          conversation.value = data.messages
          scrollBottom()
        } else if (data.type === 'conversation') {
          const msg = data.message
          const sid = msg.session_id

          if (!allConversations[sid]) {
            allConversations[sid] = []
          }
          allConversations[sid].push(msg)

          if (sid === activeSession.value) {
            conversation.value = [...allConversations[sid]]
            scrollBottom()
          }

          const existing = sessions.value.find((s) => s.session_id === sid)
          if (existing) {
            existing.message_count = allConversations[sid].length
          } else {
            sessions.value.push({
              session_id: sid,
              message_count: 1,
              created_at: msg.timestamp,
            })
          }
        } else if (data.type === 'intervene_result') {
          intervening.value = false
        } else if (data.type === 'error') {
          intervening.value = false
        }
      }

      ws.onclose = () => {
        adminConnected.value = false
        setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        adminConnected.value = false
      }
    }

    function joinSession(sid) {
      activeSession.value = sid
      if (allConversations[sid]) {
        conversation.value = [...allConversations[sid]]
      } else {
        conversation.value = []
      }
      ws.send(JSON.stringify({ action: 'join_session', session_id: sid }))
      scrollBottom()
    }

    function intervene() {
      const text = interveneText.value.trim()
      if (!text || !ws || !activeSession.value) return

      intervening.value = true
      interveneText.value = ''

      conversation.value.push({
        role: 'admin',
        content: text,
        timestamp: new Date().toISOString(),
      })
      scrollBottom()

      ws.send(
        JSON.stringify({
          action: 'intervene',
          session_id: activeSession.value,
          message: text,
        })
      )
    }

    function scrollBottom() {
      nextTick(() => {
        const el = convContainer.value
        if (el) el.scrollTop = el.scrollHeight
      })
    }

    function roleAvatar(role) {
      return role === 'client'
        ? '👤'
        : role === 'agent'
          ? '🧱'
          : role === 'admin'
            ? '🎧'
            : '❓'
    }

    function roleLabel(role) {
      return role === 'client'
        ? '客户'
        : role === 'agent'
          ? '小砖家'
          : role === 'admin'
            ? '客服(介入)'
            : role
    }

    function formatTime(ts) {
      if (!ts) return ''
      return new Date(ts).toLocaleTimeString()
    }

    onMounted(connect)
    onUnmounted(() => ws?.close())

    return {
      sessions,
      activeSession,
      conversation,
      interveneText,
      intervening,
      adminConnected,
      convContainer,
      joinSession,
      intervene,
      roleAvatar,
      roleLabel,
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
  background: #f0f2f5;
  height: 100vh;
}

.admin-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 280px;
  background: #1a1a2e;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #2a2a4e;
}

.sidebar-header h2 {
  font-size: 16px;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.list-title {
  padding: 8px 20px;
  font-size: 12px;
  text-transform: uppercase;
  color: #888;
  letter-spacing: 0.5px;
}

.session-item {
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.session-item:hover {
  background: #252547;
}

.session-item.active {
  background: #252547;
  border-left-color: #ff6d00;
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-name {
  font-family: monospace;
  font-size: 13px;
}

.session-count {
  font-size: 11px;
  color: #888;
}

.empty-list {
  padding: 20px;
  text-align: center;
  color: #666;
  font-size: 13px;
}

.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid #2a2a4e;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e74c3c;
}

.status-dot.connected {
  background: #2ecc71;
}

.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.no-session {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  gap: 12px;
}

.no-session-icon {
  font-size: 48px;
}

.panel-header {
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.message-count {
  font-size: 12px;
  color: #888;
}

.conversation-view {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.conv-message {
  display: flex;
  gap: 12px;
}

.conv-message.admin {
  border-left: 3px solid #ff6d00;
  padding-left: 9px;
}

.conv-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.conv-body {
  flex: 1;
}

.conv-role {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conv-time {
  font-weight: 400;
  color: #aaa;
  font-size: 11px;
}

.conv-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.conv-content.thinking {
  color: #aaa;
  font-style: italic;
}

.conv-message.admin .conv-content {
  background: #fff3e0;
  padding: 10px 14px;
  border-radius: 8px;
}

.conv-message.client .conv-content {
  background: #e3f2fd;
  padding: 10px 14px;
  border-radius: 8px 8px 8px 2px;
}

.conv-message.agent .conv-content {
  background: #f5f5f5;
  padding: 10px 14px;
  border-radius: 8px 8px 2px 8px;
}

.conv-tools {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.conv-tool-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.06);
  color: #888;
}

.intervene-bar {
  padding: 16px 24px;
  border-top: 2px solid #ff6d00;
  background: #fff8f0;
  display: flex;
  gap: 10px;
}

.intervene-bar input {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #ffe0b2;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.intervene-bar input:focus {
  border-color: #ff6d00;
}

.intervene-bar button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ff6d00, #e65100);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.intervene-bar button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.intervene-bar button:not(:disabled):hover {
  opacity: 0.9;
}
</style>
