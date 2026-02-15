import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Download, Check } from 'lucide-react'
import UploadStep from '../components/UploadStep'
import JobDescStep from '../components/JobDescStep'
import ProgressStep from '../components/ProgressStep'

export default function Home() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [resumeData, setResumeData] = useState<any>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  const steps = [
    { id: 1, name: 'Upload', icon: Upload },
    { id: 2, name: 'Customize', icon: FileText },
    { id: 3, name: 'Download', icon: Download },
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
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 gradient-text">
          ATS Resume Maker
        </h1>
        <p className="text-slate-400 text-lg">
          AI-Powered Resume Optimization for FAANG/MAANG Companies
        </p>
      </div>

      {/* Step Wizard */}
      <div className="mb-8">
        <div className="flex items-center justify-center">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isActive = step.id === currentStep
            const isCompleted = step.id < currentStep

            return (
              <div key={step.id} className="flex items-center">
                <div
                  className={`flex flex-col items-center ${
                    isActive
                      ? 'text-blue-400'
                      : isCompleted
                      ? 'text-green-400'
                      : 'text-slate-600'
                  }`}
                >
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-colors ${
                      isActive
                        ? 'border-blue-400 bg-blue-400/10'
                        : isCompleted
                        ? 'border-green-400 bg-green-400/10'
                        : 'border-slate-700 bg-slate-800/50'
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="h-6 w-6" />
                    ) : (
                      <Icon className="h-6 w-6" />
                    )}
                  </div>
                  <span className="mt-2 text-sm font-medium">{step.name}</span>
                </div>

                {index < steps.length - 1 && (
                  <div className="mx-4 w-16 md:w-24">
                    <div
                      className={`h-0.5 transition-colors ${
                        step.id < currentStep ? 'bg-green-400' : 'bg-slate-700'
                      }`}
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="glass rounded-2xl p-6 md:p-8">
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
  )
}
