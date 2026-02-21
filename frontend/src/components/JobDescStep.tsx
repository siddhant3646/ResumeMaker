import { useState, useEffect, useRef } from 'react'
import { Loader2, Sparkles, Target, Zap, ArrowLeft, Check, Briefcase, Brain, FileText, BarChart3 } from 'lucide-react'
import { generateResume, retryGeneration, optimizeATS } from '../services/api'
import toast from 'react-hot-toast'

const TARGET_ATS_SCORE = 92
const MAX_RETRIES = 9

const STATUS_MESSAGES = [
  'Analyzing job description keywords…',
  'Matching your experience to requirements…',
  'Enhancing bullet points with metrics…',
  'Optimizing keyword density…',
  'Applying STAR format improvements…',
  'Fine-tuning skills alignment…',
  'Polishing professional summary…',
  'Running ATS compatibility check…',
  'Maximizing relevance score…',
  'Finalizing optimizations…',
]

interface JobDescStepProps {
  resumeData: any
  onGenerationComplete: (result: any) => void
  onAtsComplete: (tailoredResume: any) => void
  onBack: () => void
}

export default function JobDescStep({ resumeData, onGenerationComplete, onAtsComplete, onBack }: JobDescStepProps) {
  const [jobDescription, setJobDescription] = useState('')
  const [mode, setMode] = useState<'tailor' | 'ats'>('tailor')
  const [isGenerating, setIsGenerating] = useState(false)
  const [genStatus, setGenStatus] = useState('')
  const [currentAttempt, setCurrentAttempt] = useState(0)
  const [currentScore, setCurrentScore] = useState(0)
  const [statusMsgIndex, setStatusMsgIndex] = useState(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Cycle status messages every 4 seconds during generation
  useEffect(() => {
    if (isGenerating) {
      intervalRef.current = setInterval(() => {
        setStatusMsgIndex(i => (i + 1) % STATUS_MESSAGES.length)
      }, 4000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
      setStatusMsgIndex(0)
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [isGenerating])

  const handleGenerate = async () => {
    if (mode === 'tailor' && !jobDescription.trim()) {
      toast.error('Please enter a job description')
      return
    }

    setIsGenerating(true)
    setCurrentAttempt(1)
    setCurrentScore(0)

    try {
      if (mode === 'tailor') {
        // --- Initial generation ---
        setGenStatus('Generating resume (attempt 1)…')
        const response = await generateResume({
          resume_data: resumeData,
          job_description: jobDescription,
          config: {
            generation_mode: 'tailor_with_jd',
            fabrication_enabled: true
          }
        })

        if (!response.success || !response.tailored_resume) {
          toast.error(response.message || 'Generation failed')
          return
        }

        let bestResult = response.tailored_resume
        let bestScore = response.ats_score ?? 0
        let jobAnalysis = response.job_analysis
        setCurrentScore(bestScore)

        toast.success(`Attempt 1: ATS Score ${bestScore.toFixed(0)}`, { duration: 3000 })

        // --- Client-driven retry loop ---
        for (let retry = 1; retry <= MAX_RETRIES; retry++) {
          if (bestScore >= TARGET_ATS_SCORE) break

          setCurrentAttempt(retry + 1)
          setGenStatus(`Improving resume (attempt ${retry + 1}, current: ${bestScore.toFixed(0)})…`)
          try {
            const retryResp = await retryGeneration({
              resume_data: resumeData,
              previous_result: bestResult,
              job_analysis: jobAnalysis,
              job_description: jobDescription,
              retry_count: retry,
              config: {
                generation_mode: 'tailor_with_jd',
                fabrication_enabled: true
              }
            })

            if (retryResp.success && retryResp.tailored_resume) {
              const newScore = retryResp.ats_score ?? 0
              toast.success(`Attempt ${retry + 1}: ATS Score ${newScore.toFixed(0)}`, { duration: 3000 })

              if (newScore > bestScore) {
                bestResult = retryResp.tailored_resume
                bestScore = newScore
                jobAnalysis = retryResp.job_analysis
                setCurrentScore(newScore)
              }
            }
          } catch (retryErr) {
            console.error(`Retry ${retry} failed:`, retryErr)
            // Continue with best result so far
            break
          }
        }

        localStorage.setItem('tailored_resume', JSON.stringify(bestResult))
        toast.success(`Resume optimized! Final ATS Score: ${bestScore.toFixed(0)}`)
        onGenerationComplete(bestResult)
      } else {
        setGenStatus('Optimizing for ATS…')
        const response = await optimizeATS({
          resume_data: resumeData
        })

        if (response.success) {
          toast.success('Resume optimized for ATS!')
          onAtsComplete(response.tailored_resume)
        }
      }
    } catch (error) {
      console.error('Generation error:', error)
      toast.error('Failed to generate resume. Please try again.')
    } finally {
      setIsGenerating(false)
      setGenStatus('')
    }
  }

  if (isGenerating) {
    const progressPercent = currentScore > 0 ? Math.min((currentScore / TARGET_ATS_SCORE) * 100, 100) : 0
    const circumference = 2 * Math.PI * 54 // radius = 54
    const strokeOffset = circumference - (progressPercent / 100) * circumference

    return (
      <div className="py-16 px-8 space-y-10 animate-fade-in">
        {/* Animated Progress Ring */}
        <div className="flex flex-col items-center">
          <div className="relative w-36 h-36 mb-6">
            {/* Background ring */}
            <svg className="w-36 h-36 -rotate-90" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle
                cx="60" cy="60" r="54" fill="none"
                stroke="url(#gradient)" strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeOffset}
                className="transition-all duration-1000 ease-out"
              />
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#818cf8" />
                  <stop offset="100%" stopColor="#c084fc" />
                </linearGradient>
              </defs>
            </svg>
            {/* Score inside ring */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              {currentScore > 0 ? (
                <>
                  <span className="text-3xl font-black text-white tabular-nums">{currentScore.toFixed(0)}</span>
                  <span className="text-xs font-semibold text-zinc-400 tracking-wider">ATS SCORE</span>
                </>
              ) : (
                <div className="w-8 h-8 border-3 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            {/* Pulse glow */}
            <div className="absolute inset-0 rounded-full bg-indigo-500/10 animate-ping opacity-20" />
          </div>

          {/* Attempt badge */}
          <div className="badge badge-glow mb-4 inline-flex">
            <Brain className="w-3.5 h-3.5 mr-2 text-indigo-300" />
            <span>Attempt {currentAttempt} of {MAX_RETRIES + 1}</span>
          </div>

          {/* Cycling status message */}
          <p className="text-zinc-300 text-[15px] font-medium text-center transition-opacity duration-500" key={statusMsgIndex}>
            {STATUS_MESSAGES[statusMsgIndex]}
          </p>
        </div>

        {/* Animated step indicators */}
        <div className="grid grid-cols-3 gap-4 max-w-sm mx-auto">
          {[
            { icon: FileText, label: 'Analyzing', done: currentScore > 0 },
            { icon: BarChart3, label: 'Scoring', done: currentScore >= 80 },
            { icon: Target, label: 'Targeting 92+', done: currentScore >= TARGET_ATS_SCORE },
          ].map((step, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <div className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all duration-500 ${step.done
                  ? 'bg-gradient-to-br from-emerald-400/20 to-teal-500/20 border border-emerald-500/30 shadow-[0_4px_15px_rgba(52,211,153,0.2)]'
                  : 'glass border border-white/5'
                }`}>
                {step.done ? (
                  <Check className="w-5 h-5 text-emerald-400" />
                ) : (
                  <step.icon className="w-5 h-5 text-zinc-500" />
                )}
              </div>
              <span className={`text-xs font-semibold transition-colors ${step.done ? 'text-emerald-400' : 'text-zinc-500'}`}>
                {step.label}
              </span>
            </div>
          ))}
        </div>

        {/* Info footer */}
        <p className="text-center text-sm text-zinc-500 font-medium">
          This may take 1–3 minutes. Each attempt improves keyword match and ATS compatibility.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-[1.25rem] bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 mb-5 shadow-inner">
          <Briefcase className="w-8 h-8 text-purple-400" />
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight mb-2">Customize Your Resume</h2>
        <p className="text-zinc-400 font-medium max-w-md mx-auto">
          Intelligently choose how you want to radically optimize your resume.
        </p>
      </div>

      {/* Mode Selection Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <button
          onClick={() => setMode('tailor')}
          className={`group relative p-6 rounded-3xl text-left transition-all duration-300 ${mode === 'tailor'
            ? 'glass-dark border-[1.5px] border-indigo-500/50 shadow-[0_8px_30px_rgba(99,102,241,0.2)] scale-[1.02]'
            : 'glass-dark border border-white/5 hover:border-white/10 hover:bg-white/[0.04]'
            }`}
        >
          {/* Selected Indicator */}
          {mode === 'tailor' && (
            <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg animate-scale-in">
              <Check className="w-4 h-4 text-white" />
            </div>
          )}

          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-inner">
            <Target className="w-7 h-7 text-indigo-400" />
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight mb-1.5">Tailor for Job</h3>
          <p className="text-[15px] font-medium text-zinc-400 leading-relaxed mb-4">
            Optimize deeply for a specific job description.
          </p>
          <div className="flex flex-wrap gap-2.5">
            <span className="text-[11px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">Best Match</span>
            <span className="text-[11px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-400">Keywords</span>
          </div>
        </button>

        <button
          onClick={() => setMode('ats')}
          className={`group relative p-6 rounded-3xl text-left transition-all duration-300 ${mode === 'ats'
            ? 'glass-dark border-[1.5px] border-blue-500/50 shadow-[0_8px_30px_rgba(59,130,246,0.2)] scale-[1.02]'
            : 'glass-dark border border-white/5 hover:border-white/10 hover:bg-white/[0.04]'
            }`}
        >
          {mode === 'ats' && (
            <div className="absolute top-4 right-4 w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg animate-scale-in">
              <Check className="w-4 h-4 text-white" />
            </div>
          )}

          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-inner">
            <Zap className="w-7 h-7 text-blue-400" />
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight mb-1.5">ATS Optimization</h3>
          <p className="text-[15px] font-medium text-zinc-400 leading-relaxed mb-4">
            Quick optimization without a job description.
          </p>
          <div className="flex flex-wrap gap-2.5">
            <span className="text-[11px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400">Fast</span>
            <span className="text-[11px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">STAR Format</span>
          </div>
        </button>
      </div>

      {/* Job Description Input (only for tailor mode) */}
      {mode === 'tailor' && (
        <div className="space-y-4 animate-fade-in mt-2">
          <label className="flex items-center gap-2.5 text-[15px] font-semibold text-zinc-300 tracking-wide">
            <Target className="w-5 h-5 text-indigo-400" />
            Job Description
          </label>
          <div className="relative">
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the complete job description here. Include requirements, responsibilities, and qualifications..."
              className="w-full h-56 p-5 rounded-2xl input-modern resize-none text-[15px] leading-relaxed shadow-inner"
            />
            {/* Character Count */}
            <div className="absolute bottom-4 right-4 text-xs font-semibold text-zinc-500 bg-black/40 px-2 py-1 rounded-md backdrop-blur-md">
              {jobDescription.length} characters
            </div>
          </div>
          <p className="text-sm font-medium text-zinc-400 flex items-center gap-2.5 bg-indigo-500/5 border border-indigo-500/10 px-4 py-3 rounded-xl backdrop-blur-sm">
            <span className="text-indigo-400 text-lg">💡</span>
            Tip: Include all requirements, skills, and responsibilities for best results
          </p>
        </div>
      )}

      {/* ATS Mode Info */}
      {mode === 'ats' && (
        <div className="glass-dark rounded-3xl p-6 sm:p-8 space-y-4 animate-fade-in border border-blue-500/20 mt-2">
          <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-3">
            <Zap className="w-6 h-6 text-blue-400 p-1 bg-blue-500/10 rounded-lg" />
            ATS-Only Optimization
          </h3>
          <ul className="space-y-3.5">
            {[
              'Rewrite bullets using strict STAR format',
              'Add impressive quantification and metrics',
              'Use significantly stronger action verbs',
              'No fabricated experience added',
              'Single pass lightning-fast generation'
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-3.5 text-[15px] font-medium text-zinc-300">
                <Check className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0 drop-shadow-sm" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-6">
        <button
          onClick={onBack}
          disabled={isGenerating}
          className="flex items-center justify-center sm:justify-start gap-2.5 px-6 py-3.5 rounded-2xl glass-dark hover:bg-white/5 border border-white/10 text-zinc-300 font-semibold transition-all duration-300 disabled:opacity-50 hover:border-white/20 active:scale-[0.98]"
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || (mode === 'tailor' && !jobDescription.trim())}
          className="flex-1 btn-primary py-3.5 text-[16px]"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              {genStatus || 'Optimizing Resume...'}
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              {mode === 'tailor' ? 'Tailor Resume' : 'Optimize for ATS'}
            </>
          )}
        </button>
      </div>
    </div>
  )
}

