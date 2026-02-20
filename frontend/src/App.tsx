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
          <div className="orb orb-1 -top-40 -left-60"></div>
          <div className="orb orb-2 top-1/2 -right-40"></div>
          <div className="orb orb-3 -bottom-60 left-1/4"></div>
        </div>

        {/* Grid Pattern Overlay */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '40px 40px'
          }}
        ></div>

        {/* Main Content */}
        <div className="relative z-10 min-h-screen flex items-center justify-center p-6 sm:p-8">
          <div className="max-w-7xl w-full">
            <div className="grid lg:grid-cols-12 gap-12 lg:gap-8 items-center">
              
              {/* Left Side - Hero */}
              <div className="lg:col-span-7 xl:col-span-6 text-center lg:text-left animate-fade-in-up">
                {/* Logo Badge */}
                <div className="badge badge-glow mb-8 animate-float">
                  <Sparkles className="w-3.5 h-3.5 mr-2 text-indigo-300" />
                  <span>AI-Powered Resume Builder</span>
                </div>

                {/* Main Heading */}
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1]">
                  <span className="text-white">Craft Your </span>
                  <br className="hidden lg:block" />
                  <span className="gradient-text">Perfect Resume</span>
                </h1>

                {/* Subheading */}
                <p className="text-lg sm:text-xl text-zinc-400 mb-10 max-w-2xl mx-auto lg:mx-0 leading-relaxed font-medium">
                  Stand out from the crowd with ATS-optimized resumes meticulously tailored for your dream job at top-tier tech companies.
                </p>

                {/* Feature Pills */}
                <div className="flex flex-wrap gap-4 justify-center lg:justify-start mb-12">
                  <div className="flex items-center gap-2.5 px-5 py-2.5 rounded-2xl glass-dark font-medium text-sm text-indigo-300 transition-transform hover:scale-105">
                    <Zap className="w-4 h-4" />
                    <span>AI Optimized</span>
                  </div>
                  <div className="flex items-center gap-2.5 px-5 py-2.5 rounded-2xl glass-dark font-medium text-sm text-purple-300 transition-transform hover:scale-105">
                    <FileText className="w-4 h-4" />
                    <span>ATS Friendly</span>
                  </div>
                  <div className="flex items-center gap-2.5 px-5 py-2.5 rounded-2xl glass-dark font-medium text-sm text-blue-300 transition-transform hover:scale-105">
                    <Shield className="w-4 h-4" />
                    <span>Secure & Private</span>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-8 pt-10 border-t border-white/10 max-w-2xl mx-auto lg:mx-0">
                  <div>
                    <div className="text-4xl font-black text-white mb-1">10K+</div>
                    <div className="text-sm font-medium text-zinc-500 uppercase tracking-wide">Resumes</div>
                  </div>
                  <div>
                    <div className="text-4xl font-black text-white mb-1">95%</div>
                    <div className="text-sm font-medium text-zinc-500 uppercase tracking-wide">ATS Pass</div>
                  </div>
                  <div>
                    <div className="text-4xl font-black text-white mb-1">4.9★</div>
                    <div className="text-sm font-medium text-zinc-500 uppercase tracking-wide">Rating</div>
                  </div>
                </div>
              </div>

              {/* Right Side - Login Card */}
              <div className="lg:col-span-5 xl:col-span-5 lg:col-start-8 animate-fade-in-up delay-200">
                <div className="card-modern gradient-border">
                  {/* Card Header */}
                  <div className="text-center mb-10">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-[2rem] bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg glow">
                      <FileText className="w-10 h-10 text-white drop-shadow-md" />
                    </div>
                    <h2 className="text-3xl font-bold text-white mb-3 tracking-tight">Get Started</h2>
                    <p className="text-zinc-400 font-medium">Sign in to create your optimized resume</p>
                  </div>

                  {/* Login Buttons */}
                  <LoginButton />

                  {/* Terms */}
                  <p className="text-center text-sm text-zinc-500 mt-8 font-medium">
                    By signing in, you agree to our <br />
                    <a href="#" className="text-zinc-300 hover:text-white transition-colors underline decoration-zinc-700 underline-offset-4">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="#" className="text-zinc-300 hover:text-white transition-colors underline decoration-zinc-700 underline-offset-4">
                      Privacy Policy
                    </a>
                  </p>
                </div>

                {/* Trust Badges */}
                <div className="mt-8 flex items-center justify-center gap-5 text-zinc-500 text-sm font-semibold tracking-wide uppercase">
                  <div className="flex items-center gap-1.5">
                    <Shield className="w-4 h-4" />
                    <span>Secure</span>
                  </div>
                  <span className="text-zinc-700">•</span>
                  <div className="flex items-center gap-1.5">
                    <span>🔒</span>
                    <span>Encrypted</span>
                  </div>
                  <span className="text-zinc-700">•</span>
                  <div className="flex items-center gap-1.5">
                    <span>⚡</span>
                    <span>Fast</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Bottom Gradient Fade */}
        <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-zinc-950 to-transparent pointer-events-none"></div>
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
