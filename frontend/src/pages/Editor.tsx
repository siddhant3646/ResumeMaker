import { useState } from 'react'
import { Download, ArrowLeft, Edit3, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { downloadResumePDF } from '../services/api'
import toast from 'react-hot-toast'

export default function Editor() {
  const navigate = useNavigate()
  const [isDownloading, setIsDownloading] = useState(false)

  // Mock tailored resume data (would come from API/context in real app)
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
    } catch (error) {
      toast.error('Failed to download resume')
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          Back to Home
        </button>

        <div className="flex gap-3">
          <button
            onClick={() => toast.info('Edit feature coming soon!')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
          >
            <Edit3 className="h-4 w-4" />
            Edit Resume
          </button>

          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white transition-colors disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {isDownloading ? 'Downloading...' : 'Download PDF'}
          </button>
        </div>
      </div>

      {/* ATS Score Card */}
      <div className="glass rounded-2xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">Your Resume is Ready!</h2>
            <p className="text-slate-400">Optimized for FAANG/MAANG ATS systems</p>
          </div>

          <div className="text-center">
            <div className="text-4xl font-bold gradient-text">
              {tailoredResume.ats_score.overall}
            </div>
            <div className="text-sm text-slate-500">ATS Score</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-400">
              {tailoredResume.ats_score.keyword_match}%
            </div>
            <div className="text-xs text-slate-500">Keywords</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-400">
              {tailoredResume.ats_score.star_compliance}%
            </div>
            <div className="text-xs text-slate-500">STAR Format</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-400">
              88%
            </div>
            <div className="text-xs text-slate-500">Quantification</div>
          </div>
        </div>
      </div>

      {/* Resume Preview */}
      <div className="glass rounded-2xl p-8 bg-white text-slate-900">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold">{tailoredResume.basics.name}</h1>
          <p className="text-slate-600">
            {tailoredResume.basics.email} | {tailoredResume.basics.phone}
          </p>
        </div>

        {tailoredResume.summary && (
          <div className="mb-6">
            <h2 className="text-lg font-bold border-b-2 border-slate-300 pb-2 mb-3">
              Summary
            </h2>
            <p>{tailoredResume.summary}</p>
          </div>
        )}

        <div>
          <h2 className="text-lg font-bold border-b-2 border-slate-300 pb-2 mb-3">
            Experience
          </h2>
          {tailoredResume.experience.map((exp, idx) => (
            <div key={idx} className="mb-4">
              <div className="flex justify-between items-baseline">
                <h3 className="font-semibold">{exp.role}</h3>
                <span className="text-sm text-slate-600">{exp.company}</span>
              </div>
              <ul className="list-disc list-inside mt-2 space-y-1">
                {exp.bullets.map((bullet, bidx) => (
                  <li key={bidx} className="text-slate-700">{bullet}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-center mt-8">
        <button
          onClick={() => toast.info('AI suggestions coming soon!')}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white transition-colors"
        >
          <Sparkles className="h-5 w-5" />
          Get AI Improvement Suggestions
        </button>
      </div>
    </div>
  )
}
