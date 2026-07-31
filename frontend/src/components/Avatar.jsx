import { useRef, useEffect, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { useGLTF, OrbitControls, Environment } from '@react-three/drei'

const EMOTION_EXPRESSIONS = {
  happy:     { mouthSmileLeft: 0.6, mouthSmileRight: 0.6, eyeSquintLeft: 0.3, eyeSquintRight: 0.3 },
  sad:       { mouthFrownLeft: 0.5, mouthFrownRight: 0.5, browInnerUp: 0.4 },
  angry:     { browDownLeft: 0.6, browDownRight: 0.6, mouthFrownLeft: 0.3, mouthFrownRight: 0.3 },
  fearful:   { browInnerUp: 0.7, eyeWideLeft: 0.5, eyeWideRight: 0.5 },
  surprised: { eyeWideLeft: 0.8, eyeWideRight: 0.8, mouthOpen: 0.3, jawOpen: 0.2 },
  neutral:   {},
  disgusted: { noseSneerLeft: 0.5, noseSneerRight: 0.5 },
}

function AvatarModel({ analyserRef, emotion }) {
  const { scene } = useGLTF('/avatar.glb')
  const meshRef = useRef(null)

  // Find the mesh with morph targets (blend shapes)
  useEffect(() => {
    scene.traverse((child) => {
      if (child.isMesh && child.morphTargetDictionary) {
        meshRef.current = child
      }
    })
  }, [scene])

  useFrame(() => {
    const mesh = meshRef.current
    if (!mesh || !mesh.morphTargetDictionary) return

    // Lip sync from audio amplitude
    if (analyserRef.current) {
      const data = new Uint8Array(analyserRef.current.frequencyBinCount)
      analyserRef.current.getByteFrequencyData(data)
      const avg = data.reduce((a, b) => a + b, 0) / data.length
      const mouthOpen = Math.min(avg / 128, 1)
      const jawIdx = mesh.morphTargetDictionary['jawOpen']
      if (jawIdx !== undefined) {
        mesh.morphTargetInfluences[jawIdx] = mouthOpen * 0.6
      }
    }

    // Emotion expression blend shapes
    const expressions = EMOTION_EXPRESSIONS[emotion] || {}
    Object.entries(mesh.morphTargetDictionary).forEach(([name, idx]) => {
      const target = expressions[name] ?? 0
      const current = mesh.morphTargetInfluences[idx]
      // Smooth interpolation toward target
      mesh.morphTargetInfluences[idx] = current + (target - current) * 0.05
    })
  })

  return (
    <primitive
      object={scene}
      scale={2}
      position={[0, -1.5, 0]}
    />
  )
}

export default function Avatar({ audioBase64, emotion = 'neutral' }) {
  const analyserRef = useRef(null)
  const audioCtxRef = useRef(null)

  useEffect(() => {
    if (!audioBase64) return

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    audioCtxRef.current = audioCtx

    const analyser = audioCtx.createAnalyser()
    analyser.fftSize = 256
    analyserRef.current = analyser

    const binary = atob(audioBase64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

    audioCtx.decodeAudioData(bytes.buffer).then((buffer) => {
      const source = audioCtx.createBufferSource()
      source.buffer = buffer
      source.connect(analyser)
      analyser.connect(audioCtx.destination)
      source.start()
      source.onended = () => {
        analyserRef.current = null
      }
    })

    return () => audioCtx.close()
  }, [audioBase64])

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden bg-slate-900">
      <Canvas camera={{ position: [0, 0, 3], fov: 50 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[2, 4, 2]} intensity={1} />
        <Environment preset="city" />
        <Suspense fallback={null}>
          <AvatarModel
            analyserRef={analyserRef}
            emotion={emotion}
          />
        </Suspense>
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          minPolarAngle={Math.PI / 3}
          maxPolarAngle={Math.PI / 2}
        />
      </Canvas>
    </div>
  )
}

useGLTF.preload('/avatar.glb')
