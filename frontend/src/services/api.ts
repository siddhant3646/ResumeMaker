import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// DEBUG-TEMP: log resolved API base URL
console.log('[DEBUG] VITE_API_URL env:', JSON.stringify(import.meta.env.VITE_API_URL))
console.log('[DEBUG] Resolved API_URL:', JSON.stringify(API_URL))
console.log('[DEBUG] window.location.origin:', window.location.origin)

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// DEBUG-TEMP: request interceptor
api.interceptors.request.use((config) => {
  const fullUrl = (config.baseURL || '') + (config.url || '')
  console.log(`[DEBUG] REQUEST ${config.method?.toUpperCase()} ${fullUrl}`)
  return config
})

// DEBUG-TEMP: response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`[DEBUG] RESPONSE ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('[DEBUG] RESPONSE ERROR', {
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      fullURL: (error.config?.baseURL || '') + (error.config?.url || ''),
      status: error.response?.status,
      message: error.message,
      code: error.code,
    })
    return Promise.reject(error)
  }
)

// Add auth token to requests
export const setAuthToken = (token: string) => {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Remove auth token
export const removeAuthToken = () => {
  delete api.defaults.headers.common['Authorization']
}

// Health check
export const healthCheck = async () => {
  const response = await api.get('/api/health')
  return response.data
}

// Resume API
export const uploadResume = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/api/resume/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const generateResume = async (data: {
  resume_data: any
  job_description: string
  config?: any
}) => {
  console.log('[DEBUG] generateResume called, baseURL:', api.defaults.baseURL) // DEBUG-TEMP
  try {
    const response = await api.post('/api/resume/generate', data, {
      timeout: 180_000, // 3 minutes — generation is synchronous and can take 60-120 s
    })
    console.log('[DEBUG] generateResume success:', response.status) // DEBUG-TEMP
    return response.data
  } catch (err: any) {
    console.error('[DEBUG] generateResume FAILED:', { // DEBUG-TEMP
      message: err.message,
      code: err.code,
      responseStatus: err.response?.status,
      responseData: err.response?.data,
      requestURL: err.config?.baseURL + err.config?.url,
    })
    throw err
  }
}

export const retryGeneration = async (data: {
  resume_data: any
  previous_result: any
  job_analysis: any
  job_description: string
  retry_count: number
  config?: any
}) => {
  const response = await api.post('/api/resume/retry', data, {
    timeout: 180_000,
  })
  return response.data
}

export const optimizeATS = async (data: { resume_data: any }) => {
  const response = await api.post('/api/resume/optimize-ats', data)
  return response.data
}

export const getGenerationStatus = async (jobId: string) => {
  const response = await api.get(`/api/resume/status/${jobId}`)
  return response.data
}

export const downloadResumePDF = async (resumeData: any) => {
  try {
    const response = await api.post('/api/resume/download', resumeData, {
      responseType: 'blob',
    })
    return response.data
  } catch (error: any) {
    if (error.response?.data instanceof Blob) {
      const text = await error.response.data.text()
      try {
        const json = JSON.parse(text)
        throw new Error(json.error || json.detail || 'Failed to download resume')
      } catch {
        throw new Error(text || 'Failed to download resume')
      }
    }
    throw error
  }
}

// WebSocket connection for real-time updates
export const createWebSocket = (jobId: string) => {
  const wsUrl = API_URL.replace('http', 'ws')
  return new WebSocket(`${wsUrl}/ws/${jobId}`)
}

// AI Improve text
export const improveText = async (data: {
  original_text: string
  user_prompt: string
  context: string
}) => {
  const response = await api.post('/api/resume/improve', data)
  return response.data
}

// Check ATS Score
export const checkATSScore = async (resumeData: any) => {
  const response = await api.post('/api/resume/check-ats', { resume_data: resumeData })
  return response.data
}

export default api
