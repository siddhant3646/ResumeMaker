import { ReactNode } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { Loader2, LogOut, User, FileText } from 'lucide-react'
import { setAuthToken } from '../services/api'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, isLoading, logout, getAccessTokenSilently } = useAuth0()

  const setupAuth = async () => {
    try {
      const token = await getAccessTokenSilently({
        authorizationParams: {
          audience: import.meta.env.VITE_AUTH0_AUDIENCE || `https://${import.meta.env.VITE_AUTH0_DOMAIN}/api/v2/`
        }
      })
      setAuthToken(token)
    } catch (error) {
      console.error('Error getting token:', error)
    }
  }

  if (!isLoading && user) {
    setupAuth()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen gradient-mesh flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="relative w-16 h-16 mx-auto mb-5">
            <div className="absolute inset-0 rounded-[1.25rem] bg-gradient-to-r from-indigo-500 to-purple-500 animate-spin-slow opacity-30"></div>
            <div className="absolute inset-2 rounded-2xl bg-zinc-950 flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
            </div>
          </div>
          <p className="text-zinc-500 font-medium tracking-wide">Initializing workspace...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen text-foreground bg-zinc-950 relative overflow-hidden flex flex-col">
      {/* Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] animate-pulse-glow"></div>
        <div className="absolute -bottom-40 -left-60 w-[600px] h-[600px] bg-purple-500/10 rounded-full blur-[150px] animate-pulse-glow delay-300"></div>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 backdrop-blur-2xl bg-zinc-950/60 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-6 sm:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Logo */}
            <div className="flex items-center gap-4 cursor-pointer group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-[1rem] blur-md opacity-40 group-hover:opacity-60 transition-opacity duration-300"></div>
                <div className="relative w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-[1rem] flex items-center justify-center shadow-lg group-hover:scale-[1.05] transition-transform duration-300">
                  <FileText className="w-6 h-6 text-white drop-shadow-sm" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold text-white tracking-tight">ResumeMaker</span>
                <span className="text-[11px] uppercase tracking-widest text-indigo-400 font-semibold -mt-0.5">AI Powered</span>
              </div>
            </div>

            {/* User Menu */}
            {user && (
              <div className="flex items-center gap-4">
                {/* User Info */}
                <div className="hidden sm:flex items-center gap-3 px-4 py-2 rounded-2xl glass-dark hover:bg-white/[0.04] transition-colors duration-300 cursor-default">
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name || 'User'}
                      className="w-8 h-8 rounded-full ring-2 ring-indigo-500/40"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <span className="text-[15px] text-white font-medium tracking-wide">{user.name || user.email}</span>
                </div>

                {/* Logout Button */}
                <button
                  onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                  className="flex items-center gap-2.5 px-5 py-2.5 rounded-2xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/40 text-red-400 text-sm font-semibold transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 py-10 flex-grow">
        {children}
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 mt-auto bg-black/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-6 text-sm text-zinc-500 font-medium tracking-wide">
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></div>
                <span>All systems operational</span>
              </div>
              <span className="hidden md:inline text-zinc-700">•</span>
              <span className="hidden md:inline text-zinc-400">Secure authentication by Auth0</span>
            </div>
            <div className="flex items-center gap-5">
              <span className="text-[13px] text-zinc-600 font-medium">We never store your resume data</span>
              <div className="flex items-center gap-1.5 text-[13px] text-zinc-500 font-semibold px-3 py-1 rounded-full bg-white/5 border border-white/10">
                <span>🔒</span>
                <span>End-to-end encrypted</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
