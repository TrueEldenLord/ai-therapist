import { useEffect, useRef, useCallback } from 'react'
import { api } from '../lib/api'

export function useWebcam(onEmotionUpdate, intervalMs = 2000) {
  const videoRef = useRef(null)
  const canvasRef = useRef(document.createElement('canvas'))
  const streamRef = useRef(null)
  const intervalRef = useRef(null)

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || video.readyState < 2) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)

    // Remove the "data:image/jpeg;base64," prefix
    const base64 = canvas.toDataURL('image/jpeg', 0.7).split(',')[1]
    api.analyzeFrame(base64)
      .then(onEmotionUpdate)
      .catch(() => {}) // silently ignore analysis errors
  }, [onEmotionUpdate])

  useEffect(() => {
    let active = true

    navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480 } })
      .then((stream) => {
        if (!active) { stream.getTracks().forEach(t => t.stop()); return }
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      })
      .catch(console.error)

    intervalRef.current = setInterval(captureFrame, intervalMs)

    return () => {
      active = false
      clearInterval(intervalRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [captureFrame, intervalMs])

  return videoRef
}
