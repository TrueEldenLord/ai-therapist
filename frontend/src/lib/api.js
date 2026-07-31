import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: BASE })

export const api = {
  async newSession() {
    const { data } = await client.post('/api/session/new')
    return data // { session_id }
  },

  async analyzeFrame(imageBase64) {
    const { data } = await client.post('/api/analyze-face', {
      image: imageBase64,
    })
    return data // emotional context
  },

  async chat(sessionId, message, emotionalContext = {}) {
    const { data } = await client.post('/api/chat', {
      session_id: sessionId,
      message,
      emotional_context: emotionalContext,
    })
    return data // { text, audio, crisis }
  },
}
