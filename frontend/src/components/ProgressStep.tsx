import { useEffect, useState, useRef } from 'react'
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { getGenerationStatus, createWebSocket } from '../services/api'
import toast from 'react-hot-toast'

interface ProgressStepProps {
  jobId: string
  onComplete: () => void
}

export default function ProgressStep({ jobId, onComplete }: ProgressStepProps) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('pending')
  const [message, setMessage] = useState('Initializing...')
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Try WebSocket first
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

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        // Fall back to polling
        startPolling()
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
      }
    } catch (error) {
      // Fall back to polling if WebSocket fails
      startPolling()
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [jobId, onComplete])

  const startPolling = async () => {
    // Poll every 2 seconds
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

  const getStatusIcon = () => {
    if (status === 'completed') {
      return <CheckCircle className="h-16 w-16 text-green-500" />
    } else if (status === 'failed') {
      return <AlertCircle className="h-16 w-16 text-red-500" />
    } else {
      return <Loader2 className="h-16 w-16 text-blue-500 animate-spin" />
    }
  }

  return (
    <div className="text-center py-8">
      <div className="flex justify-center mb-6">
        {getStatusIcon()}
      </div>

      <h2 className="text-2xl font-bold text-white mb-2">
        {status === 'completed' 
          ? 'Resume Ready!' 
          : status === 'failed'
          ? 'Generation Failed'
          : 'Optimizing Your Resume'
        }
      </h2>

      {error ? (
        <p className="text-red-400 mb-4">{error}</p>
      ) : (
        <p className="text-slate-400 mb-8">{message}</p>
      )}

      {/* Progress Bar */}
      {!error && (
        <div className="max-w-md mx-auto">
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-4">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-slate-500">{Math.round(progress)}%</p>
        </div>
      )}

      {/* Retry button on error */}
      {error && (
        <button
          onClick={() => window.location.reload()}
          className="mt-6 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  )
}
