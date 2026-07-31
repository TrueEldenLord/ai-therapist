import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mic, MicOff, Send } from 'lucide-react'
import { useSpeech } from '../hooks/useSpeech'

export default function VoiceInput({ onSend, disabled }) {
  const [text, setText] = useState('')

  const { listening, start, stop } = useSpeech((transcript) => {
    setText(transcript)
  })

  function handleSend() {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function toggleMic() {
    listening ? stop() : start()
  }

  return (
    <div className="flex items-end gap-2 p-3 bg-slate-800 rounded-2xl border border-slate-700">
      {/* Mic button */}
      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={toggleMic}
        disabled={disabled}
        className={`p-2 rounded-xl transition-colors ${
          listening
            ? 'bg-red-500 text-white'
            : 'bg-slate-700 text-slate-400 hover:text-white hover:bg-slate-600'
        } disabled:opacity-40`}
        title={listening ? 'Stop recording' : 'Start voice input'}
      >
        {listening ? <MicOff size={20} /> : <Mic size={20} />}
      </motion.button>

      {/* Text input */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={1}
        placeholder={listening ? 'Listening…' : 'Type or speak…'}
        className="flex-1 bg-transparent text-slate-100 placeholder-slate-500
                   resize-none outline-none text-sm leading-relaxed
                   disabled:opacity-40"
      />

      {/* Send button */}
      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        className="p-2 rounded-xl bg-brand-600 text-white hover:bg-brand-500
                   transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        title="Send"
      >
        <Send size={20} />
      </motion.button>
    </div>
  )
}
