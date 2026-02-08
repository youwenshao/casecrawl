import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle,
  ExternalLink,
  FileText,
  ScrollText,
  FileX,
  Scale
} from 'lucide-react'
import { getCase, getCaseSearchResults, selectCaseResult } from '../utils/api'
import { SearchResultItem, CitationMatchType } from '../types'

const matchTypeConfig: Record<CitationMatchType, { label: string; color: string }> = {
  exact: { label: 'Exact Match', color: 'bg-green-100 text-green-800 border-green-200' },
  similar_volume: { label: 'Volume Tolerance', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  year_match_only: { label: 'Year Match Only', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  none: { label: 'No Match', color: 'bg-red-100 text-red-800 border-red-200' },
}

const Disambiguation = () => {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const [selectedResult, setSelectedResult] = useState<string | null>(null)

  // Queries
  const caseQuery = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => getCase(caseId!),
    enabled: !!caseId,
  })

  const resultsQuery = useQuery({
    queryKey: ['case-results', caseId],
    queryFn: () => getCaseSearchResults(caseId!),
    enabled: !!caseId,
  })

  // Mutation
  const selectMutation = useMutation({
    mutationFn: (resultId: string) => selectCaseResult(caseId!, resultId),
    onSuccess: () => {
      navigate('/dashboard')
    },
  })

  const handleSelect = () => {
    if (selectedResult) {
      selectMutation.mutate(selectedResult)
    }
  }

  if (caseQuery.isLoading || resultsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const caseData = caseQuery.data
  const results = resultsQuery.data

  if (!caseData || !results) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Case not found</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Select Correct Case</h1>
        <p className="text-gray-600 mt-1">
          Multiple matches found for this case. Please review and select the correct one.
        </p>
      </div>

      {/* Input Details */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h2 className="text-sm font-medium text-blue-900 mb-2">Your Input</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-blue-700 uppercase tracking-wide">Party Names</p>
            <p className="text-sm font-medium text-blue-900">{caseData.party_names_raw}</p>
          </div>
          <div>
            <p className="text-xs text-blue-700 uppercase tracking-wide">Citation</p>
            <p className="text-sm font-medium text-blue-900">
              {caseData.citation_raw || 'Not provided'}
            </p>
          </div>
        </div>
      </div>

      {/* Civil Procedure Warning */}
      {results.has_civil_procedure && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-900">Civil Procedure Cases Detected</h3>
              <p className="text-sm text-red-700 mt-1">
                One or more results are Civil Procedure cases. These require manual Westlaw review.
                Auto-download is disabled for Civil Procedure cases.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Volume Tolerance Warning */}
      {results.results.some(r => r.citation_match_type === 'similar_volume') && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <Scale className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-900">Volume Number Differs</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Some results have different volume numbers than your citation. 
                This will be flagged if selected.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results Grid */}
      <div className="space-y-4">
        {results.results.map((result) => (
          <ResultCard
            key={result.id}
            result={result}
            userCitation={caseData.citation_raw}
            isSelected={selectedResult === result.id}
            onSelect={() => setSelectedResult(result.id)}
            disabled={selectMutation.isPending}
          />
        ))}
      </div>

      {/* Actions */}
      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={() => navigate('/dashboard')}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSelect}
          disabled={!selectedResult || selectMutation.isPending}
          className={`
            px-6 py-2 rounded-lg text-sm font-medium text-white
            transition-colors duration-200
            ${!selectedResult || selectMutation.isPending
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
            }
          `}
        >
          {selectMutation.isPending ? 'Selecting...' : 'Select Case'}
        </button>
      </div>

      {/* Error */}
      {selectMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">
            {selectMutation.error instanceof Error 
              ? selectMutation.error.message 
              : 'Failed to select case. Please try again.'}
          </p>
        </div>
      )}
    </div>
  )
}

interface ResultCardProps {
  result: SearchResultItem
  userCitation?: string
  isSelected: boolean
  onSelect: () => void
  disabled: boolean
}

const ResultCard = ({ result, userCitation, isSelected, onSelect, disabled }: ResultCardProps) => {
  const matchConfig = matchTypeConfig[result.citation_match_type]
  const canDownload = result.has_downloadable_document && !result.is_civil_procedure

  return (
    <div
      onClick={() => !disabled && onSelect()}
      className={`
        border-2 rounded-lg p-4 cursor-pointer transition-all duration-200
        ${isSelected 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-200 hover:border-gray-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-sm font-medium text-gray-900">{result.parties_display}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${matchConfig.color}`}>
              {matchConfig.label}
            </span>
            {result.is_civil_procedure && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-800 border border-red-200">
                Civil Procedure
              </span>
            )}
          </div>

          {/* Citation Info */}
          <div className="grid md:grid-cols-2 gap-2 mb-3">
            <div>
              <p className="text-xs text-gray-500">Westlaw Citation</p>
              <p className="text-sm font-medium text-gray-900">{result.westlaw_citation}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Where Reported</p>
              <p className="text-sm text-gray-900">
                {result.where_reported.slice(0, 3).join(', ')}
                {result.where_reported.length > 3 && '...'}
              </p>
            </div>
          </div>

          {/* Details */}
          <div className="grid md:grid-cols-3 gap-2 text-sm">
            <div>
              <span className="text-gray-500">Year:</span>{' '}
              <span className="font-medium">{result.year}</span>
            </div>
            <div>
              <span className="text-gray-500">Decision Date:</span>{' '}
              <span className="font-medium">{result.decision_date || 'Unknown'}</span>
            </div>
            <div>
              <span className="text-gray-500">Match Score:</span>{' '}
              <span className="font-medium">{(result.similarity_score * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Principal Subject */}
          {result.principal_subject && (
            <div className="mt-2">
              <p className="text-xs text-gray-500">Principal Subject</p>
              <p className="text-sm text-gray-700">{result.principal_subject}</p>
            </div>
          )}

          {/* Available Documents */}
          <div className="mt-3 flex items-center space-x-4">
            <span className="text-xs text-gray-500">Available Documents:</span>
            <div className="flex items-center space-x-3">
              <DocumentBadge 
                type="PDF" 
                available={result.available_documents.pdf}
              />
              <DocumentBadge 
                type="Transcript" 
                available={result.available_documents.transcript}
              />
              <DocumentBadge 
                type="Analysis" 
                available={result.available_documents.analysis}
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col items-end space-y-2 ml-4">
          {result.westlaw_url && (
            <a
              href={result.westlaw_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <span>View on Westlaw</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {!canDownload && (
            <span className="text-xs text-red-600 flex items-center">
              <FileX className="w-3 h-3 mr-1" />
              Cannot auto-download
            </span>
          )}
          {isSelected && (
            <CheckCircle2 className="w-6 h-6 text-blue-600" />
          )}
        </div>
      </div>
    </div>
  )
}

const DocumentBadge = ({ type, available }: { type: string; available: boolean }) => (
  <span className={`
    inline-flex items-center space-x-1 text-xs
    ${available ? 'text-green-700' : 'text-gray-400'}
  `}>
    {type === 'PDF' && <FileText className="w-3 h-3" />}
    {type === 'Transcript' && <ScrollText className="w-3 h-3" />}
    {type === 'Analysis' && <Scale className="w-3 h-3" />}
    <span>{type}</span>
    {available ? (
      <CheckCircle2 className="w-3 h-3" />
    ) : (
      <XCircle className="w-3 h-3" />
    )}
  </span>
)

export default Disambiguation
