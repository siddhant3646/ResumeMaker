import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { Loader2 } from 'lucide-react'
import Layout from './components/Layout'
import Home from './pages/Home'
import Editor from './pages/Editor'
import LoginButton from './components/auth/LoginButton'

function App() {
  const { isLoading, isAuthenticated, error } = useAuth0()

  if (error) {
    console.error('Auth0 error:', error)
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="text-center">
          <h1 className="text-2xl text-red-500 mb-4">Authentication Error</h1>
          <p className="text-slate-400 mb-4">{error.message}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Authenticating...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              ResumeMaker AI
            </h1>
            <p className="text-slate-400">
              Sign in to create ATS-optimized resumes
            </p>
          </div>
          <LoginButton />
        </div>
      </div>
    )
  }

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/editor" element={<Editor />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
