import { useState } from 'react'
import { X, Loader2, Sparkles, Save, RotateCcw, Plus, Trash2 } from 'lucide-react'
import { improveText, checkATSScore } from '../services/api'
import toast from 'react-hot-toast'

interface EditModalProps {
  isOpen: boolean
  onClose: () => void
  resume: any
  onSave: (updatedResume: any) => void
}

export default function EditModal({ isOpen, onClose, resume, onSave }: EditModalProps) {
  const [editedResume, setEditedResume] = useState(resume)
  const [isImproving, setIsImproving] = useState(false)
  const [improvingField, setImprovingField] = useState<string | null>(null)
  const [aiPrompt, setAiPrompt] = useState('')
  const [isCheckingScore, setIsCheckingScore] = useState(false)
  const [showScore, setShowScore] = useState(false)
  const [atsScore, setAtsScore] = useState<any>(null)

  if (!isOpen) return null

  const handleImprove = async (field: string, currentValue: string, context: string) => {
    if (!aiPrompt.trim()) {
      toast.error('Please enter what you want to improve')
      return
    }

    setIsImproving(true)
    setImprovingField(field)

    try {
      const result = await improveText({
        original_text: currentValue,
        user_prompt: aiPrompt,
        context
      })

      if (result.success) {
        const newResume = { ...editedResume }
        
        if (field === 'summary') {
          newResume.summary = result.improved_text
        } else if (field.startsWith('bullet-')) {
          const [_, expIdx, bulletIdx] = field.split('-')
          newResume.experience[parseInt(expIdx)].bullets[parseInt(bulletIdx)] = result.improved_text
        }
        
        setEditedResume(newResume)
        toast.success('Text improved!')
        setAiPrompt('')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to improve text')
    } finally {
      setIsImproving(false)
      setImprovingField(null)
    }
  }

  const handleCheckScore = async () => {
    setIsCheckingScore(true)
    try {
      const result = await checkATSScore(editedResume)
      if (result.success) {
        setAtsScore(result.ats_score)
        setShowScore(true)
        toast.success('ATS Score calculated!')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to check ATS score')
    } finally {
      setIsCheckingScore(false)
    }
  }

  const handleSave = () => {
    onSave(editedResume)
    onClose()
    toast.success('Resume saved!')
  }

  const handleReset = () => {
    setEditedResume(resume)
    setShowScore(false)
    setAtsScore(null)
  }

  const updateField = (field: string, value: any) => {
    const newResume = { ...editedResume }
    if (field === 'name') newResume.basics.name = value
    else if (field === 'email') newResume.basics.email = value
    else if (field === 'phone') newResume.basics.phone = value
    else if (field === 'summary') newResume.summary = value
    setEditedResume(newResume)
  }

  const updateBullet = (expIdx: number, bulletIdx: number, value: string) => {
    const newResume = { ...editedResume }
    newResume.experience[expIdx].bullets[bulletIdx] = value
    setEditedResume(newResume)
  }

  const addBullet = (expIdx: number) => {
    const newResume = { ...editedResume }
    newResume.experience[expIdx].bullets.push('• ')
    setEditedResume(newResume)
  }

  const removeBullet = (expIdx: number, bulletIdx: number) => {
    const newResume = { ...editedResume }
    newResume.experience[expIdx].bullets.splice(bulletIdx, 1)
    setEditedResume(newResume)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-zinc-900 rounded-3xl shadow-2xl border border-white/10 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Edit Resume</h2>
              <p className="text-sm text-zinc-400">Make changes or use AI to improve</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5 text-zinc-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1">Name</label>
                <input
                  type="text"
                  value={editedResume.basics.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className="w-full px-4 py-2 bg-zinc-800 border border-white/10 rounded-xl text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1">Email</label>
                <input
                  type="email"
                  value={editedResume.basics.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  className="w-full px-4 py-2 bg-zinc-800 border border-white/10 rounded-xl text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1">Phone</label>
                <input
                  type="text"
                  value={editedResume.basics.phone || ''}
                  onChange={(e) => updateField('phone', e.target.value)}
                  className="w-full px-4 py-2 bg-zinc-800 border border-white/10 rounded-xl text-white"
                />
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-white">Professional Summary</h3>
            <div className="relative">
              <textarea
                value={editedResume.summary || ''}
                onChange={(e) => updateField('summary', e.target.value)}
                rows={3}
                className="w-full px-4 py-3 bg-zinc-800 border border-white/10 rounded-xl text-white resize-none"
              />
              <div className="absolute bottom-3 right-3 flex gap-2">
                <input
                  type="text"
                  placeholder="What to improve?"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  className="px-3 py-1 bg-zinc-700 border border-white/10 rounded-lg text-sm text-white placeholder-zinc-500 w-48"
                />
                <button
                  onClick={() => handleImprove('summary', editedResume.summary || '', 'professional summary')}
                  disabled={isImproving}
                  className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm text-white flex items-center gap-1 disabled:opacity-50"
                >
                  {isImproving && improvingField === 'summary' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  Improve
                </button>
              </div>
            </div>
          </div>

          {/* Experience */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Experience</h3>
            {editedResume.experience.map((exp: any, expIdx: number) => (
              <div key={expIdx} className="p-4 bg-zinc-800/50 rounded-xl space-y-3">
                <div className="flex items-center gap-4">
                  <input
                    type="text"
                    value={exp.role}
                    onChange={(e) => {
                      const newResume = { ...editedResume }
                      newResume.experience[expIdx].role = e.target.value
                      setEditedResume(newResume)
                    }}
                    placeholder="Role"
                    className="flex-1 px-3 py-2 bg-zinc-700 border border-white/10 rounded-lg text-white text-sm font-medium"
                  />
                  <input
                    type="text"
                    value={exp.company}
                    onChange={(e) => {
                      const newResume = { ...editedResume }
                      newResume.experience[expIdx].company = e.target.value
                      setEditedResume(newResume)
                    }}
                    placeholder="Company"
                    className="flex-1 px-3 py-2 bg-zinc-700 border border-white/10 rounded-lg text-white text-sm"
                  />
                </div>
                
                {exp.bullets.map((bullet: string, bulletIdx: number) => (
                  <div key={bulletIdx} className="flex items-start gap-2">
                    <textarea
                      value={bullet}
                      onChange={(e) => updateBullet(expIdx, bulletIdx, e.target.value)}
                      rows={2}
                      className="flex-1 px-3 py-2 bg-zinc-700 border border-white/10 rounded-lg text-white text-sm resize-none"
                    />
                    <button
                      onClick={() => removeBullet(expIdx, bulletIdx)}
                      className="p-2 text-zinc-500 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                
                <button
                  onClick={() => addBullet(expIdx)}
                  className="flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300"
                >
                  <Plus className="w-4 h-4" /> Add Bullet
                </button>
              </div>
            ))}
          </div>

          {/* ATS Score */}
          {showScore && atsScore && (
            <div className="p-4 bg-zinc-800/50 rounded-xl space-y-3">
              <h3 className="text-lg font-semibold text-white">ATS Score</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center p-3 bg-zinc-700 rounded-lg">
                  <div className="text-2xl font-bold text-emerald-400">{atsScore.overall}</div>
                  <div className="text-xs text-zinc-400">Overall</div>
                </div>
                <div className="text-center p-3 bg-zinc-700 rounded-lg">
                  <div className="text-2xl font-bold text-blue-400">{atsScore.keyword_match}</div>
                  <div className="text-xs text-zinc-400">Keywords</div>
                </div>
                <div className="text-center p-3 bg-zinc-700 rounded-lg">
                  <div className="text-2xl font-bold text-purple-400">{atsScore.star_compliance}</div>
                  <div className="text-xs text-zinc-400">STAR</div>
                </div>
                <div className="text-center p-3 bg-zinc-700 rounded-lg">
                  <div className="text-2xl font-bold text-orange-400">{atsScore.quantification}</div>
                  <div className="text-xs text-zinc-400">Quant</div>
                </div>
                <div className="text-center p-3 bg-zinc-700 rounded-lg">
                  <div className="text-2xl font-bold text-pink-400">{atsScore.action_verb_strength}</div>
                  <div className="text-xs text-zinc-400">Verbs</div>
                </div>
              </div>
              {atsScore.missing_keywords?.length > 0 && (
                <div className="mt-3">
                  <div className="text-sm font-medium text-zinc-400 mb-1">Missing Keywords:</div>
                  <div className="flex flex-wrap gap-1">
                    {atsScore.missing_keywords.map((kw: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-300 rounded text-xs">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-white/10 bg-zinc-900">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-zinc-400 hover:text-white transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          
          <div className="flex items-center gap-3">
            <button
              onClick={handleCheckScore}
              disabled={isCheckingScore}
              className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-xl text-white font-medium flex items-center gap-2 disabled:opacity-50"
            >
              {isCheckingScore ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Check ATS Score
            </button>
            
            <button
              onClick={handleSave}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-medium flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              Save Resume
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
