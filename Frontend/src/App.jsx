import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import ChatPage from './pages/ChatPage'
import LoginPage from './pages/LoginPage'

// Demo users matching the database sample data
const demoUsers = {
  'user_sample_001': {
    id: 'user_sample_001',
    name: 'John Doe',
    email: 'john.doe@example.com',
    title: 'Sample User',
    role: 'user',
    org_id: 'org_sample_001'
  },
  'user_sample_002': {
    id: 'user_sample_002',
    name: 'Jane Doe',
    email: 'jane.doe@example.com',
    title: 'Sample User',
    role: 'admin',
    org_id: 'org_sample_001'
  }
}

const organizations = {
  'org_sample_001': {
    id: 'org_sample_001',
    name: 'Sample Organization'
  }
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleLogin = (userId, navigate) => {
    setLoading(true)
    // Simulate login delay
    setTimeout(() => {
      setCurrentUser(demoUsers[userId])
      setLoading(false)
      if (navigate) {
        navigate('/chat')
      }
    }, 500)
  }

  const handleLogout = () => {
    setCurrentUser(null)
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/login"
          element={
            currentUser ? (
              <Navigate to="/chat" replace />
            ) : (
              <LoginPage
                onLogin={handleLogin}
                loading={loading}
                demoUsers={demoUsers}
              />
            )
          }
        />
        <Route
          path="/chat"
          element={
            currentUser ? (
              <ChatPage
                user={currentUser}
                org={organizations[currentUser.org_id]}
                onLogout={handleLogout}
              />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  )
}