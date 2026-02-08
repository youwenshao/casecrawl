import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Upload, FileSpreadsheet, Check, AlertCircle, Download } from 'lucide-react'
import { createBatch } from '../utils/api'

const BatchUpload = () => {
  const navigate = useNavigate()
  const [autoDownload, setAutoDownload] = useState(true)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => createBatch(file, autoDownload),
    onSuccess: (data) => {
      navigate(`/batch/${data.batch_id}`)
    },
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadedFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  })

  const handleUpload = () => {
    if (uploadedFile) {
      uploadMutation.mutate(uploadedFile)
    }
  }

  const downloadTemplate = () => {
    const csv = 'party_name,citation,notes\n"Smith v Jones","[2020] HKCFI 123","Example case"\n"ABC Ltd v XYZ Corp","[2019] 1 WLR 456",""'
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'casecrawl_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Cases</h1>
        <p className="text-gray-600">
          Upload a CSV or Excel file with case information to begin crawling
        </p>
      </div>

      {/* Template Download */}
      <div className="mb-6 flex justify-center">
        <button
          onClick={downloadTemplate}
          className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          <Download className="w-4 h-4" />
          <span>Download CSV Template</span>
        </button>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <input {...getInputProps()} />
        
        {uploadedFile ? (
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <FileSpreadsheet className="w-8 h-8 text-green-600" />
            </div>
            <p className="text-lg font-medium text-gray-900">{uploadedFile.name}</p>
            <p className="text-sm text-gray-500">
              {(uploadedFile.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <Upload className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop the file here' : 'Drag & drop your file here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to select a file
            </p>
            <p className="text-xs text-gray-400 mt-4">
              Supports CSV, XLSX, XLS
            </p>
          </div>
        )}
      </div>

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

      {/* Upload Button */}
      {uploadedFile && (
        <div className="mt-6">
          <button
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className={`
              w-full py-3 px-4 rounded-lg font-medium text-white
              transition-colors duration-200
              ${uploadMutation.isPending
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
              }
            `}
          >
            {uploadMutation.isPending ? (
              <span className="flex items-center justify-center space-x-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Uploading...</span>
              </span>
            ) : (
              'Start Processing'
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {uploadMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-sm text-red-700">
            {uploadMutation.error instanceof Error 
              ? uploadMutation.error.message 
              : 'Upload failed. Please try again.'}
          </p>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Required CSV Format:</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 font-medium text-gray-700">Column</th>
                <th className="text-left py-2 px-3 font-medium text-gray-700">Description</th>
                <th className="text-left py-2 px-3 font-medium text-gray-700">Example</th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              <tr className="border-b border-gray-100">
                <td className="py-2 px-3 font-mono text-xs">party_name</td>
                <td className="py-2 px-3">Party names (required)</td>
                <td className="py-2 px-3 font-mono text-xs">Smith v Jones</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-2 px-3 font-mono text-xs">citation</td>
                <td className="py-2 px-3">Case citation (optional)</td>
                <td className="py-2 px-3 font-mono text-xs">[2020] HKCFI 123</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-xs">notes</td>
                <td className="py-2 px-3">Optional notes</td>
                <td className="py-2 px-3 font-mono text-xs">-</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default BatchUpload
