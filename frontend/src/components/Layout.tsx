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
      const token = await getAccessTokenSilently()
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
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 animate-spin-slow opacity-30"></div>
            <div className="absolute inset-2 rounded-xl bg-slate-900 flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
            </div>
          </div>
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-mesh relative">
      {/* Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 backdrop-blur-xl bg-slate-900/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl blur opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div className="relative w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <FileText className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold text-white">ResumeMaker</span>
                <span className="text-xs text-indigo-400 -mt-0.5">AI Powered</span>
              </div>
            </div>

            {/* User Menu */}
            {user && (
              <div className="flex items-center gap-3">
                {/* User Info */}
                <div className="hidden sm:flex items-center gap-3 px-4 py-2 rounded-xl glass">
                  {user.picture ? (
                    <img 
                      src={user.picture} 
                      alt={user.name || 'User'} 
                      className="w-7 h-7 rounded-full ring-2 ring-indigo-500/30"
                    />
                  ) : (
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <span className="text-sm text-slate-300 font-medium">{user.name || user.email}</span>
                </div>

                {/* Logout Button */}
                <button
                  onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/30 text-red-400 text-sm font-medium transition-all duration-300 hover:-translate-y-0.5"
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
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-6 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span>All systems operational</span>
              </div>
              <span className="hidden md:inline">•</span>
              <span className="hidden md:inline">Secure authentication by Auth0</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-slate-600">We never store your resume data</span>
              <div className="flex items-center gap-1 text-xs text-slate-500">
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
