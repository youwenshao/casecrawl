import axios from 'axios'
import { BatchJob, BatchStatistics, CaseJob, SearchResultItem } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Batch API
export const createBatch = async (
  file: File,
  autoDownload: boolean = true
): Promise<{ batch_id: string; total_cases: number; message: string }> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('auto_download_exact_matches', String(autoDownload))

  const response = await api.post('/batches', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getBatch = async (batchId: string): Promise<BatchJob> => {
  const response = await api.get(`/batches/${batchId}`)
  return response.data
}

export const getBatchStatistics = async (batchId: string): Promise<BatchStatistics> => {
  const response = await api.get(`/batches/${batchId}/statistics`)
  return response.data
}

export const getBatchCases = async (
  batchId: string,
  params?: { status?: string; skip?: number; limit?: number }
): Promise<{ items: CaseJob[]; total: number }> => {
  const response = await api.get(`/batches/${batchId}/cases`, { params })
  return response.data
}

// Case API
export const getCase = async (caseId: string): Promise<CaseJob> => {
  const response = await api.get(`/cases/${caseId}`)
  return response.data
}

export const getCaseSearchResults = async (
  caseId: string
): Promise<{
  case_id: string
  party_names_raw: string
  citation_raw?: string
  user_citation_normalized?: string
  results: SearchResultItem[]
  total_results: number
  has_exact_match: boolean
  has_civil_procedure: boolean
}> => {
  const response = await api.get(`/cases/${caseId}/search-results`)
  return response.data
}

export const selectCaseResult = async (
  caseId: string,
  resultId: string
): Promise<{ case_id: string; selected_result_id: string; status: string; message: string }> => {
  const response = await api.post(`/cases/${caseId}/select`, {
    result_id: resultId,
    override_civil_procedure: false,
  })
  return response.data
}

export const forceManualReview = async (
  caseId: string,
  reason?: string
): Promise<CaseJob> => {
  const response = await api.post(`/cases/${caseId}/force-manual`, { reason })
  return response.data
}

// Session API
export const createSession = async (credentials: {
  username: string
  password: string
  totp_code?: string
}) => {
  const response = await api.post('/sessions', credentials)
  return response.data
}

export default api
