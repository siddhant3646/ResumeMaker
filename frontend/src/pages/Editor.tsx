import { useState } from 'react'
import { Download, ArrowLeft, Edit3, Sparkles, CheckCircle, Target, BarChart3 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { downloadResumePDF } from '../services/api'
import toast from 'react-hot-toast'

export default function Editor() {
  const navigate = useNavigate()
  const [isDownloading, setIsDownloading] = useState(false)

  const tailoredResume = {
    basics: {
      name: 'John Doe',
      email: 'john@example.com',
      phone: '+1 234 567 8900'
    },
    summary: 'Experienced software engineer with 5+ years of experience in full-stack development...',
    experience: [
      {
        company: 'Tech Corp',
        role: 'Senior Software Engineer',
        bullets: [
          'Led development of microservices architecture serving 1M+ users',
          'Improved system performance by 40% through optimization initiatives'
        ]
      }
    ],
    ats_score: {
      overall: 92,
      keyword_match: 95,
      star_compliance: 90
    }
  }

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

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors group"
        >
          <div className="w-8 h-8 rounded-lg glass flex items-center justify-center group-hover:bg-white/10 transition-colors">
            <ArrowLeft className="h-4 w-4" />
          </div>
          <span>Back to Home</span>
        </button>

        <div className="flex gap-3 w-full sm:w-auto">
          <button
            onClick={() => toast('Edit feature coming soon!', { icon: 'ℹ️' })}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl glass hover:bg-white/10 text-slate-300 font-medium transition-all"
          >
            <Edit3 className="h-4 w-4" />
            <span>Edit</span>
          </button>

          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium transition-all shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 hover:-translate-y-0.5 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            <span>{isDownloading ? 'Downloading...' : 'Download PDF'}</span>
          </button>
        </div>
      </div>

      {/* ATS Score Card */}
      <div className="glass rounded-2xl p-6 gradient-border">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-green-500/25">
              <CheckCircle className="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Your Resume is Ready!</h2>
              <p className="text-slate-400 text-sm">Optimized for FAANG/MAANG ATS systems</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {/* Circular Progress */}
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="6"
                  fill="transparent"
                  className="text-slate-800"
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
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">{tailoredResume.ats_score.overall}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">ATS Score</div>
              <div className="text-xs text-green-400 font-medium">Excellent</div>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="grid grid-cols-3 gap-4">
          <div className="glass rounded-xl p-4 text-center group hover:bg-white/5 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform">
              <Target className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-2xl font-bold text-green-400">
              {tailoredResume.ats_score.keyword_match}%
            </div>
            <div className="text-xs text-slate-500">Keywords Match</div>
          </div>
          <div className="glass rounded-xl p-4 text-center group hover:bg-white/5 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform">
              <BarChart3 className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-blue-400">
              {tailoredResume.ats_score.star_compliance}%
            </div>
            <div className="text-xs text-slate-500">STAR Format</div>
          </div>
          <div className="glass rounded-xl p-4 text-center group hover:bg-white/5 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform">
              <Sparkles className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-purple-400">88%</div>
            <div className="text-xs text-slate-500">Quantification</div>
          </div>
        </div>
      </div>

      {/* Resume Preview */}
      <div className="glass rounded-2xl p-8 bg-white text-slate-900 shadow-xl">
        <div className="text-center mb-6 pb-4 border-b border-slate-200">
          <h1 className="text-2xl font-bold text-slate-800">{tailoredResume.basics.name}</h1>
          <p className="text-slate-500 text-sm mt-1">
            {tailoredResume.basics.email} • {tailoredResume.basics.phone}
          </p>
        </div>

        {tailoredResume.summary && (
          <div className="mb-6">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-2">
              Professional Summary
            </h2>
            <p className="text-slate-600 text-sm leading-relaxed">{tailoredResume.summary}</p>
          </div>
        )}

        <div>
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-3">
            Professional Experience
          </h2>
          {tailoredResume.experience.map((exp, idx) => (
            <div key={idx} className="mb-4">
              <div className="flex justify-between items-baseline mb-2">
                <h3 className="font-semibold text-slate-800">{exp.role}</h3>
                <span className="text-sm text-slate-500 font-medium">{exp.company}</span>
              </div>
              <ul className="space-y-1.5">
                {exp.bullets.map((bullet, bidx) => (
                  <li key={bidx} className="flex items-start gap-2 text-slate-600 text-sm">
                    <span className="text-indigo-500 mt-1">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* AI Suggestions */}
      <div className="flex justify-center">
        <button
          onClick={() => toast('AI suggestions coming soon!', { icon: '✨' })}
          className="flex items-center gap-2 px-6 py-3 rounded-xl glass glass-hover text-slate-300 font-medium transition-all"
        >
          <Sparkles className="h-5 w-5 text-indigo-400" />
          <span>Get AI Improvement Suggestions</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400">Soon</span>
        </button>
      </div>
    </div>
  )
}
