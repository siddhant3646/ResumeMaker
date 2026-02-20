import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { Loader2, Sparkles, FileText, Zap, Shield } from 'lucide-react'
import Layout from './components/Layout'
import Home from './pages/Home'
import Editor from './pages/Editor'
import LoginButton from './components/auth/LoginButton'

function App() {
  const { isLoading, isAuthenticated, error } = useAuth0()

  if (error) {
    console.error('Auth0 error:', error)
    return (
      <div className="min-h-screen gradient-mesh flex items-center justify-center p-4">
        <div className="glass rounded-2xl p-8 max-w-md w-full text-center animate-scale-in">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Authentication Error</h1>
          <p className="text-slate-400 mb-6">{error.message}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-primary w-full text-white"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen gradient-mesh flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 animate-spin-slow opacity-20"></div>
            <div className="absolute inset-2 rounded-full bg-slate-900 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
            </div>
          </div>
          <p className="text-slate-400 text-lg">Authenticating...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen gradient-mesh relative overflow-hidden">
        {/* Floating Orbs Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="orb orb-1 -top-40 -left-40"></div>
          <div className="orb orb-2 top-1/2 -right-40"></div>
          <div className="orb orb-3 -bottom-40 left-1/3"></div>
        </div>

        {/* Grid Pattern Overlay */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}
        ></div>

        {/* Main Content */}
        <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
          <div className="max-w-6xl w-full">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              
              {/* Left Side - Hero */}
              <div className="text-center lg:text-left animate-fade-in-up">
                {/* Logo */}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm text-slate-300">AI-Powered Resume Builder</span>
                </div>

                {/* Main Heading */}
                <h1 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                  <span className="text-white">Craft Your </span>
                  <span className="gradient-text">Perfect Resume</span>
                </h1>

                {/* Subheading */}
                <p className="text-xl text-slate-400 mb-8 max-w-lg mx-auto lg:mx-0">
                  Stand out from the crowd with ATS-optimized resumes tailored for your dream job at FAANG & MAANG companies.
                </p>

                {/* Feature Pills */}
                <div className="flex flex-wrap gap-3 justify-center lg:justify-start mb-8">
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                    <Zap className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm text-indigo-300">AI Optimized</span>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20">
                    <FileText className="w-4 h-4 text-purple-400" />
                    <span className="text-sm text-purple-300">ATS Friendly</span>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20">
                    <Shield className="w-4 h-4 text-blue-400" />
                    <span className="text-sm text-blue-300">Secure</span>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-6 pt-8 border-t border-white/10">
                  <div>
                    <div className="text-3xl font-bold text-white">10K+</div>
                    <div className="text-sm text-slate-500">Resumes Created</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-white">95%</div>
                    <div className="text-sm text-slate-500">ATS Pass Rate</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-white">4.9★</div>
                    <div className="text-sm text-slate-500">User Rating</div>
                  </div>
                </div>
              </div>

              {/* Right Side - Login Card */}
              <div className="animate-fade-in-up delay-200">
                <div className="glass rounded-3xl p-8 lg:p-10 gradient-border">
                  {/* Card Header */}
                  <div className="text-center mb-8">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg glow">
                      <FileText className="w-8 h-8 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Get Started</h2>
                    <p className="text-slate-400">Sign in to create your optimized resume</p>
                  </div>

                  {/* Login Buttons */}
                  <LoginButton />

                  {/* Terms */}
                  <p className="text-center text-xs text-slate-500 mt-6">
                    By signing in, you agree to our{' '}
                    <a href="#" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="#" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                      Privacy Policy
                    </a>
                  </p>
                </div>

                {/* Trust Badges */}
                <div className="mt-6 flex items-center justify-center gap-4 text-slate-500 text-sm">
                  <div className="flex items-center gap-1">
                    <Shield className="w-4 h-4" />
                    <span>Secure</span>
                  </div>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    <span>🔒</span>
                    <span>Encrypted</span>
                  </div>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    <span>⚡</span>
                    <span>Fast</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Bottom Gradient Fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-900/50 to-transparent pointer-events-none"></div>
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
