import { useState, useCallback, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import Avatar from '../components/Avatar'
import WebcamFeed from '../components/WebcamFeed'
import ChatWindow from '../components/ChatWindow'
import VoiceInput from '../components/VoiceInput'
import CrisisCard from '../components/CrisisCard'
import { useWebcam } from '../hooks/useWebcam'
import { api } from '../lib/api'

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: "Hello, I'm Mira. I'm here to listen and support you. How are you feeling today?",
}

export default function Session() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('sid')

  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [emotionContext, setEmotionContext] = useState(null)
  const [currentAudio, setCurrentAudio] = useState(null)
  const [crisis, setCrisis] = useState(false)
  const [sending, setSending] = useState(false)

  const latestEmotionRef = useRef(null)

  const handleEmotionUpdate = useCallback((ctx) => {
    setEmotionContext(ctx)
    latestEmotionRef.current = ctx
  }, [])

  const videoRef = useWebcam(handleEmotionUpdate, 2000)

  async function handleSend(message) {
    if (!sessionId || sending) return

    setSending(true)
    setMessages((prev) => [...prev, { role: 'user', content: message }])

    try {
      const response = await api.chat(
        sessionId,
        message,
        latestEmotionRef.current || {}
      )

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.text },
      ])
      setCurrentAudio(response.audio)

      if (response.crisis) {
        setCrisis(true)
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I had trouble responding. Please try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  if (!sessionId) {
    navigate('/')
    return null
  }

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800">
        <h1 className="text-brand-500 font-bold text-xl tracking-tight">MindMirror</h1>
        <button
          onClick={() => navigate('/')}
          className="text-slate-400 hover:text-white text-sm transition-colors"
        >
          End Session
        </button>
      </header>

      {/* Main layout */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left column: webcam + avatar */}
        <div className="w-72 flex-shrink-0 flex flex-col gap-4">
          <WebcamFeed videoRef={videoRef} emotionContext={emotionContext} />
          <div className="flex-1 min-h-0">
            <Avatar
              audioBase64={currentAudio}
              emotion={emotionContext?.dominant_emotion || 'neutral'}
            />
          </div>
        </div>

        {/* Right column: chat */}
        <div className="flex-1 flex flex-col bg-slate-900 rounded-2xl overflow-hidden border border-slate-800">
          <ChatWindow messages={messages} />
          <div className="p-3 border-t border-slate-800">
            <VoiceInput onSend={handleSend} disabled={sending || crisis} />
          </div>
        </div>
      </div>

      {/* Crisis overlay */}
      <CrisisCard visible={crisis} />
    </div>
  )
}
