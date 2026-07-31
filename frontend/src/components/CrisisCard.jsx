import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Phone, MessageSquare, Globe } from 'lucide-react'

const RESOURCES = [
  {
    icon: Phone,
    label: 'Call or Text',
    name: 'Suicide & Crisis Lifeline',
    value: '988',
    href: 'tel:988',
    color: 'text-red-400',
  },
  {
    icon: MessageSquare,
    label: 'Text',
    name: 'Crisis Text Line',
    value: 'HOME to 741741',
    href: 'sms:741741?body=HOME',
    color: 'text-amber-400',
  },
  {
    icon: Globe,
    label: 'International',
    name: 'Find A Helpline',
    value: 'findahelpline.com',
    href: 'https://findahelpline.com',
    color: 'text-blue-400',
  },
]

export default function CrisisCard({ visible }) {
  const navigate = useNavigate()

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center
                     bg-slate-950/95 backdrop-blur-sm px-6"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            className="max-w-md w-full bg-slate-800 border border-slate-600
                       rounded-3xl p-8 space-y-6"
          >
            <div className="text-center space-y-2">
              <div className="text-4xl">💙</div>
              <h2 className="text-2xl font-bold text-white">
                You're not alone
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                I hear you, and I'm really glad you reached out.
                Please connect with someone who can help right now.
              </p>
            </div>

            <div className="space-y-3">
              {RESOURCES.map((r) => (
                <a
                  key={r.name}
                  href={r.href}
                  target={r.href.startsWith('http') ? '_blank' : undefined}
                  rel="noreferrer"
                  className="flex items-center gap-4 bg-slate-700 hover:bg-slate-600
                             rounded-2xl p-4 transition-colors"
                >
                  <r.icon className={`${r.color} flex-shrink-0`} size={24} />
                  <div>
                    <p className="text-slate-400 text-xs">{r.label}</p>
                    <p className="text-white font-semibold text-sm">{r.name}</p>
                    <p className={`${r.color} font-bold`}>{r.value}</p>
                  </div>
                </a>
              ))}
            </div>

            <button
              onClick={() => navigate('/')}
              className="w-full py-3 rounded-2xl bg-slate-700 hover:bg-slate-600
                         text-slate-300 text-sm transition-colors"
            >
              Return to home
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
