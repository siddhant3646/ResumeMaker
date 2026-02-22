import { useState, useEffect, useRef } from 'react'
import { Loader2, Sparkles, Target, Zap, ArrowLeft, Check, Briefcase, Brain, FileText, BarChart3 } from 'lucide-react'
import { generateResume, optimizeATS, regenerateResume } from '../services/api'
import toast from 'react-hot-toast'

const TARGET_ATS_SCORE = 80
const MAX_PASSES = 5

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

    try {
      if (mode === 'tailor') {
        // Pass 1: initial generation
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

        let bestResume = response.tailored_resume
        let bestScore = response.ats_score ?? 0

        // Passes 2-5: improve until ATS >= TARGET_ATS_SCORE
        for (let attempt = 2; attempt <= MAX_PASSES && bestScore < TARGET_ATS_SCORE; attempt++) {
          try {
            const improved = await regenerateResume({
              resume_data: bestResume,
              job_description: jobDescription,
              attempt
            })

            if (improved.success && improved.tailored_resume) {
              const newScore = improved.ats_score ?? 0
              if (newScore > bestScore) {
                bestResume = improved.tailored_resume
                bestScore = newScore
              }
            }
          } catch (err) {
            console.warn(`Regeneration attempt ${attempt} failed, using best so far`)
            break
          }
        }

        localStorage.setItem('tailored_resume', JSON.stringify(bestResume))
        toast.success(`Resume optimized! ATS Score: ${bestScore.toFixed(0)}`)
        onGenerationComplete(bestResume)
      } else {
        const response = await optimizeATS({
          resume_data: resumeData
        })

        if (response.success) {
          toast.success('Resume optimized for ATS!')
          onAtsComplete(response.tailored_resume)
        }
      }
    } catch (error: any) {
      console.error('Generation error:', error)
      toast.error(error.message || 'Failed to generate resume. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  if (isGenerating) {
    const circumference = 2 * Math.PI * 54

    return (
      <div className="py-16 px-8 space-y-10 animate-fade-in">
        {/* Animated Progress Ring */}
        <div className="flex flex-col items-center">
          <div className="relative w-36 h-36 mb-6">
            <svg className="w-36 h-36 -rotate-90 animate-spin" style={{ animationDuration: '3s' }} viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle
                cx="60" cy="60" r="54" fill="none"
                stroke="url(#gradient)" strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={circumference * 0.7}
                className="transition-all duration-1000 ease-out"
              />
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#818cf8" />
                  <stop offset="100%" stopColor="#c084fc" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <Brain className="w-8 h-8 text-indigo-400 animate-pulse" />
            </div>
            {/* Pulse glow */}
            <div className="absolute inset-0 rounded-full bg-indigo-500/10 animate-ping opacity-20" />
          </div>

          {/* Badge */}
          <div className="badge badge-glow mb-4 inline-flex">
            <Sparkles className="w-3.5 h-3.5 mr-2 text-indigo-300" />
            <span>AI Optimizing — Target: {TARGET_ATS_SCORE}+</span>
          </div>

          {/* Cycling status message */}
          <p className="text-zinc-300 text-[15px] font-medium text-center transition-opacity duration-500" key={statusMsgIndex}>
            {STATUS_MESSAGES[statusMsgIndex]}
          </p>
        </div>

        {/* Animated step indicators */}
        <div className="grid grid-cols-3 gap-4 max-w-sm mx-auto">
          {[
            { icon: FileText, label: 'Analyzing' },
            { icon: BarChart3, label: 'Scoring' },
            { icon: Target, label: `Targeting ${TARGET_ATS_SCORE}+` },
          ].map((step, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <div className="w-11 h-11 rounded-2xl flex items-center justify-center glass border border-white/5">
                <step.icon className="w-5 h-5 text-zinc-400 animate-pulse" style={{ animationDelay: `${i * 0.5}s` }} />
              </div>
              <span className="text-xs font-semibold text-zinc-500">{step.label}</span>
            </div>
          ))}
        </div>

        {/* Info footer */}
        <p className="text-center text-sm text-zinc-500 font-medium">
          This may take 2–5 minutes. The AI is iteratively improving your resume to reach ATS {TARGET_ATS_SCORE}+.
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
              Optimizing Resume...
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

