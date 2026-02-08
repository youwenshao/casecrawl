import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock,
  FileText,
  ExternalLink,
  Pause,
  Play,
  HelpCircle
} from 'lucide-react'
import { getBatch, getBatchStatistics, getBatchCases } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'
import { CaseJob, CaseStatus, BatchStatistics } from '../types'

const statusConfig: Record<CaseStatus, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: 'Pending', color: 'bg-gray-100 text-gray-700', icon: <Clock className="w-4 h-4" /> },
  searching: { label: 'Searching', color: 'bg-blue-100 text-blue-700', icon: <Loader2 className="w-4 h-4 animate-spin" /> },
  ambiguous: { label: 'Ambiguous', color: 'bg-yellow-100 text-yellow-700', icon: <HelpCircle className="w-4 h-4" /> },
  awaiting_selection: { label: 'Awaiting Selection', color: 'bg-orange-100 text-orange-700', icon: <HelpCircle className="w-4 h-4" /> },
  civil_procedure_blocked: { label: 'Civil Procedure', color: 'bg-red-100 text-red-700', icon: <AlertTriangle className="w-4 h-4" /> },
  citation_mismatch: { label: 'Citation Mismatch', color: 'bg-red-100 text-red-700', icon: <XCircle className="w-4 h-4" /> },
  analysis_only: { label: 'Analysis Only', color: 'bg-purple-100 text-purple-700', icon: <FileText className="w-4 h-4" /> },
  downloading: { label: 'Downloading', color: 'bg-blue-100 text-blue-700', icon: <Loader2 className="w-4 h-4 animate-spin" /> },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-700', icon: <CheckCircle2 className="w-4 h-4" /> },
  error: { label: 'Error', color: 'bg-red-100 text-red-700', icon: <XCircle className="w-4 h-4" /> },
}

const Dashboard = () => {
  const { batchId } = useParams<{ batchId?: string }>()
  const [selectedBatchId, setSelectedBatchId] = useState<string | undefined>(batchId)

  // WebSocket for real-time updates
  const { isConnected, lastMessage } = useWebSocket({
    batchId: selectedBatchId,
  })

  // Queries
  const batchQuery = useQuery({
    queryKey: ['batch', selectedBatchId],
    queryFn: () => getBatch(selectedBatchId!),
    enabled: !!selectedBatchId,
    refetchInterval: 5000,
  })

  const statsQuery = useQuery({
    queryKey: ['batch-stats', selectedBatchId],
    queryFn: () => getBatchStatistics(selectedBatchId!),
    enabled: !!selectedBatchId,
    refetchInterval: 5000,
  })

  const casesQuery = useQuery({
    queryKey: ['batch-cases', selectedBatchId],
    queryFn: () => getBatchCases(selectedBatchId!, { limit: 50 }),
    enabled: !!selectedBatchId,
    refetchInterval: 5000,
  })

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      // Refetch data on relevant messages
      if (lastMessage.type === 'case_completed' || 
          lastMessage.type === 'case_error' ||
          lastMessage.type === 'civil_procedure_detected') {
        batchQuery.refetch()
        statsQuery.refetch()
        casesQuery.refetch()
      }
    }
  }, [lastMessage])

  if (!selectedBatchId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No batch selected. <Link to="/" className="text-blue-600 hover:underline">Upload a file</Link> to get started.</p>
      </div>
    )
  }

  const stats = statsQuery.data
  const cases = casesQuery.data?.items || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Batch Progress</h1>
          <p className="text-sm text-gray-500">Batch ID: {selectedBatchId}</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <StatCard 
            label="Total" 
            value={stats.total_cases} 
            color="bg-gray-50 border-gray-200" 
          />
          <StatCard 
            label="Completed" 
            value={stats.completed} 
            color="bg-green-50 border-green-200" 
            textColor="text-green-700"
          />
          <StatCard 
            label="Pending" 
            value={stats.pending} 
            color="bg-blue-50 border-blue-200" 
            textColor="text-blue-700"
          />
          <StatCard 
            label="Errors" 
            value={stats.errors} 
            color="bg-red-50 border-red-200" 
            textColor="text-red-700"
          />
          <StatCard 
            label="Ambiguous" 
            value={stats.ambiguous} 
            color="bg-yellow-50 border-yellow-200" 
            textColor="text-yellow-700"
          />
          <StatCard 
            label="Civil Proc." 
            value={stats.civil_procedure_blocked} 
            color="bg-red-50 border-red-200" 
            textColor="text-red-700"
          />
          <StatCard 
            label="Awaiting" 
            value={stats.awaiting_selection} 
            color="bg-orange-50 border-orange-200" 
            textColor="text-orange-700"
          />
        </div>
      )}

      {/* Progress Bar */}
      {stats && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Overall Progress</span>
            <span className="text-sm font-medium text-gray-900">{stats.progress_percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${stats.progress_percentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Cases Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="text-sm font-medium text-gray-900">Recent Cases</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Party Names
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Citation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {cases.map((caseItem) => (
                <CaseRow key={caseItem.id} caseItem={caseItem} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

const StatCard = ({ 
  label, 
  value, 
  color, 
  textColor = 'text-gray-900' 
}: { 
  label: string
  value: number
  color: string
  textColor?: string 
}) => (
  <div className={`${color} border rounded-lg p-3`}>
    <p className="text-xs text-gray-600 uppercase tracking-wide">{label}</p>
    <p className={`text-2xl font-bold ${textColor}`}>{value}</p>
  </div>
)

const CaseRow = ({ caseItem }: { caseItem: CaseJob }) => {
  const status = statusConfig[caseItem.status]

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <p className="text-sm font-medium text-gray-900 truncate max-w-xs">
          {caseItem.party_names_raw}
        </p>
        {caseItem.party_names_normalized && (
          <p className="text-xs text-gray-500">
            {caseItem.party_names_normalized.abbreviated}
          </p>
        )}
      </td>
      <td className="px-4 py-3">
        <p className="text-sm text-gray-900">
          {caseItem.citation_raw || '-'}
        </p>
        {caseItem.volume_tolerance_applied && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
            Volume differs
          </span>
        )}
      </td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
          {status.icon}
          <span>{status.label}</span>
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center space-x-2">
          {(caseItem.status === 'ambiguous' || caseItem.status === 'awaiting_selection') && (
            <Link
              to={`/case/${caseItem.id}/disambiguate`}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Select
            </Link>
          )}
          {caseItem.westlaw_url && (
            <a
              href={caseItem.westlaw_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gray-600"
              title="View on Westlaw"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
          {caseItem.file_path && (
            <a
              href={`/files/${caseItem.batch_id}/${caseItem.file_name}`}
              className="text-gray-400 hover:text-gray-600"
              title="Download"
            >
              <FileText className="w-4 h-4" />
            </a>
          )}
        </div>
      </td>
    </tr>
  )
}

export default Dashboard
