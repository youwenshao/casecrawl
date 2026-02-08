import { useState, forwardRef, useImperativeHandle } from 'react'
import { Plus, Trash2, AlertCircle } from 'lucide-react'
import { ManualCaseEntry } from '../types'

interface CaseEntryFormProps {
  cases: ManualCaseEntry[]
  onChange: (cases: ManualCaseEntry[]) => void
  maxCases?: number
}

export interface CaseEntryFormRef {
  validateAll: () => boolean
}

const CaseEntryForm = forwardRef<CaseEntryFormRef, CaseEntryFormProps>(
  ({ cases, onChange, maxCases = 100 }, ref) => {
  const [errors, setErrors] = useState<Record<number, string>>({})

  const addCase = () => {
    if (cases.length >= maxCases) {
      return
    }
    onChange([...cases, { party_name: '', citation: '', notes: '' }])
  }

  const removeCase = (index: number) => {
    const newCases = cases.filter((_, i) => i !== index)
    onChange(newCases)
    
    // Clear error for removed case and shift others
    const newErrors: Record<number, string> = {}
    Object.entries(errors).forEach(([key, value]) => {
      const keyNum = parseInt(key)
      if (keyNum < index) {
        newErrors[keyNum] = value
      } else if (keyNum > index) {
        newErrors[keyNum - 1] = value
      }
    })
    setErrors(newErrors)
  }

  const updateCase = (index: number, field: keyof ManualCaseEntry, value: string) => {
    const newCases = cases.map((c, i) => {
      if (i === index) {
        return { ...c, [field]: value }
      }
      return c
    })
    onChange(newCases)

    // Clear error when user types
    if (errors[index]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[index]
        return newErrors
      })
    }
  }

  const validateAll = (): boolean => {
    let isValid = true
    const newErrors: Record<number, string> = {}
    
    cases.forEach((caseEntry, index) => {
      if (!caseEntry.party_name.trim()) {
        newErrors[index] = 'Party name is required'
        isValid = false
      }
    })
    
    setErrors(newErrors)
    return isValid
  }

  // Expose validateAll method via ref
  useImperativeHandle(ref, () => ({
    validateAll
  }))

  return (
    <div className="space-y-4">
      {cases.map((caseEntry, index) => (
        <div
          key={index}
          className={`bg-white border rounded-lg p-4 transition-colors ${
            errors[index] ? 'border-red-300 ring-1 ring-red-300' : 'border-gray-200'
          }`}
        >
          <div className="flex items-start justify-between mb-3">
            <span className="text-sm font-medium text-gray-500">
              Case #{index + 1}
            </span>
            {cases.length > 1 && (
              <button
                onClick={() => removeCase(index)}
                className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                title="Remove case"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="space-y-3">
            {/* Party Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Party Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={caseEntry.party_name}
                onChange={(e) => updateCase(index, 'party_name', e.target.value)}
                placeholder="e.g., Smith v Jones"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors[index] ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors[index] && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {errors[index]}
                </p>
              )}
            </div>

            {/* Citation */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Citation
              </label>
              <input
                type="text"
                value={caseEntry.citation || ''}
                onChange={(e) => updateCase(index, 'citation', e.target.value)}
                placeholder="e.g., [2020] HKCFI 123"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Optional. Supports HK and UK citation formats.
              </p>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <input
                type="text"
                value={caseEntry.notes || ''}
                onChange={(e) => updateCase(index, 'notes', e.target.value)}
                placeholder="Optional notes"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      ))}

      {/* Add Case Button */}
      <button
        onClick={addCase}
        disabled={cases.length >= maxCases}
        className={`w-full py-3 border-2 border-dashed rounded-lg flex items-center justify-center space-x-2 transition-colors ${
          cases.length >= maxCases
            ? 'border-gray-200 text-gray-400 cursor-not-allowed'
            : 'border-gray-300 text-gray-600 hover:border-blue-500 hover:text-blue-600'
        }`}
      >
        <Plus className="w-5 h-5" />
        <span>Add Another Case</span>
      </button>

      {cases.length >= maxCases && (
        <p className="text-sm text-amber-600 text-center">
          Maximum {maxCases} cases allowed per batch
        </p>
      )}
    </div>
  )
})

CaseEntryForm.displayName = 'CaseEntryForm'

export default CaseEntryForm
