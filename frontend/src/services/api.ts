import axios, { AxiosError } from 'axios'

// Backend URL configuration
// Only supports Streamlit backend
const getApiUrl = (): string => {
  const url = import.meta.env.VITE_API_URL
  if (!url) {
    console.error('VITE_API_URL is required')
    throw new Error('API URL not configured')
  }
  
  if (!url.startsWith('http')) {
    console.warn('API URL should start with http:// or https://')
  }
  
  return url
}

const API_URL = getApiUrl()

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Retry helper for transient failures
const fetchWithRetry = async <T>(fn: () => Promise<T>, retries = 2): Promise<T> => {
  try {
    return await fn()
  } catch (error) {
    if (retries > 0 && (error as AxiosError)?.code === 'ECONNABORTED') {
      console.log(`Request timed out, retrying... (${retries} retries left)`)
      return fetchWithRetry(fn, retries - 1)
    }
    throw error
  }
}

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
  const response = await fetchWithRetry(() => api.post('/api/resume/generate', data, {
    timeout: 300_000, // 5 minutes for HuggingFace cold start
  }))
  return response.data
}

export const regenerateResume = async (data: {
  resume_data: any
  job_description: string
  attempt: number
  force_variation?: boolean
}) => {
  const response = await fetchWithRetry(() => api.post('/api/resume/regenerate', data, {
    timeout: 300_000, // 5 minutes for HuggingFace
  }))
  return response.data
}

export const consolidateResume = async (data: {
  resume_data: any
  job_description?: string
}) => {
  const response = await api.post('/api/resume/consolidate', data, {
    timeout: 60_000,
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
  const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
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
