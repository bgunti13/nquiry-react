import React, { useState } from 'react'
import { X, MessageSquare, Zap, ArrowRight } from 'lucide-react'
import axios from 'axios'

const IntelligentQuestions = ({ 
  questions, 
  originalQuery,
  partialTicketData,
  customerEmail,
  onCompleted,
  onCancel
}) => {
  const [answers, setAnswers] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleAnswerChange = (questionIndex, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionIndex]: value
    }))
  }

  const handleSubmit = async () => {
    // Validate that all questions are answered
    const unansweredQuestions = questions.filter((_, index) => !answers[index]?.trim())
    
    if (unansweredQuestions.length > 0) {
      setError(`Please answer all questions before proceeding.`)
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // Convert answers to a structured format
      const structuredAnswers = {}
      questions.forEach((question, index) => {
        const answer = answers[index]?.trim()
        if (answer) {
          // Create field names from questions
          const fieldName = question.toLowerCase()
            .replace(/[^a-z0-9\s]/g, '')
            .replace(/\s+/g, '_')
          structuredAnswers[fieldName] = answer
        }
      })

      // Call the API to complete ticket creation with answers
      const response = await axios.post('http://localhost:8000/api/tickets/create-with-answers', {
        original_query: originalQuery,
        customer_email: customerEmail,
        answers: structuredAnswers,
        analysis: partialTicketData
      })

      if (response.data.status === 'success') {
        onCompleted(response.data)
      } else {
        setError(response.data.message || 'Failed to create ticket')
      }

    } catch (error) {
      console.error('Error creating ticket with answers:', error)
      setError(error.response?.data?.message || 'Error creating ticket. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4 text-white">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="bg-white bg-opacity-20 p-2 rounded-full">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Intelligent Ticket Creation</h2>
                <p className="text-blue-100 text-sm">Just a few quick questions to create your ticket</p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {/* Progress indicator */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>Quick Questions</span>
              <span>{Object.keys(answers).length} of {questions.length} answered</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                style={{ width: `${(Object.keys(answers).length / questions.length) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Original Query Display */}
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <div className="flex items-start space-x-3">
              <MessageSquare className="w-5 h-5 text-gray-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Your Original Query:</p>
                <p className="text-gray-900">{originalQuery}</p>
              </div>
            </div>
          </div>

          {/* AI Analysis Summary */}
          {partialTicketData && (
            <div className="bg-blue-50 p-4 rounded-lg mb-6">
              <h3 className="text-sm font-medium text-blue-800 mb-2">🤖 AI Analysis Complete</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {partialTicketData.category && (
                  <div>
                    <span className="text-blue-600 font-medium">Category:</span>
                    <span className="ml-2 text-gray-900">{partialTicketData.category}</span>
                  </div>
                )}
                {partialTicketData.priority && (
                  <div>
                    <span className="text-blue-600 font-medium">Priority:</span>
                    <span className="ml-2 text-gray-900">{partialTicketData.priority}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Questions */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Please provide the following information:</h3>
            
            {questions.map((question, index) => (
              <div key={index} className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  {index + 1}. {question}
                </label>
                <textarea
                  value={answers[index] || ''}
                  onChange={(e) => handleAnswerChange(index, e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="3"
                  placeholder="Type your answer here..."
                />
              </div>
            ))}
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              All information provided will be included in your support ticket
            </div>
            <div className="flex space-x-3">
              <button
                onClick={onCancel}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting || Object.keys(answers).length < questions.length}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    <span>Creating Ticket...</span>
                  </>
                ) : (
                  <>
                    <span>Create Ticket</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default IntelligentQuestions