import React, { useState } from 'react'

const AuthenticationForm = ({ onInitialize, isLoading, error }) => {
  const [email, setEmail] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (email.trim()) {
      onInitialize(email.trim())
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && email.trim()) {
      handleSubmit(e)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-500 to-green-500 rounded-2xl flex items-center justify-center mb-6">
            <span className="text-2xl text-white font-bold">N</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Nquiry
          </h2>
          <p className="text-gray-600 mb-8">
            Your intelligent query assistant
          </p>
        </div>

        {/* Authentication Card */}
        <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              🔐 Customer Authentication
            </h3>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Customer Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="your.email@company.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                disabled={isLoading}
                required
              />
              <p className="text-xs text-gray-500 mt-2">
                Press enter after typing your email to initialize Nquiry
              </p>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">❌ {error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={!email.trim() || isLoading}
              className="w-full bg-gradient-to-r from-blue-500 to-green-500 text-white py-3 px-4 rounded-lg font-medium hover:from-blue-600 hover:to-green-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Initializing Nquiry...
                </>
              ) : (
                'Initialize Nquiry'
              )}
            </button>
          </form>

          {/* Help Text */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">
              💡 What happens next?
            </h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Your credentials will be used for role-based access</li>
              <li>• nQuiry will initialize with your organization data</li>
              <li>• You'll have access to personalized assistance</li>
            </ul>
          </div>
        </div>

        {/* Example Queries Preview */}
        <div className="bg-gray-50 p-6 rounded-xl">
          <h4 className="font-medium text-gray-900 mb-3">
            🎯 Example Queries You Can Ask:
          </h4>
          <div className="grid grid-cols-1 gap-2 text-sm text-gray-600">
            <div className="flex items-center">
              <span className="text-blue-500 mr-2">•</span>
              How do I reset my password?
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">•</span>
              What are the system requirements?
            </div>
            <div className="flex items-center">
              <span className="text-purple-500 mr-2">•</span>
              How to configure MFA settings?
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthenticationForm