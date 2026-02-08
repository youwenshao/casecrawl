import { Routes, Route, Link } from 'react-router-dom'
import { FileUp, LayoutDashboard, Settings } from 'lucide-react'
import BatchUpload from './pages/BatchUpload'
import Dashboard from './pages/Dashboard'
import Disambiguation from './pages/Disambiguation'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">CC</span>
                </div>
                <span className="text-xl font-semibold text-gray-900">CaseCrawl</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/"
                className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100"
              >
                <FileUp className="w-4 h-4" />
                <span>Upload</span>
              </Link>
              <Link
                to="/dashboard"
                className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<BatchUpload />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/batch/:batchId" element={<Dashboard />} />
          <Route path="/case/:caseId/disambiguate" element={<Disambiguation />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
