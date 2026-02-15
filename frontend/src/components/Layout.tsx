import { ReactNode } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import { Loader2, LogOut, User } from 'lucide-react'
import { setAuthToken } from '../services/api'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, isLoading, logout, getAccessTokenSilently } = useAuth0()

  // Get and set auth token
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
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/50 backdrop-blur-md bg-slate-950/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                R
              </div>
              <span className="text-xl font-bold gradient-text">ResumeMaker AI</span>
            </div>

            {/* User Menu */}
            {user && (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-slate-300">
                  <User className="h-4 w-4" />
                  <span className="text-sm hidden sm:inline">{user.name || user.email}</span>
                </div>
                <button
                  onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                  className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 text-slate-300 text-sm transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/50 mt-auto py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-500 text-sm">
          <p>🔒 Secure authentication powered by Auth0</p>
          <p className="mt-1">We never store your resume data on our servers</p>
        </div>
      </footer>
    </div>
  )
}
