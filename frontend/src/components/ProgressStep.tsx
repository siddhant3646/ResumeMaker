import { useEffect, useState, useRef } from 'react'
import { Loader2, CheckCircle, AlertCircle, Sparkles, FileText, Zap } from 'lucide-react'
import { getGenerationStatus, createWebSocket } from '../services/api'
import toast from 'react-hot-toast'

interface ProgressStepProps {
  jobId: string
  onComplete: () => void
}

const steps = [
  { id: 1, label: 'Analyzing Context', icon: FileText },
  { id: 2, label: 'Optimizing Value', icon: Sparkles },
  { id: 3, label: 'Finalizing Output', icon: Zap },
]

export default function ProgressStep({ jobId, onComplete }: ProgressStepProps) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('pending')
  const [message, setMessage] = useState('Initializing optimization sequence...')
  const [streamText, setStreamText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    try {
      const ws = createWebSocket(jobId)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setProgress(data.progress)
        setStatus(data.status)
        setMessage(data.message)
        if (data.stream_text) {
          setStreamText(data.stream_text)
        }

        if (data.status === 'completed') {
          if (data.result) {
            localStorage.setItem('tailored_resume', JSON.stringify(data.result))
          }
          toast.success('Resume optimized successfully!', { style: { borderRadius: '12px', background: '#059669', color: '#fff' } })
          setTimeout(onComplete, 1800)
        } else if (data.status === 'failed') {
          setError(data.error || 'Generation failed')
          toast.error(data.error || 'Optimization process failed')
        }
      }

      ws.onerror = () => {
        startPolling()
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
      }
    } catch {
      startPolling()
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [jobId, onComplete])

  const startPolling = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const data = await getGenerationStatus(jobId)
        setProgress(data.progress)
        setStatus(data.status)
        setMessage(data.message)

        if (data.status === 'completed') {
          clearInterval(pollInterval)
          if (data.result) {
            localStorage.setItem('tailored_resume', JSON.stringify(data.result))
          }
          toast.success('Resume optimized successfully!', { style: { borderRadius: '12px', background: '#059669', color: '#fff' } })
          setTimeout(onComplete, 1800)
        } else if (data.status === 'failed') {
          clearInterval(pollInterval)
          setError(data.error || 'Generation failed')
          toast.error(data.error || 'Optimization process failed')
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000)
  }

  const currentStepIndex = Math.min(Math.floor(progress / 33.33), 2)

  return (
    <div className="py-10 space-y-10 animate-fade-in max-w-lg mx-auto">
      {/* Status Header */}
      <div className="text-center">
        {status === 'completed' ? (
          <div className="animate-scale-in">
            <div className="w-24 h-24 mx-auto mb-6 rounded-[1.5rem] bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-[0_10px_40px_rgba(52,211,153,0.3)]">
              <CheckCircle className="w-12 h-12 text-white drop-shadow-sm" />
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight mb-2">Resume Ready!</h2>
            <p className="text-zinc-400 font-medium">Redirecting to preview editor...</p>
          </div>
        ) : status === 'failed' ? (
          <div className="animate-scale-in">
            <div className="w-24 h-24 mx-auto mb-6 rounded-[1.5rem] bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center shadow-[0_10px_40px_rgba(239,68,68,0.3)]">
              <AlertCircle className="w-12 h-12 text-white drop-shadow-sm" />
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight mb-2">Generation Failed</h2>
            <p className="text-red-400 font-medium max-w-sm mx-auto">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-8 btn-primary px-8"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="animate-fade-in flex flex-col items-center">
            {/* Premium Apple-inspired Radar Animation */}
            <div className="relative w-32 h-32 mb-10 mt-4 flex items-center justify-center">
              {/* Outer pulsing rings */}
              <div className="absolute inset-0 rounded-full border border-indigo-500/20 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite]"></div>
              <div className="absolute inset-2 rounded-full border border-purple-500/30 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite] animation-delay-700"></div>
              <div className="absolute inset-6 rounded-full border border-pink-500/40 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite] animation-delay-1000"></div>

              {/* Spinning radar sweep */}
              <div className="absolute inset-0 rounded-full overflow-hidden mask-radial-gradient">
                <div className="absolute inset-0 bg-[conic-gradient(from_0deg,transparent_0deg,transparent_270deg,rgba(99,102,241,0.4)_360deg)] animate-[spin_2s_linear_infinite]"></div>
              </div>

              {/* Central glowing core */}
              <div className="relative w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-[0_0_30px_rgba(99,102,241,0.6)]">
                <Sparkles className="w-5 h-5 text-white animate-pulse" />
                <div className="absolute inset-0 rounded-full bg-white/20 animate-ping"></div>
              </div>
            </div>

            <h2 className="text-3xl font-bold text-white tracking-tight mb-3">Optimizing Your Resume</h2>
            <p className="text-zinc-400 font-medium h-6 text-[15px]">{message}</p>
          </div>
        )}
      </div>

      {/* Progress Steps */}
      {status !== 'completed' && status !== 'failed' && (
        <div className="space-y-6">
          <div className="flex items-center justify-center -mx-4 relative z-10">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = index === currentStepIndex
              const isCompleted = index < currentStepIndex

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-700 ease-out ${isCompleted
                        ? 'bg-gradient-to-br from-emerald-400 to-teal-500 shadow-[0_5px_20px_rgba(52,211,153,0.3)] scale-100'
                        : isActive
                          ? 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-[0_5px_20px_rgba(99,102,241,0.4)] scale-110 mb-1'
                          : 'glass-dark'
                        }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-6 h-6 text-white" />
                      ) : (
                        <Icon className={`w-6 h-6 transition-colors duration-500 ${isActive ? 'text-white' : 'text-zinc-600'}`} />
                      )}
                    </div>
                    {/* Make label absolute to prevent layout shifts from scale */}
                    <span className={`absolute mt-16 text-[11px] font-bold uppercase tracking-wider transition-colors duration-500 ${isActive ? 'text-white' : isCompleted ? 'text-zinc-300' : 'text-zinc-600'}`}>
                      {step.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className="w-12 sm:w-16 md:w-20 h-[3px] mx-3 sm:mx-4 bg-zinc-800/80 overflow-hidden rounded-full mt-[-10px]">
                      <div
                        className={`h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-1000 ease-in-out ${isCompleted ? 'w-full' : 'w-0'
                          }`}
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {status !== 'completed' && status !== 'failed' && (
        <div className="w-full space-y-4 pt-12">
          <div className="relative h-2.5 bg-zinc-800/80 rounded-full overflow-hidden border border-white/5 shadow-inner">
            {/* Gradient Progress */}
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${progress}%` }}
            />
            {/* Shimmer Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          </div>

          {/* Progress Text */}
          <div className="flex items-center justify-between text-sm px-1 overflow-hidden">
            <span className="text-zinc-400 font-medium font-mono text-xs truncate max-w-[250px] opacity-70">
              {streamText || "Supercharging text..."}
            </span>
            <span className="text-white font-bold tracking-wider flex-shrink-0">{Math.round(progress)}%</span>
          </div>
        </div>
      )}

      {/* Info Card */}
      {status !== 'completed' && status !== 'failed' && (
        <div className="flex items-start gap-4 p-5 rounded-2xl glass-dark border border-indigo-500/10 max-w-md mx-auto mt-8 animate-fade-in-up delay-200">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0 border border-indigo-500/20">
            <Sparkles className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <p className="text-[15px] text-zinc-200 font-bold tracking-tight mb-0.5">AI Engine Working</p>
            <p className="text-[13px] text-zinc-400 font-medium leading-relaxed">
              Our deeply trained AI models are fundamentally analyzing your resume and optimizing it for strict ATS requirements.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

