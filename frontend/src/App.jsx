import { Routes, Route, Navigate } from 'react-router-dom'
import Welcome from './pages/Welcome'
import Session from './pages/Session'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route path="/session" element={<Session />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
