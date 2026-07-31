import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../lib/api'

export default function Welcome() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleBegin() {
    setLoading(true)
    setError(null)
    try {
      const { session_id } = await api.newSession()
      navigate(`/session?sid=${session_id}`)
    } catch {
      setError('Could not connect to the server. Make sure the backend is running.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-slate-950">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-lg w-full text-center space-y-8"
      >
        {/* Logo / Title */}
        <div className="space-y-2">
          <h1 className="text-5xl font-bold text-brand-500 tracking-tight">
            MindMirror
          </h1>
          <p className="text-slate-400 text-lg">
            An AI companion that sees how you feel
          </p>
        </div>

        {/* Disclaimer Card */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 text-left space-y-3">
          <h2 className="text-amber-400 font-semibold text-sm uppercase tracking-wider">
            Important Notice
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            MindMirror is an AI tool for emotional support and reflection only.
            It is <strong className="text-white">not a substitute</strong> for
            professional mental health care, diagnosis, or treatment.
          </p>
          <p className="text-slate-300 text-sm leading-relaxed">
            If you are in crisis or feel you may harm yourself or others, please
            call or text{' '}
            <a href="tel:988" className="text-brand-500 font-bold hover:underline">
              988
            </a>{' '}
            (Suicide &amp; Crisis Lifeline) immediately.
          </p>
        </div>

        {/* Begin Button */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleBegin}
          disabled={loading}
          className="w-full py-4 rounded-2xl bg-brand-600 hover:bg-brand-500
                     text-white font-semibold text-lg transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Starting session…' : 'Begin Session'}
        </motion.button>

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        <p className="text-slate-600 text-xs">
          By continuing you acknowledge the above notice.
        </p>
      </motion.div>
    </div>
  )
}
