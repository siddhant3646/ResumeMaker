import { useState, useEffect } from 'react'
import { Download, ArrowLeft, Edit3, Sparkles, CheckCircle, Target, BarChart3, ShieldCheck } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { downloadResumePDF } from '../services/api'
import toast from 'react-hot-toast'

export default function Editor() {
  const navigate = useNavigate()
  const [isDownloading, setIsDownloading] = useState(false)
  const [tailoredResume, setTailoredResume] = useState<any>(null)

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
    } catch {
      toast.error('Failed to download resume')
    } finally {
      setIsDownloading(false)
    }
  }

  if (!tailoredResume) return null;

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
            onClick={() => toast('Edit feature coming soon!', { icon: '✨', style: { borderRadius: '12px', background: '#18181b', color: '#fff' } })}
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
              <div className="text-[13px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-md inline-block">Excellent</div>
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
                  strokeDasharray={`${2 * Math.PI * 36 * (tailoredResume.ats_score.overall / 100)} ${2 * Math.PI * 36}`}
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
                <span className="text-[28px] font-black text-white">{tailoredResume.ats_score.overall}</span>
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
              <div className="text-xl font-bold text-emerald-400">{tailoredResume.ats_score.keyword_match}%</div>
            </div>
          </div>
          <div className="glass-dark rounded-2xl p-5 hover:bg-white/[0.04] transition-colors flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
              <BarChart3 className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-0.5">STAR Format</div>
              <div className="text-xl font-bold text-blue-400">{tailoredResume.ats_score.star_compliance}%</div>
            </div>
          </div>
          <div className="glass-dark rounded-2xl p-5 hover:bg-white/[0.04] transition-colors flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
              <ShieldCheck className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-0.5">Quantification</div>
              <div className="text-xl font-bold text-purple-400">88%</div>
            </div>
          </div>
        </div>
      </div>

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

      {/* AI Suggestions */}
      <div className="flex justify-center pt-8">
        <button
          onClick={() => toast('AI suggestions coming soon!', { icon: '✨', style: { borderRadius: '12px', background: '#18181b', color: '#fff' } })}
          className="group flex items-center gap-3 px-8 py-4 rounded-full glass-dark border border-white/10 hover:bg-white/5 transition-all shadow-lg hover:shadow-xl hover:-translate-y-1"
        >
          <Sparkles className="h-5 w-5 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
          <span className="font-semibold text-white tracking-wide">Get AI Improvement Suggestions</span>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border border-indigo-500/30 text-indigo-300 bg-indigo-500/10 ml-2">Soon</span>
        </button>
      </div>
    </div>
  )
}

