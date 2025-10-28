import React, { useState, useEffect } from 'react'
import { X, FileText, AlertCircle, Send, Download, Settings } from 'lucide-react'
import axios from 'axios'

const TicketForm = ({ 
  query, 
  isEscalation = false, 
  customerEmail, 
  chatHistory = [], 
  onTicketCreated, 
  onCancel 
}) => {
  const [formData, setFormData] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [error, setError] = useState(null)
  
  // Dynamic ticket configuration state
  const [ticketCategory, setTicketCategory] = useState(null)
  const [requiredFields, setRequiredFields] = useState({})
  const [populatedFields, setPopulatedFields] = useState({})
  const [isLoading, setIsLoading] = useState(true)

  // Preview ticket category and get dynamic fields
  useEffect(() => {
    const previewTicketCategory = async () => {
      try {
        setIsLoading(true)
        const { chatService } = await import('../../services/chatService')
        const response = await chatService.previewTicketCategory(query, customerEmail)
        
        if (response.status === 'success') {
          setTicketCategory(response.category)
          setRequiredFields(response.required_fields || {})
          setPopulatedFields(response.populated_fields || {})
          
          // Initialize form data with default values (handle async description)
          const initialFormData = {}
          
          // Set default values for required fields
          for (const field of Object.keys(response.required_fields || {})) {
            if (field === 'description') {
              // Generate conversation summary asynchronously
              initialFormData[field] = await generateConversationSummary()
            } else {
              initialFormData[field] = ''
            }
          }
          
          // Add some common fields with defaults
          initialFormData.priority = 'Medium'
          
          setFormData(initialFormData)
        } else {
          setError(response.message || 'Failed to determine ticket category')
        }
      } catch (error) {
        console.error('Error previewing ticket category:', error)
        setError('Failed to load ticket configuration')
      } finally {
        setIsLoading(false)
      }
    }
    
    if (query && customerEmail) {
      previewTicketCategory()
    }
  }, [query, customerEmail])

  // Generate conversation summary for ticket description using LLM
  const generateConversationSummary = async () => {
    if (!chatHistory || chatHistory.length === 0) {
      return query || 'No conversation history available.'
    }

    try {
      const response = await axios.post('http://localhost:8000/api/chat/summarize', {
        messages: chatHistory,
        query: query
      })
      
      if (response.data.status === 'success') {
        return response.data.summary
      } else {
        // Fallback to simple summary
        return `Customer inquiry: ${query}\n\nConversation involved ${chatHistory.length} messages discussing technical support requirements.`
      }
    } catch (error) {
      console.error('Error generating conversation summary:', error)
      // Fallback to simple summary
      return `Customer inquiry: ${query}\n\nConversation involved ${chatHistory.length} messages. Please review the full conversation history for complete context.`
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Show confirmation dialog first
    if (!showConfirmation) {
      setShowConfirmation(true)
      return
    }

    // Proceed with actual ticket creation
    setIsSubmitting(true)
    setError(null)

    try {
      // Prepare dynamic form data for submission
      const submissionData = {
        original_query: query,
        customer_email: customerEmail,
        is_escalation: isEscalation,
        // Include all dynamic form fields
        ...formData
      }

      // Call ticket creation API
      const response = await fetch('http://127.0.0.1:8000/api/tickets/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      // Generate JIRA-style ticket ID
      const category = result.category || 'GENERAL'
      const jiraTicketId = `${category.substring(0, 4).toUpperCase()}-${Math.floor(Math.random() * 9000) + 1000}`
      
      const ticketData = {
        ...result,
        jira_ticket_id: jiraTicketId
      }

      onTicketCreated(ticketData)

    } catch (error) {
      console.error('Failed to create ticket:', error)
      setError(error.message)
    }
  }

  const handleConfirmCreate = async () => {
    setShowConfirmation(false)
    setIsSubmitting(true)
    setError(null)

    try {
      // Prepare dynamic form data for submission
      const submissionData = {
        original_query: query,
        customer_email: customerEmail,
        is_escalation: isEscalation,
        // Include all dynamic form fields
        ...formData
      }

      // Call ticket creation API
      const response = await fetch('http://127.0.0.1:8000/api/tickets/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      // Generate JIRA-style ticket ID
      const category = result.category || 'GENERAL'
      const jiraTicketId = `${category.substring(0, 4).toUpperCase()}-${Math.floor(Math.random() * 9000) + 1000}`
      
      const ticketData = {
        ...result,
        jira_ticket_id: jiraTicketId
      }

      onTicketCreated(ticketData)

    } catch (error) {
      console.error('Failed to create ticket:', error)
      setError(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelConfirmation = () => {
    setShowConfirmation(false)
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // Render dynamic form field based on field type and configuration
  const renderField = (fieldName, fieldDescription) => {
    const value = formData[fieldName] || ''
    
    // Common input props
    const inputProps = {
      value,
      onChange: (e) => handleChange(fieldName, e.target.value),
      className: "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    }

    // Field-specific rendering
    switch (fieldName.toLowerCase()) {
      case 'priority':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {fieldDescription}
            </label>
            <select {...inputProps}>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Low">Low</option>
              <option value="Highest">Highest</option>
              <option value="Lowest">Lowest</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Select the priority level for this ticket</p>
          </div>
        )
      
      case 'area':
      case 'area_affected':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {fieldDescription}
            </label>
            <select {...inputProps}>
              <option value="Other">Other</option>
              <option value="UI/UX">UI/UX</option>
              <option value="Performance">Performance</option>
              <option value="Integration">Integration</option>
              <option value="Data">Data</option>
              <option value="Security">Security</option>
              <option value="Database">Database</option>
              <option value="Deployment">Deployment</option>
              <option value="Access">Access</option>
              <option value="Monitoring">Monitoring</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Select the area most affected by this issue</p>
          </div>
        )
      
      case 'environment':
      case 'reported_environment':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {fieldDescription}
            </label>
            <select {...inputProps}>
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
              <option value="testing">Testing</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Select the environment where this issue occurs</p>
          </div>
        )
      
      case 'description':
        return (
          <div key={fieldName} className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {fieldDescription}
            </label>
            <textarea
              {...inputProps}
              rows={8}
              placeholder="Modify the description if needed"
            />
            <p className="text-xs text-gray-500 mt-1">Modify the description if needed</p>
          </div>
        )
      
      default:
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {fieldDescription}
            </label>
            <input
              type="text"
              {...inputProps}
              placeholder={`Enter ${fieldDescription.toLowerCase()}`}
            />
            <p className="text-xs text-gray-500 mt-1">Enter the {fieldDescription.toLowerCase()}</p>
          </div>
        )
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="border-t border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto p-6">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-gray-600">Nquiry is thinking...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="border-t border-gray-200 bg-white">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {isEscalation ? '🎫 Escalate to Human Support' : `🎫 Create ${ticketCategory || ''} Support Ticket`}
              </h2>
              <p className="text-sm text-gray-600">
                {isEscalation 
                  ? "I'll help you escalate this to our support team. Please provide the required details below."
                  : `Creating a ${ticketCategory || ''} ticket based on your query. Please provide the required details below.`
                }
              </p>
            </div>
          </div>
          
          {/* Display original query */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-700 mb-1">
              {isEscalation ? 'Escalation Request:' : 'Original Query:'}
            </p>
            <p className="text-gray-900">{query}</p>
            {ticketCategory && (
              <p className="text-sm text-blue-600 mt-2">
                <Settings className="w-4 h-4 inline mr-1" />
                Ticket Category: {ticketCategory}
              </p>
            )}
          </div>

          {/* Show populated fields that will be auto-filled */}
          {Object.keys(populatedFields).length > 0 && (
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm font-medium text-green-700 mb-2">
                ✅ These fields will be auto-populated:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-green-600">
                {Object.entries(populatedFields).map(([key, value]) => (
                  <div key={key}>
                    <strong>{key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> {value}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Dynamic Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {Object.keys(requiredFields).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(requiredFields).map(([fieldName, fieldDescription]) => 
                renderField(fieldName, fieldDescription)
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No additional fields required for this ticket category.</p>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">❌ Error creating ticket: {error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Creating Ticket...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  🎫 Create Ticket
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              ❌ Cancel
            </button>
          </div>
        </form>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4">
            <div className="flex items-center mb-4">
              <AlertCircle className="w-6 h-6 text-orange-500 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">Confirm Ticket Creation</h3>
            </div>
            
            <p className="text-gray-600 mb-6">
              Are you sure you want to create this {ticketCategory || ''} support ticket? 
              This will submit your request to the support team.
            </p>
            
            <div className="flex space-x-3">
              <button
                onClick={handleConfirmCreate}
                disabled={isSubmitting}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2 inline-block"></div>
                    Creating...
                  </>
                ) : (
                  'Yes, Create Ticket'
                )}
              </button>
              
              <button
                onClick={handleCancelConfirmation}
                disabled={isSubmitting}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg font-medium hover:bg-gray-400 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TicketForm