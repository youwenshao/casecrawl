export type BatchStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'paused'

export type CaseStatus = 
  | 'pending'
  | 'searching'
  | 'ambiguous'
  | 'awaiting_selection'
  | 'civil_procedure_blocked'
  | 'citation_mismatch'
  | 'analysis_only'
  | 'downloading'
  | 'completed'
  | 'error'

export type CitationMatchType = 'exact' | 'similar_volume' | 'year_match_only' | 'none'

export interface BatchJob {
  id: string
  status: BatchStatus
  created_at: string
  completed_at?: string
  total_cases: number
  user_id?: string
  auto_download_exact_matches: boolean
  completed_cases_count: number
  error_cases_count: number
  civil_procedure_blocked_count: number
  pending_cases_count: number
}

export interface BatchStatistics {
  batch_id: string
  status: BatchStatus
  total_cases: number
  completed: number
  pending: number
  errors: number
  ambiguous: number
  civil_procedure_blocked: number
  awaiting_selection: number
  progress_percentage: number
}

export interface CaseJob {
  id: string
  batch_id: string
  party_names_raw: string
  party_names_normalized?: {
    full: string
    abbreviated: string
    variations: string[]
  }
  citation_raw?: string
  citation_normalized?: string
  year_extracted?: number
  status: CaseStatus
  confidence_level?: 'high' | 'medium' | 'low'
  civil_procedure_flag: boolean
  volume_tolerance_applied: boolean
  file_path?: string
  file_name?: string
  westlaw_url?: string
  created_at: string
  updated_at: string
}

export interface SearchResultItem {
  id: string
  westlaw_citation: string
  where_reported: string[]
  principal_subject?: string
  is_civil_procedure: boolean
  parties_display: string
  decision_date?: string
  year: number
  available_documents: {
    pdf: boolean
    transcript: boolean
    analysis: boolean
  }
  citation_match_type: CitationMatchType
  similarity_score: number
  westlaw_url?: string
  citation_match_badge?: string
}

export interface WebSocketMessage {
  type: 'case_completed' | 'case_error' | 'civil_procedure_detected' | 
        'ambiguous_requires_selection' | 'batch_complete' | 'connected'
  case_id?: string
  batch_id?: string
  message?: string
  timestamp: string
  statistics?: BatchStatistics
}
