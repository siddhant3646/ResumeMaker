import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Download, Check, Sparkles, Target, Briefcase, Shield } from 'lucide-react'
import UploadStep from '../components/UploadStep'
import JobDescStep from '../components/JobDescStep'
import ProgressStep from '../components/ProgressStep'

export default function Home() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [resumeData, setResumeData] = useState<any>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  const steps = [
    { id: 1, name: 'Upload', icon: Upload, description: 'Upload your resume' },
    { id: 2, name: 'Customize', icon: FileText, description: 'Add job details' },
    { id: 3, name: 'Download', icon: Download, description: 'Get your resume' },
  ]

  const handleUploadComplete = (data: any) => {
    setResumeData(data)
    setCurrentStep(2)
  }

  const handleGenerationStart = (id: string) => {
    setJobId(id)
    setCurrentStep(3)
  }

  const handleGenerationComplete = () => {
    navigate('/editor')
  }

  return (
    <div className="min-h-screen relative">
      {/* Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-20 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px] animate-pulse-glow"></div>
        <div className="absolute bottom-20 left-20 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[120px] animate-pulse-glow delay-200"></div>
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-12 lg:py-16">

        {/* Header */}
        <div className="text-center mb-16 animate-fade-in-up">
          <div className="badge badge-glow mb-6 inline-flex animate-float">
            <Sparkles className="w-3.5 h-3.5 mr-2 text-indigo-300" />
            <span>AI-Powered Resume Optimization</span>
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
            <span className="text-white">Create Your </span>
            <span className="gradient-text">Perfect Resume</span>
          </h1>
          <p className="text-zinc-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed font-medium">
            Upload your resume, intricately tailor it for your target job, and download an ATS-optimized version in minutes.
          </p>
        </div>

        {/* Feature Cards - Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 animate-fade-in-up delay-100">
          <div className="card-modern group p-8">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300 shadow-[0_0_15px_rgba(99,102,241,0.15)]">
              <Target className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="font-bold text-white mb-2 text-lg tracking-tight">ATS Optimized</h3>
            <p className="text-sm text-zinc-400 font-medium leading-relaxed">Beat applicant tracking systems effortlessly with intelligent keyword optimization.</p>
          </div>
          <div className="card-modern group p-8">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300 shadow-[0_0_15px_rgba(168,85,247,0.15)]">
              <Briefcase className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="font-bold text-white mb-2 text-lg tracking-tight">Job Tailored</h3>
            <p className="text-sm text-zinc-400 font-medium leading-relaxed">Customize bullet points perfectly for specific roles and high-tier companies.</p>
          </div>
          <div className="card-modern group p-8">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300 shadow-[0_0_15px_rgba(59,130,246,0.15)]">
              <Sparkles className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="font-bold text-white mb-2 text-lg tracking-tight">AI Enhanced</h3>
            <p className="text-sm text-zinc-400 font-medium leading-relaxed">Powered by advanced AI for industry-leading qualitative results.</p>
          </div>
        </div>

        {/* Step Wizard */}
        <div className="mb-12 animate-fade-in-up delay-200">
          <div className="flex items-center justify-center">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = step.id === currentStep
              const isCompleted = step.id < currentStep

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`relative w-16 h-16 rounded-[1.25rem] flex items-center justify-center transition-all duration-500 ${isActive
                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-[0_8px_30px_rgba(99,102,241,0.3)] scale-110 text-white'
                        : isCompleted
                          ? 'bg-gradient-to-br from-emerald-400 to-teal-500 shadow-[0_8px_30px_rgba(52,211,153,0.3)] text-white'
                          : 'glass text-zinc-400'
                        }`}
                    >
                      {/* Pulse Animation for Active */}
                      {isActive && (
                        <div className="absolute inset-0 rounded-[1.25rem] bg-indigo-500 animate-ping opacity-20"></div>
                      )}

                      {isCompleted ? (
                        <Check className="h-7 w-7 relative z-10" />
                      ) : (
                        <Icon className="h-7 w-7 relative z-10" />
                      )}
                    </div>
                    <span className={`mt-4 text-[15px] font-semibold transition-colors ${isActive ? 'text-white' : isCompleted ? 'text-emerald-400' : 'text-zinc-500'
                      }`}>
                      {step.name}
                    </span>
                    <span className="text-xs font-medium text-zinc-600 mt-1 hidden sm:block tracking-wide">
                      {step.description}
                    </span>
                  </div>

                  {index < steps.length - 1 && (
                    <div className="mx-6 w-16 sm:w-24 md:w-32">
                      <div className="relative h-1.5 rounded-full bg-white/5 border border-white/5 overflow-hidden">
                        <div
                          className={`absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-700 ease-out ${step.id < currentStep ? 'w-full' : 'w-0'
                            }`}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="animate-fade-in-up delay-300">
          <div className="card-modern gradient-border bg-black/40">
            {currentStep === 1 && (
              <UploadStep onUploadComplete={handleUploadComplete} />
            )}

            {currentStep === 2 && resumeData && (
              <JobDescStep
                resumeData={resumeData}
                onGenerationStart={handleGenerationStart}
                onAtsComplete={(tailoredResume) => {
                  // Save the result directly and navigate to editor
                  localStorage.setItem('tailored_resume', JSON.stringify(tailoredResume))
                  navigate('/editor')
                }}
                onBack={() => setCurrentStep(1)}
              />
            )}

            {currentStep === 3 && jobId && (
              <ProgressStep
                jobId={jobId}
                onComplete={handleGenerationComplete}
              />
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 pb-8 text-center animate-fade-in delay-400">
          <p className="text-sm font-medium text-zinc-600 flex items-center justify-center gap-2">
            <Shield className="w-4 h-4" />
            Your data is strictly secure and never structurally stored on our servers
          </p>
        </div>
      </div>
    </div>
  )
}
