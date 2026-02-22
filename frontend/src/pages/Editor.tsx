import { useState, useEffect } from 'react'
import { Download, ArrowLeft, Edit3, Sparkles, CheckCircle, Target, BarChart3, ShieldCheck, RotateCcw, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { downloadResumePDF, checkATSScore } from '../services/api'
import toast from 'react-hot-toast'
import EditModal from '../components/EditModal'

export default function Editor() {
  const navigate = useNavigate()
  const [isDownloading, setIsDownloading] = useState(false)
  const [tailoredResume, setTailoredResume] = useState<any>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isCheckingScore, setIsCheckingScore] = useState(false)
  const [liveAtsScore, setLiveAtsScore] = useState<any>(null)

  useEffect(() => {
    const saved = localStorage.getItem('tailored_resume')
    if (saved) {
      try {
        setTailoredResume(JSON.parse(saved))
      } catch (e) {
        toast.error('Failed to load resume data')
        navigate('/')
      }
    } else {
      navigate('/')
    }
  }, [navigate])

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const blob = await downloadResumePDF(tailoredResume)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'tailored_resume.pdf'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      toast.success('Resume downloaded!')
    } catch (error: any) {
      console.error('Download error:', error)
      const message = error?.response?.data?.error || error?.message || 'Failed to download resume'
      toast.error(message)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleSaveEdit = (updatedResume: any) => {
    setTailoredResume(updatedResume)
    localStorage.setItem('tailored_resume', JSON.stringify(updatedResume))
  }

  const handleCheckAts = async () => {
    setIsCheckingScore(true)
    try {
      const result = await checkATSScore(tailoredResume)
      if (result.success) {
        setLiveAtsScore(result.ats_score)
        toast.success('ATS Score updated!')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to check ATS score')
    } finally {
      setIsCheckingScore(false)
    }
  }

  const handleStartOver = () => {
    localStorage.removeItem('tailored_resume')
    localStorage.removeItem('parsed_resume')
    navigate('/')
  }

  if (!tailoredResume) return null;

  const atsScore = liveAtsScore || tailoredResume.ats_score

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-12">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2.5 text-zinc-400 hover:text-white transition-colors group px-2 py-1"
        >
          <div className="w-9 h-9 rounded-xl glass-dark flex items-center justify-center group-hover:bg-white/10 transition-colors shadow-sm">
            <ArrowLeft className="h-4 w-4" />
          </div>
          <span className="font-medium tracking-wide text-[15px]">Back to Home</span>
        </button>

        <div className="flex flex-wrap gap-3 w-full sm:w-auto">
          <button
            onClick={handleStartOver}
            className="flex-1 sm:flex-none btn-secondary gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Start Over</span>
          </button>

          <button
            onClick={() => setIsEditModalOpen(true)}
            className="flex-1 sm:flex-none btn-secondary gap-2"
          >
            <Edit3 className="h-4 w-4" />
            <span>Edit</span>
          </button>

          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="flex-1 sm:flex-none btn-primary gap-2"
          >
            <Download className="h-4 w-4" />
            <span>{isDownloading ? 'Downloading...' : 'Download PDF'}</span>
          </button>
        </div>
      </div>

      {/* ATS Score Card */}
      <div className="card-modern gradient-border bg-black/40">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8 mb-8">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="absolute inset-0 bg-emerald-500 rounded-2xl blur opacity-30"></div>
              <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-lg">
                <CheckCircle className="w-8 h-8 text-white drop-shadow-sm" />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight mb-1">Your Resume is Ready!</h2>
              <p className="text-zinc-400 text-sm font-medium">Optimized for strict FAANG/MAANG ATS systems</p>
            </div>
          </div>

          <div className="flex items-center gap-6 glass px-6 py-4 rounded-2xl">
            <div className="text-right">
              <div className="text-sm font-semibold text-zinc-400 tracking-wide uppercase mb-1">ATS Score</div>
              <div className="text-[13px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-md inline-block">
                {atsScore?.overall >= 90 ? 'Excellent' : atsScore?.overall >= 80 ? 'Good' : 'Needs Work'}
              </div>
            </div>
            {/* Circular Progress */}
            <div className="relative w-20 h-20 drop-shadow-lg">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="6"
                  fill="transparent"
                  className="text-white/5"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="url(#gradient)"
                  strokeWidth="6"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 36 * ((atsScore?.overall || 0) / 100)} ${2 * Math.PI * 36}`}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#34d399" />
                    <stop offset="100%" stopColor="#10b981" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-[28px] font-black text-white">{atsScore?.overall || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Score Breakdown (Bento style minimal) */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="glass-dark rounded-2xl p-5 hover:bg-white/[0.04] transition-colors flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Target className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-0.5">Keywords</div>
              <div className="text-xl font-bold text-emerald-400">{atsScore?.keyword_match || 0}%</div>
            </div>
          </div>
          <div className="glass-dark rounded-2xl p-5 hover:bg-white/[0.04] transition-colors flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
              <BarChart3 className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-0.5">STAR Format</div>
              <div className="text-xl font-bold text-blue-400">{atsScore?.star_compliance || 0}%</div>
            </div>
          </div>
          <div className="glass-dark rounded-2xl p-5 hover:bg-white/[0.04] transition-colors flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
              <ShieldCheck className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-0.5">Quantification</div>
              <div className="text-xl font-bold text-purple-400">{atsScore?.quantification || 0}%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Fabrication Notes */}
      {tailoredResume.fabrication_notes?.length > 0 && (
        <div className="glass-dark rounded-2xl p-5 border border-amber-500/20">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <h3 className="text-lg font-semibold text-white">Content Enhancement Details</h3>
          </div>
          <ul className="space-y-2">
            {tailoredResume.fabrication_notes.map((note: string, idx: number) => (
              <li key={idx} className="text-sm text-zinc-400 flex items-start gap-2">
                <span className="text-amber-400">•</span>
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Resume Preview */}
      <div className="bg-white rounded-[2rem] p-10 sm:p-14 text-zinc-900 shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/10 relative overflow-hidden">
        {/* Decorative inner border */}
        <div className="absolute inset-4 border border-zinc-100 rounded-3xl pointer-events-none"></div>

        <div className="text-center mb-8 pb-6 border-b border-zinc-200">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-zinc-900 tracking-tight mb-2">{tailoredResume.basics.name}</h1>
          <p className="text-zinc-500 font-medium">
            {tailoredResume.basics.email} <span className="mx-2 text-zinc-300">•</span> {tailoredResume.basics.phone}
          </p>
        </div>

        {tailoredResume.summary && (
          <div className="mb-8 pl-2">
            <h2 className="text-sm font-bold text-indigo-600 uppercase tracking-widest mb-3">
              Professional Summary
            </h2>
            <p className="text-zinc-700 text-[15px] leading-relaxed font-medium">{tailoredResume.summary}</p>
          </div>
        )}

        <div className="pl-2">
          <h2 className="text-sm font-bold text-indigo-600 uppercase tracking-widest mb-5">
            Professional Experience
          </h2>
          {tailoredResume.experience.map((exp: any, idx: number) => (
            <div key={idx} className="mb-6 last:mb-0">
              <div className="flex flex-col sm:flex-row justify-between sm:items-baseline mb-3">
                <h3 className="text-lg font-bold text-zinc-900">{exp.role}</h3>
                <span className="text-sm text-zinc-500 font-semibold">{exp.company}</span>
              </div>
              <ul className="space-y-2.5">
                {exp.bullets.map((bullet: string, bidx: number) => (
                  <li key={bidx} className="flex items-start gap-3 text-zinc-700 text-[15px] font-medium leading-relaxed">
                    <span className="text-indigo-400 mt-1.5 text-xs">●</span>
                    <span className="flex-1">{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Re-check ATS Score - only show if score is below target */}
      {atsScore?.overall < 90 && (
        <div className="flex flex-col items-center justify-center gap-2 pt-6">
          <button
            onClick={handleCheckAts}
            disabled={isCheckingScore}
            className="group flex items-center gap-3 px-6 py-3 rounded-full glass-dark border border-amber-500/20 hover:bg-amber-500/10 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
          >
            {isCheckingScore ? (
              <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 text-amber-400 group-hover:text-amber-300 transition-colors" />
            )}
            <span className="font-medium text-amber-200 text-sm">
              {isCheckingScore ? 'Analyzing...' : 'Re-analyze ATS Score'}
            </span>
          </button>
          <p className="text-zinc-500 text-xs">Score below 90 - re-analyze after making edits</p>
        </div>
      )}

      {/* Edit Modal */}
      <EditModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        resume={tailoredResume}
        onSave={handleSaveEdit}
      />
    </div>
  )
}
