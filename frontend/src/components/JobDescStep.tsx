import { useState } from 'react'
import { FileText, Loader2, Sparkles } from 'lucide-react'
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
        // ATS-only mode
        const response = await optimizeATS({
          resume_data: resumeData
        })

        if (response.success) {
          toast.success('Resume optimized for ATS!')
          // In ATS mode, we get result immediately (no job queue)
          // Handle completion differently
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
      {/* Mode Selection */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setMode('tailor')}
          className={`flex-1 p-4 rounded-xl border-2 transition-all ${
            mode === 'tailor'
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-slate-700 hover:border-slate-600'
          }`}
        >
          <div className="text-2xl mb-2">🎯</div>
          <h3 className="font-semibold text-white">Tailor for Specific Job</h3>
          <p className="text-sm text-slate-400 mt-1">
            Optimize for a specific job description
          </p>
        </button>

        <button
          onClick={() => setMode('ats')}
          className={`flex-1 p-4 rounded-xl border-2 transition-all ${
            mode === 'ats'
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-slate-700 hover:border-slate-600'
          }`}
        >
          <div className="text-2xl mb-2">⚡</div>
          <h3 className="font-semibold text-white">ATS Optimization Only</h3>
          <p className="text-sm text-slate-400 mt-1">
            Improve existing content for ATS
          </p>
        </button>
      </div>

      {/* Job Description Input (only for tailor mode) */}
      {mode === 'tailor' && (
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Job Description
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the complete job description here..."
            className="w-full h-48 p-4 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
          />
          <p className="text-xs text-slate-500 mt-2">
            Include all requirements, responsibilities, and qualifications
          </p>
        </div>
      )}

      {/* ATS Mode Description */}
      {mode === 'ats' && (
        <div className="p-4 bg-slate-800/50 rounded-xl">
          <h3 className="font-semibold text-white mb-2">⚡ ATS-Only Optimization Mode</h3>
          <ul className="space-y-2 text-sm text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              Rewrite existing bullets using STAR format
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              Add quantification and metrics
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              Use stronger action verbs
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <strong>No new experience added</strong> - only improves existing content
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              Single pass generation (faster)
            </li>
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4 pt-4">
        <button
          onClick={onBack}
          disabled={isGenerating}
          className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition-colors disabled:opacity-50"
        >
          ← Back
        </button>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || (mode === 'tailor' && !jobDescription.trim())}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Sparkles className="h-5 w-5" />
              {mode === 'tailor' ? 'Tailor Resume' : 'Optimize for ATS'}
            </>
          )}
        </button>
      </div>
    </div>
  )
}
