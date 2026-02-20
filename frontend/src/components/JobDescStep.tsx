import { useState } from 'react'
import { Loader2, Sparkles, Target, Zap, ArrowLeft, Check, Briefcase } from 'lucide-react'
import { generateResume, optimizeATS } from '../services/api'
import toast from 'react-hot-toast'

interface JobDescStepProps {
  resumeData: any
  onGenerationStart: (jobId: string) => void
  onBack: () => void
}

export default function JobDescStep({ resumeData, onGenerationStart, onBack }: JobDescStepProps) {
  const [jobDescription, setJobDescription] = useState('')
  const [mode, setMode] = useState<'tailor' | 'ats'>('tailor')
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerate = async () => {
    if (mode === 'tailor' && !jobDescription.trim()) {
      toast.error('Please enter a job description')
      return
    }

    setIsGenerating(true)

    try {
      if (mode === 'tailor') {
        const response = await generateResume({
          resume_data: resumeData,
          job_description: jobDescription,
          config: {
            generation_mode: 'tailor_with_jd',
            fabrication_enabled: true
          }
        })

        if (response.success) {
          toast.success('Resume generation started!')
          onGenerationStart(response.job_id)
        } else {
          toast.error(response.message || 'Generation failed')
        }
      } else {
        const response = await optimizeATS({
          resume_data: resumeData
        })

        if (response.success) {
          toast.success('Resume optimized for ATS!')
        }
      }
    } catch (error) {
      console.error('Generation error:', error)
      toast.error('Failed to start generation. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 mb-4">
          <Briefcase className="w-7 h-7 text-purple-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Customize Your Resume</h2>
        <p className="text-slate-400 max-w-md mx-auto">
          Choose how you want to optimize your resume
        </p>
      </div>

      {/* Mode Selection Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <button
          onClick={() => setMode('tailor')}
          className={`group relative p-5 rounded-2xl text-left transition-all duration-300 ${
            mode === 'tailor'
              ? 'bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-2 border-indigo-500/50 shadow-lg shadow-indigo-500/10'
              : 'glass glass-hover border border-transparent'
          }`}
        >
          {/* Selected Indicator */}
          {mode === 'tailor' && (
            <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Check className="w-4 h-4 text-white" />
            </div>
          )}
          
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <Target className="w-6 h-6 text-indigo-400" />
          </div>
          <h3 className="font-semibold text-white mb-1">Tailor for Job</h3>
          <p className="text-sm text-slate-400">
            Optimize for a specific job description
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-xs px-2 py-1 rounded-full bg-indigo-500/10 text-indigo-400">Best Match</span>
            <span className="text-xs px-2 py-1 rounded-full bg-purple-500/10 text-purple-400">Keywords</span>
          </div>
        </button>

        <button
          onClick={() => setMode('ats')}
          className={`group relative p-5 rounded-2xl text-left transition-all duration-300 ${
            mode === 'ats'
              ? 'bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-2 border-blue-500/50 shadow-lg shadow-blue-500/10'
              : 'glass glass-hover border border-transparent'
          }`}
        >
          {mode === 'ats' && (
            <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
              <Check className="w-4 h-4 text-white" />
            </div>
          )}
          
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <Zap className="w-6 h-6 text-blue-400" />
          </div>
          <h3 className="font-semibold text-white mb-1">ATS Optimization</h3>
          <p className="text-sm text-slate-400">
            Quick optimization without job description
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-400">Fast</span>
            <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400">STAR Format</span>
          </div>
        </button>
      </div>

      {/* Job Description Input (only for tailor mode) */}
      {mode === 'tailor' && (
        <div className="space-y-3 animate-fade-in">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <Target className="w-4 h-4 text-indigo-400" />
            Job Description
          </label>
          <div className="relative">
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the complete job description here. Include requirements, responsibilities, and qualifications..."
              className="w-full h-48 p-4 rounded-xl input-modern resize-none"
            />
            {/* Character Count */}
            <div className="absolute bottom-3 right-3 text-xs text-slate-600">
              {jobDescription.length} characters
            </div>
          </div>
          <p className="text-xs text-slate-500 flex items-center gap-2">
            <span className="text-indigo-400">💡</span>
            Tip: Include all requirements, skills, and responsibilities for best results
          </p>
        </div>
      )}

      {/* ATS Mode Info */}
      {mode === 'ats' && (
        <div className="glass rounded-xl p-5 space-y-3 animate-fade-in">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-400" />
            ATS-Only Optimization
          </h3>
          <ul className="space-y-2">
            {[
              'Rewrite bullets using STAR format',
              'Add quantification and metrics',
              'Use stronger action verbs',
              'No new experience added',
              'Single pass generation (faster)'
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                <Check className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <button
          onClick={onBack}
          disabled={isGenerating}
          className="flex items-center gap-2 px-5 py-3 rounded-xl glass hover:bg-white/5 text-slate-300 font-medium transition-all duration-300 disabled:opacity-50"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || (mode === 'tailor' && !jobDescription.trim())}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 text-white font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 hover:-translate-y-0.5"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Starting...
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
