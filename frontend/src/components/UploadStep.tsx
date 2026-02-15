import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
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

    // Validate file
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
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Upload Your Resume</h2>
        <p className="text-slate-400">
          Upload your master resume (PDF format). Our AI will analyze it and prepare to create a tailored version optimized for your target job.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${isDragActive 
            ? 'border-blue-500 bg-blue-500/10' 
            : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/50'
          }
          ${isUploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        {isUploading ? (
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-4" />
            <p className="text-lg font-medium text-white">Processing your resume...</p>
            <p className="text-slate-400">This may take a few seconds</p>
          </div>
        ) : uploadedFile ? (
          <div className="flex flex-col items-center">
            <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
            <p className="text-lg font-medium text-white">{uploadedFile.name}</p>
            <p className="text-slate-400">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <Upload className="h-12 w-12 text-slate-500 mb-4" />
            <p className="text-lg font-medium text-white mb-2">
              {isDragActive ? 'Drop your resume here' : 'Drag and drop your resume'}
            </p>
            <p className="text-slate-400 mb-4">or click to browse files</p>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <File className="h-4 w-4" />
              <span>PDF only • Max 10MB</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-start gap-3 p-4 bg-slate-800/50 rounded-lg">
        <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-slate-400">
          Your resume is processed locally and never stored on our servers. We only extract text for AI optimization.
        </p>
      </div>
    </div>
  )
}
