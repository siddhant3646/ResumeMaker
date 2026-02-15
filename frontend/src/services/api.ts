import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
  const response = await api.post('/api/resume/generate', data)
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
  const response = await api.post('/api/resume/download', resumeData, {
    responseType: 'blob',
  })
  return response.data
}

// WebSocket connection for real-time updates
export const createWebSocket = (jobId: string) => {
  const wsUrl = API_URL.replace('http', 'ws')
  return new WebSocket(`${wsUrl}/ws/${jobId}`)
}

export default api
