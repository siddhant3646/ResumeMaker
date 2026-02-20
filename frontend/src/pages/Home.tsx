import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Download, Check, Sparkles, Target, Briefcase } from 'lucide-react'
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
        <div className="absolute top-20 right-20 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl animate-pulse-glow"></div>
        <div className="absolute bottom-20 left-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse-glow delay-200"></div>
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="text-center mb-10 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-4">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm text-slate-300">AI-Powered Resume Optimization</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="text-white">Create Your </span>
            <span className="gradient-text">Perfect Resume</span>
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Upload your resume, customize it for your target job, and download an ATS-optimized version in minutes.
          </p>
        </div>

        {/* Feature Cards - Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10 animate-fade-in-up delay-100">
          <div className="card-modern group">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Target className="w-5 h-5 text-indigo-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">ATS Optimized</h3>
            <p className="text-sm text-slate-400">Beat applicant tracking systems with keyword optimization</p>
          </div>
          <div className="card-modern group">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Briefcase className="w-5 h-5 text-purple-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">Job Tailored</h3>
            <p className="text-sm text-slate-400">Customize for specific roles and companies</p>
          </div>
          <div className="card-modern group">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Sparkles className="w-5 h-5 text-blue-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">AI Enhanced</h3>
            <p className="text-sm text-slate-400">Powered by advanced AI for best results</p>
          </div>
        </div>

        {/* Step Wizard */}
        <div className="mb-8 animate-fade-in-up delay-200">
          <div className="flex items-center justify-center">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = step.id === currentStep
              const isCompleted = step.id < currentStep

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`relative w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-500 ${
                        isActive
                          ? 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25 scale-110'
                          : isCompleted
                          ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-500/25'
                          : 'glass'
                      }`}
                    >
                      {/* Pulse Animation for Active */}
                      {isActive && (
                        <div className="absolute inset-0 rounded-2xl bg-indigo-500 animate-ping opacity-20"></div>
                      )}
                      
                      {isCompleted ? (
                        <Check className="h-6 w-6 text-white relative z-10" />
                      ) : (
                        <Icon className={`h-6 w-6 relative z-10 ${
                          isActive ? 'text-white' : 'text-slate-400'
                        }`} />
                      )}
                    </div>
                    <span className={`mt-3 text-sm font-medium transition-colors ${
                      isActive ? 'text-white' : isCompleted ? 'text-green-400' : 'text-slate-500'
                    }`}>
                      {step.name}
                    </span>
                    <span className="text-xs text-slate-600 mt-0.5 hidden sm:block">
                      {step.description}
                    </span>
                  </div>

                  {index < steps.length - 1 && (
                    <div className="mx-6 w-20 md:w-32">
                      <div className="relative h-1 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className={`absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500 ${
                            step.id < currentStep ? 'w-full' : 'w-0'
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
          <div className="glass rounded-3xl p-6 md:p-8 gradient-border">
            {currentStep === 1 && (
              <UploadStep onUploadComplete={handleUploadComplete} />
            )}

            {currentStep === 2 && resumeData && (
              <JobDescStep
                resumeData={resumeData}
                onGenerationStart={handleGenerationStart}
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
        <div className="mt-12 text-center">
          <p className="text-sm text-slate-500">
            Your data is secure and never stored on our servers
          </p>
        </div>
      </div>
    </div>
  )
}
