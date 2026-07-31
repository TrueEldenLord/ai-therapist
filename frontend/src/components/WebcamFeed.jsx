const EMOTION_EMOJI = {
  happy: '😊', sad: '😔', angry: '😠', fearful: '😨',
  disgusted: '🤢', surprised: '😲', neutral: '😐',
}

const INTENSITY_COLOR = {
  high: 'text-red-400',
  moderate: 'text-amber-400',
  mild: 'text-green-400',
}

function intensityLabel(score) {
  if (score >= 0.6) return 'high'
  if (score >= 0.3) return 'moderate'
  return 'mild'
}

export default function WebcamFeed({ videoRef, emotionContext }) {
  const emotion = emotionContext?.dominant_emotion || 'neutral'
  const intensity = emotionContext?.emotion_intensity || 0
  const eyeContact = emotionContext?.eye_contact || '—'
  const label = intensityLabel(intensity)

  return (
    <div className="flex flex-col gap-3">
      {/* Video */}
      <div className="relative rounded-2xl overflow-hidden bg-slate-800 aspect-video">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover scale-x-[-1]" // mirror effect
        />
        {!emotionContext?.face_detected && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-slate-500 text-sm">No face detected</p>
          </div>
        )}
      </div>

      {/* Emotion Badge */}
      <div className="bg-slate-800 rounded-xl p-3 grid grid-cols-2 gap-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{EMOTION_EMOJI[emotion] || '😐'}</span>
          <div>
            <p className="text-slate-400 text-xs">Emotion</p>
            <p className={`font-semibold capitalize ${INTENSITY_COLOR[label]}`}>
              {emotion} ({label})
            </p>
          </div>
        </div>
        <div>
          <p className="text-slate-400 text-xs">Eye contact</p>
          <p className="font-semibold capitalize text-slate-200">{eyeContact}</p>
        </div>
      </div>
    </div>
  )
}
