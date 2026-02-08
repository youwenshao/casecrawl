import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { 
  Keyboard, 
  Check, 
  AlertCircle, 
  Upload,
  Loader2,
  Info
} from 'lucide-react'
import CaseEntryForm, { CaseEntryFormRef } from '../components/CaseEntryForm'
import { createManualBatch } from '../utils/api'
import { ManualCaseEntry } from '../types'

const ManualEntry = () => {
  const navigate = useNavigate()
  const [cases, setCases] = useState<ManualCaseEntry[]>([
    { party_name: '', citation: '', notes: '' }
  ])
  const [autoDownload, setAutoDownload] = useState(true)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const formRef = useRef<CaseEntryFormRef>(null)

  const submitMutation = useMutation({
    mutationFn: createManualBatch,
    onSuccess: (data) => {
      navigate(`/batch/${data.batch_id}`)
    },
  })

  const validateForm = (): boolean => {
    const errors: string[] = []
    
    // Check if we have at least one case
    if (cases.length === 0) {
      errors.push('Please add at least one case')
    }
    
    // Validate each case has party name
    cases.forEach((caseEntry, index) => {
      if (!caseEntry.party_name.trim()) {
        errors.push(`Case #${index + 1}: Party name is required`)
      }
    })
    
    setValidationErrors(errors)
    return errors.length === 0
  }

  const handleSubmit = () => {
    if (!validateForm()) {
      return
    }

    // Filter out empty cases and clean up data
    const validCases = cases
      .filter(c => c.party_name.trim())
      .map(c => ({
        party_name: c.party_name.trim(),
        citation: c.citation?.trim() || undefined,
        notes: c.notes?.trim() || undefined,
      }))

    submitMutation.mutate({
      cases: validCases,
      auto_download_exact_matches: autoDownload,
    })
  }

  const handleCasesChange = useCallback((newCases: ManualCaseEntry[]) => {
    setCases(newCases)
    if (validationErrors.length > 0) {
      setValidationErrors([])
    }
  }, [validationErrors.length])

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Enter Cases Manually</h1>
        <p className="text-gray-600">
          Enter case information directly without uploading a file
        </p>
      </div>

      {/* Entry Method Toggle */}
      <div className="mb-8 bg-gray-100 rounded-lg p-1 flex">
        <button
          onClick={() => navigate('/')}
          className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
        >
          <Upload className="w-4 h-4" />
          <span>File Upload</span>
        </button>
        <button
          className="flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md bg-white text-sm font-medium text-blue-600 shadow-sm"
        >
          <Keyboard className="w-4 h-4" />
          <span>Manual Entry</span>
        </button>
      </div>

      {/* Info Card */}
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-blue-900">How it works</h3>
            <ul className="mt-1 text-sm text-blue-700 space-y-1">
              <li>• Enter party names (required) and citations (optional)</li>
              <li>• Add up to 100 cases per batch</li>
              <li>• Cases will be processed immediately after submission</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Case Entry Form */}
      <CaseEntryForm
        ref={formRef}
        cases={cases}
        onChange={handleCasesChange}
        maxCases={100}
      />

      {/* Options */}
      <div className="mt-6 bg-white rounded-lg border border-gray-200 p-4">
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="checkbox"
            checked={autoDownload}
            onChange={(e) => setAutoDownload(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">
            Auto-download exact matches
          </span>
        </label>
        <p className="text-xs text-gray-500 mt-1 ml-7">
          Automatically download cases with exact citation matches
        </p>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <h4 className="text-sm font-medium text-red-800">
              Please fix the following errors:
            </h4>
          </div>
          <ul className="ml-7 text-sm text-red-700 space-y-1">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Submit Error */}
      {submitMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-sm text-red-700">
            {submitMutation.error instanceof Error 
              ? submitMutation.error.message 
              : 'Failed to create batch. Please try again.'}
          </p>
        </div>
      )}

      {/* Submit Button */}
      <div className="mt-6">
        <button
          onClick={handleSubmit}
          disabled={submitMutation.isPending || cases.length === 0}
          className={`
            w-full py-3 px-4 rounded-lg font-medium text-white
            transition-colors duration-200
            ${submitMutation.isPending || cases.length === 0
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
            }
          `}
        >
          {submitMutation.isPending ? (
            <span className="flex items-center justify-center space-x-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Creating Batch...</span>
            </span>
          ) : (
            <span className="flex items-center justify-center space-x-2">
              <Check className="w-5 h-5" />
              <span>Start Processing ({cases.filter(c => c.party_name.trim()).length} cases)</span>
            </span>
          )}
        </button>
      </div>

      {/* Citation Format Help */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Supported Citation Formats:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Hong Kong</h4>
            <ul className="space-y-1 text-gray-600 font-mono text-xs">
              <li>[2020] HKCFI 123</li>
              <li>[2019] HKCA 456</li>
              <li>[2021] HKCFA 789</li>
              <li>[2020] 1 HKLRD 100</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 mb-2">United Kingdom</h4>
            <ul className="space-y-1 text-gray-600 font-mono text-xs">
              <li>[2020] UKSC 15</li>
              <li>[2019] UKHL 25</li>
              <li>[2020] EWCA 100</li>
              <li>[2020] 1 WLR 456</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ManualEntry
