import { useAuth0 } from '@auth0/auth0-react'

export default function LoginButton() {
  const { loginWithRedirect } = useAuth0()

  const handleGoogleLogin = () => {
    loginWithRedirect({
      authorizationParams: {
        connection: 'google-oauth2'
      }
    })
  }

  const handleGithubLogin = () => {
    loginWithRedirect({
      authorizationParams: {
        connection: 'github'
      }
    })
  }

  return (
    <div className="space-y-4">
      {/* Google Login Button */}
      <button
        onClick={handleGoogleLogin}
        className="group w-full relative flex items-center justify-center gap-3 px-6 py-4 bg-white/95 hover:bg-white text-zinc-900 font-semibold rounded-2xl transition-all duration-300 shadow-[0_2px_10px_rgba(0,0,0,0.1),inset_0_1px_0_rgba(255,255,255,1)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.15),inset_0_1px_0_rgba(255,255,255,1)] hover:scale-[1.02] active:scale-[0.98] overflow-hidden backdrop-blur-md"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-white/40 to-transparent opacity-50 pointer-events-none"></div>
        <svg className="w-5 h-5 relative z-10" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
        <span className="relative z-10 text-[15px] tracking-wide">Continue with Google</span>
      </button>

      {/* GitHub Login Button */}
      <button
        onClick={handleGithubLogin}
        className="group w-full relative flex items-center justify-center gap-3 px-6 py-4 bg-zinc-900/80 hover:bg-zinc-800 text-white font-semibold rounded-2xl border border-white/10 transition-all duration-300 shadow-[0_2px_10px_rgba(0,0,0,0.5)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.4)] hover:border-white/20 hover:scale-[1.02] active:scale-[0.98] backdrop-blur-xl overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent opacity-50 pointer-events-none"></div>
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 blur-xl"></div>

        <svg className="w-5 h-5 relative z-10 drop-shadow-md" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
        </svg>
        <span className="relative z-10 text-[15px] tracking-wide text-white/90">Continue with GitHub</span>
      </button>

      {/* Divider */}
      <div className="relative flex items-center gap-4 py-3">
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-zinc-700 to-transparent"></div>
        <span className="text-[11px] uppercase tracking-widest text-zinc-500 font-semibold">or</span>
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-zinc-700 to-transparent"></div>
      </div>

      {/* Email Login - Placeholder */}
      <button
        className="group w-full relative flex items-center justify-center gap-3 px-6 py-4 bg-transparent hover:bg-white/[0.03] text-zinc-300 font-medium rounded-2xl border border-white/10 hover:border-white/20 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
      >
        <svg className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <span className="text-[15px] tracking-wide">Continue with Email</span>
        <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full ml-1 border border-indigo-500/20">Soon</span>
      </button>
    </div>
  )
}

