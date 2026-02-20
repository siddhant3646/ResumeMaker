import { useEffect, useState, useRef } from 'react'
import { Loader2, CheckCircle, AlertCircle, Sparkles, FileText, Zap } from 'lucide-react'
import { getGenerationStatus, createWebSocket } from '../services/api'
import toast from 'react-hot-toast'

interface ProgressStepProps {
  jobId: string
  onComplete: () => void
}

const steps = [
  { id: 1, label: 'Analyzing', icon: FileText },
  { id: 2, label: 'Optimizing', icon: Sparkles },
  { id: 3, label: 'Finalizing', icon: Zap },
]

export default function ProgressStep({ jobId, onComplete }: ProgressStepProps) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('pending')
  const [message, setMessage] = useState('Initializing...')
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

        if (data.status === 'completed') {
          toast.success('Resume generated successfully!')
          setTimeout(onComplete, 1500)
        } else if (data.status === 'failed') {
          setError(data.error || 'Generation failed')
          toast.error(data.error || 'Generation failed')
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
          toast.success('Resume generated successfully!')
          setTimeout(onComplete, 1500)
        } else if (data.status === 'failed') {
          clearInterval(pollInterval)
          setError(data.error || 'Generation failed')
          toast.error(data.error || 'Generation failed')
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000)
  }

  const currentStepIndex = Math.min(Math.floor(progress / 33.33), 2)

  return (
    <div className="py-6 space-y-8">
      {/* Status Header */}
      <div className="text-center">
        {status === 'completed' ? (
          <div className="animate-scale-in">
            <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-green-500/30">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Resume Ready!</h2>
            <p className="text-slate-400">Redirecting to editor...</p>
          </div>
        ) : status === 'failed' ? (
          <div className="animate-scale-in">
            <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center shadow-lg shadow-red-500/30">
              <AlertCircle className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Generation Failed</h2>
            <p className="text-red-400">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 btn-primary text-white"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="animate-fade-in">
            <div className="relative w-20 h-20 mx-auto mb-4">
              {/* Spinning Background */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 animate-spin-slow opacity-50"></div>
              {/* Inner Container */}
              <div className="absolute inset-1 rounded-xl bg-slate-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Optimizing Your Resume</h2>
            <p className="text-slate-400">{message}</p>
          </div>
        )}
      </div>

      {/* Progress Steps */}
      {status !== 'completed' && status !== 'failed' && (
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-2">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = index === currentStepIndex
              const isCompleted = index < currentStepIndex

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-500 ${
                        isCompleted
                          ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-500/25'
                          : isActive
                          ? 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25 animate-pulse'
                          : 'glass'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-5 h-5 text-white" />
                      ) : (
                        <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                      )}
                    </div>
                    <span className={`text-xs mt-2 ${isActive ? 'text-white' : 'text-slate-500'}`}>
                      {step.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className="w-12 h-0.5 mx-2 bg-slate-800 overflow-hidden rounded-full">
                      <div
                        className={`h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500 ${
                          isCompleted ? 'w-full' : 'w-0'
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
        <div className="max-w-md mx-auto space-y-3">
          <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
            {/* Gradient Progress */}
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
            {/* Shimmer Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
          </div>
          
          {/* Progress Text */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Processing...</span>
            <span className="text-white font-medium">{Math.round(progress)}%</span>
          </div>
        </div>
      )}

      {/* Info Card */}
      {status !== 'completed' && status !== 'failed' && (
        <div className="flex items-start gap-3 p-4 rounded-xl glass max-w-md mx-auto">
          <Sparkles className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-slate-300 font-medium">AI at Work</p>
            <p className="text-xs text-slate-500">
              Our AI is analyzing your resume and optimizing it for maximum impact
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
