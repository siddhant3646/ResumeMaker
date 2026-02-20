import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, CheckCircle, AlertCircle, Loader2, FileText, Shield } from 'lucide-react'
import { uploadResume } from '../services/api'
import toast from 'react-hot-toast'

interface UploadStepProps {
  onUploadComplete: (data: any) => void
}

export default function UploadStep({ onUploadComplete }: UploadStepProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB')
      return
    }

    setUploadedFile(file)
    setIsUploading(true)

    try {
      const response = await uploadResume(file)
      
      if (response.success) {
        toast.success('Resume uploaded successfully!')
        onUploadComplete(response.resume_data)
      } else {
        toast.error(response.message || 'Upload failed')
      }
    } catch (error) {
      console.error('Upload error:', error)
      toast.error('Failed to upload resume. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }, [onUploadComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 mb-4">
          <Upload className="w-7 h-7 text-indigo-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Upload Your Resume</h2>
        <p className="text-slate-400 max-w-md mx-auto">
          Upload your master resume. Our AI will analyze it and prepare a tailored version.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          relative group cursor-pointer rounded-2xl p-10 transition-all duration-300
          ${isDragActive 
            ? 'bg-indigo-500/10 border-2 border-indigo-500/50 scale-[1.02]' 
            : 'glass glass-hover border border-transparent'
          }
          ${isUploading ? 'pointer-events-none' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        {/* Animated Border */}
        {!isDragActive && (
          <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 opacity-20 blur-sm"></div>
          </div>
        )}

        {isUploading ? (
          <div className="flex flex-col items-center relative z-10">
            <div className="relative w-16 h-16 mb-4">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20"></div>
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
              <div className="absolute inset-3 rounded-full bg-slate-900 flex items-center justify-center">
                <FileText className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <p className="text-lg font-semibold text-white mb-1">Processing your resume...</p>
            <p className="text-slate-400 text-sm">This may take a few seconds</p>
            
            {/* Progress Bar Animation */}
            <div className="w-full max-w-xs mt-4 h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full animate-shimmer" style={{ width: '60%', animation: 'shimmer 1.5s infinite' }}></div>
            </div>
          </div>
        ) : uploadedFile ? (
          <div className="flex flex-col items-center relative z-10">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mb-4 shadow-lg shadow-green-500/25">
              <CheckCircle className="w-8 h-8 text-white" />
            </div>
            <p className="text-lg font-semibold text-white mb-1">{uploadedFile.name}</p>
            <p className="text-slate-400 text-sm">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center relative z-10">
            <div className={`
              w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all duration-300
              ${isDragActive 
                ? 'bg-indigo-500/20 border-2 border-indigo-500/50' 
                : 'bg-slate-800/50 border border-slate-700'
              }
            `}>
              <Upload className={`w-8 h-8 transition-colors ${isDragActive ? 'text-indigo-400' : 'text-slate-400'}`} />
            </div>
            <p className="text-lg font-semibold text-white mb-2">
              {isDragActive ? 'Drop your resume here' : 'Drag and drop your resume'}
            </p>
            <p className="text-slate-400 text-sm mb-4">or click to browse files</p>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 text-xs text-slate-400">
                <File className="w-3.5 h-3.5" />
                <span>PDF only</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 text-xs text-slate-400">
                <span>Max 10MB</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
          <Shield className="w-4 h-4 text-indigo-400" />
        </div>
        <div>
          <p className="text-sm text-slate-300 font-medium mb-0.5">Privacy First</p>
          <p className="text-xs text-slate-500">
            Your resume is processed securely and never stored on our servers.
          </p>
        </div>
      </div>
    </div>
  )
}
