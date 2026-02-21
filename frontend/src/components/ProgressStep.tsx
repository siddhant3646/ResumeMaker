import { useEffect } from 'react'
import { CheckCircle, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'

interface ProgressStepProps {
  result: any
  onComplete: () => void
}

export default function ProgressStep({ result, onComplete }: ProgressStepProps) {
  useEffect(() => {
    // result is already stored in localStorage by JobDescStep before navigating here.
    // If for some reason it's not (e.g. direct render), store it now.
    if (result) {
      localStorage.setItem('tailored_resume', JSON.stringify(result))
    }
    toast.success('Resume optimized successfully!', {
      style: { borderRadius: '12px', background: '#059669', color: '#fff' },
    })
    const timer = setTimeout(onComplete, 1800)
    return () => clearTimeout(timer)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="py-10 space-y-10 animate-fade-in max-w-lg mx-auto">
      {/* Completed State */}
      <div className="text-center">
        <div className="animate-scale-in">
          <div className="w-24 h-24 mx-auto mb-6 rounded-[1.5rem] bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-[0_10px_40px_rgba(52,211,153,0.3)]">
            <CheckCircle className="w-12 h-12 text-white drop-shadow-sm" />
          </div>
          <h2 className="text-3xl font-bold text-white tracking-tight mb-2">Resume Ready!</h2>
          <p className="text-zinc-400 font-medium">Redirecting to preview editor...</p>
        </div>
      </div>

      {/* Info Card */}
      <div className="flex items-start gap-4 p-5 rounded-2xl glass-dark border border-emerald-500/10 max-w-md mx-auto animate-fade-in-up delay-200">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center flex-shrink-0 border border-emerald-500/20">
          <Sparkles className="w-5 h-5 text-emerald-400" />
        </div>
        <div>
          <p className="text-[15px] text-zinc-200 font-bold tracking-tight mb-0.5">Optimization Complete</p>
          <p className="text-[13px] text-zinc-400 font-medium leading-relaxed">
            Your resume has been fully optimized for ATS and tailored to the job description.
          </p>
        </div>
      </div>
    </div>
  )
}
