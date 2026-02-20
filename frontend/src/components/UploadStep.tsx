import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, CheckCircle, FileText, Shield } from 'lucide-react'
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
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-[1.25rem] bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 mb-5 shadow-inner">
          <Upload className="w-8 h-8 text-indigo-400" />
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight mb-2">Upload Your Resume</h2>
        <p className="text-zinc-400 font-medium max-w-md mx-auto">
          Upload your master resume. Our AI will deeply analyze it and intelligently prepare a tailored version.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          relative group cursor-pointer rounded-3xl p-12 transition-all duration-300
          ${isDragActive
            ? 'glass-dark border border-indigo-500/50 scale-[1.02] shadow-[0_0_30px_rgba(99,102,241,0.2)]'
            : 'glass-dark border border-white/5 hover:border-white/10 hover:bg-white/[0.04]'
          }
          ${isUploading ? 'pointer-events-none' : ''}
        `}
      >
        <input {...getInputProps()} />

        {/* Animated Border */}
        {!isDragActive && (
          <div className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-indigo-500/20 blur-xl"></div>
          </div>
        )}

        {isUploading ? (
          <div className="flex flex-col items-center relative z-10">
            <div className="relative w-20 h-20 mb-6 drop-shadow-md">
              <div className="absolute inset-0 rounded-full border-4 border-zinc-800"></div>
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
              <div className="absolute inset-3 rounded-full bg-zinc-950 flex items-center justify-center shadow-inner">
                <FileText className="w-6 h-6 text-indigo-400" />
              </div>
            </div>
            <p className="text-xl font-bold text-white tracking-tight mb-1.5">Processing your resume...</p>
            <p className="text-zinc-400 font-medium">This typically takes a few seconds</p>

            {/* Progress Bar Animation */}
            <div className="w-full max-w-xs mt-6 h-1.5 bg-zinc-800 rounded-full overflow-hidden border border-white/5">
              <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" style={{ width: '60%', animation: 'shimmer 1.5s infinite' }}></div>
            </div>
          </div>
        ) : uploadedFile ? (
          <div className="flex flex-col items-center relative z-10 animate-fade-in">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mb-5 shadow-lg shadow-emerald-500/30">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <p className="text-xl font-bold text-white tracking-tight mb-1">{uploadedFile.name}</p>
            <p className="text-zinc-400 font-medium tracking-wide">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center relative z-10">
            <div className={`
              w-20 h-20 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300 shadow-inner
              ${isDragActive
                ? 'bg-indigo-500/20 border border-indigo-500/50'
                : 'bg-zinc-800/40 border border-zinc-700/50'
              }
            `}>
              <Upload className={`w-10 h-10 transition-colors duration-300 ${isDragActive ? 'text-indigo-400' : 'text-zinc-500'}`} />
            </div>
            <p className="text-xl font-bold text-white tracking-tight mb-2">
              {isDragActive ? 'Drop your majestic resume here' : 'Drag and drop your resume'}
            </p>
            <p className="text-zinc-400 font-medium mb-6">or click to browse local files</p>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-800/40 border border-white/5 text-[13px] font-semibold tracking-wide text-zinc-400 shadow-sm">
                <File className="w-4 h-4 text-zinc-500" />
                <span>PDF only</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-800/40 border border-white/5 text-[13px] font-semibold tracking-wide text-zinc-400 shadow-sm">
                <span>Max 10MB</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="flex items-center gap-4 p-5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-sm">
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center shadow-inner">
          <Shield className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <p className="text-[15px] text-zinc-200 font-bold tracking-tight mb-0.5">Privacy First</p>
          <p className="text-sm text-zinc-400 font-medium">
            Your resume is processed absolutely securely and is never durably stored on our servers.
          </p>
        </div>
      </div>
    </div>
  )
}

