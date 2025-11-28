import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/sidebar/Sidebar'
import ChatContainer from './components/chat/ChatContainer'
import ChatInputFixed from './components/chat/ChatInputFixed'
import Header from './components/Header'
import AuthenticationForm from './components/AuthenticationForm'
import TicketForm from './components/forms/TicketForm'
import IntelligentQuestions from './components/forms/IntelligentQuestions'
import { MESSAGE_TYPES } from './utils/constants'
import { useVoice } from './hooks/useVoice'

const App = () => {
  // Voice functionality
  const { speak, stopSpeaking, isSpeaking } = useVoice()
  
  // Session timeout configuration (in minutes) - Easy to modify
  const SESSION_TIMEOUT = 30 // Change this value to adjust session timeout
  const WARNING_MINUTES = 5  // Show warning when this many minutes are left
  
  // Check if session has expired
  const isSessionExpired = () => {
    const lastActivity = localStorage.getItem('nquiry_lastActivity')
    if (!lastActivity) return true
    
    const timeDiff = Date.now() - parseInt(lastActivity)
    return timeDiff > SESSION_TIMEOUT * 60 * 1000 // Convert to milliseconds
  }
  
  // Authentication state - initialize from localStorage if available and not expired
  const [isInitialized, setIsInitialized] = useState(() => {
    const isAuth = localStorage.getItem('nquiry_isInitialized') === 'true'
    if (isAuth && isSessionExpired()) {
      // Session expired, clear localStorage
      localStorage.removeItem('nquiry_isInitialized')
      localStorage.removeItem('nquiry_currentUser')
      localStorage.removeItem('nquiry_customerEmail')
      localStorage.removeItem('nquiry_sessionId')
      localStorage.removeItem('nquiry_lastActivity')
      return false
    }
    return isAuth
  })
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('nquiry_currentUser')
    return saved ? JSON.parse(saved) : null
  })
  const [customerEmail, setCustomerEmail] = useState(() => {
    return localStorage.getItem('nquiry_customerEmail') || ''
  })
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('nquiry_sessionId') || null
  })
  
  // Chat state
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [conversationEnded, setConversationEnded] = useState(false)
  
  // UI state
  const [showTicketForm, setShowTicketForm] = useState(false)
  const [ticketQuery, setTicketQuery] = useState('')
  const [isEscalation, setIsEscalation] = useState(false)
  const [sessionWarningShown, setSessionWarningShown] = useState(false)
  
  // Intelligent ticket creation state
  const [showIntelligentQuestions, setShowIntelligentQuestions] = useState(false)
  const [targetedQuestions, setTargetedQuestions] = useState([])
  const [partialTicketData, setPartialTicketData] = useState({})
  
  // Chat history state
  const [chatHistory, setChatHistory] = useState([])
  const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0)
  
  // Download state
  const [downloadableTicket, setDownloadableTicket] = useState(null)
  const [showDownloads, setShowDownloads] = useState(false)

  // Generate session ID utility
  const generateSessionId = () => {
    return Date.now().toString() + '-' + Math.random().toString(36).substr(2, 9)
  }

  // Utility function to get current time in IST
  const getISTTimestamp = () => {
    return new Date().toLocaleTimeString('en-IN', { 
      timeZone: 'Asia/Kolkata',
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  // Update last activity timestamp
  const updateLastActivity = useCallback(() => {
    localStorage.setItem('nquiry_lastActivity', Date.now().toString())
  }, [])

  // Auto logout function
  const autoLogout = useCallback(() => {
    console.log('Session expired - auto logging out')
    handleLogout()
    setError('Your session has expired due to inactivity. Please log in again.')
  }, [])

  // Check session expiry periodically
  useEffect(() => {
    if (!isInitialized) return

    const checkSession = () => {
      if (isSessionExpired()) {
        autoLogout()
        return
      }

      // Check if session is expiring soon (5 minutes left)
      const lastActivity = localStorage.getItem('nquiry_lastActivity')
      if (lastActivity) {
        const timeDiff = Date.now() - parseInt(lastActivity)
        const timeLeft = SESSION_TIMEOUT * 60 * 1000 - timeDiff
        const minutesLeft = Math.floor(timeLeft / (60 * 1000))

        // Show warning if WARNING_MINUTES or less left and warning hasn't been shown
        if (minutesLeft <= WARNING_MINUTES && minutesLeft > 0 && !sessionWarningShown) {
          setSessionWarningShown(true)
          setError(`⚠️ Your session will expire in ${minutesLeft} minute(s). Please interact with the app to extend your session.`)
          
          // Clear the warning after 10 seconds
          setTimeout(() => {
            setError(null)
          }, 10000)
        }

        // Reset warning flag if user has more than (WARNING_MINUTES + 5) minutes left
        if (minutesLeft > (WARNING_MINUTES + 5) && sessionWarningShown) {
          setSessionWarningShown(false)
        }
      }
    }

    // Check session every minute
    const interval = setInterval(checkSession, 60000)

    // Update activity on user interactions
    const updateActivity = () => {
      updateLastActivity()
      // Reset session warning when user is active
      if (sessionWarningShown) {
        setSessionWarningShown(false)
        setError(null)
      }
    }
    
    // Add event listeners for user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    events.forEach(event => {
      document.addEventListener(event, updateActivity, true)
    })

    // Cleanup
    return () => {
      clearInterval(interval)
      events.forEach(event => {
        document.removeEventListener(event, updateActivity, true)
      })
    }
  }, [isInitialized, autoLogout, updateLastActivity, sessionWarningShown])

  // Update activity when app initializes
  useEffect(() => {
    if (isInitialized) {
      updateLastActivity()
    }
  }, [isInitialized, updateLastActivity])

  // Function to reload current conversation from backend
  const reloadCurrentConversation = async () => {
    if (!currentUser?.email || !sessionId) return
    
    try {
      // Get latest conversation for current session
      const response = await fetch(`http://localhost:8000/api/chat/history/${currentUser.email}`)
      if (response.ok) {
        const data = await response.json()
        if (data.history && Array.isArray(data.history)) {
          // Filter messages for current session and convert to UI format (exclude feedback messages)
          const sessionMessages = data.history
            .filter(msg => msg.session_id === sessionId && !msg.message?.startsWith('[FEEDBACK]'))
            .map((msg, index) => ({
              id: Date.now() + index,
              type: msg.role === 'user' ? MESSAGE_TYPES.USER : MESSAGE_TYPES.BOT,
              content: msg.message,
              timestamp: new Date(msg.timestamp).toLocaleTimeString('en-IN', { 
                timeZone: 'Asia/Kolkata',
                hour: '2-digit', 
                minute: '2-digit' 
              })
            }))
          
          setMessages(sessionMessages)
        }
      }
    } catch (error) {
      console.error('Failed to reload conversation:', error)
    }
  }

  // Utility function to get current date/time in IST
  const getISTDateTime = () => {
    return new Date().toLocaleString('en-IN', { 
      timeZone: 'Asia/Kolkata'
    })
  }

  const handleInitialize = async (email) => {
    try {
      setIsLoading(true)
      
      // IMPORTANT: Clear all previous user data when switching users
      setMessages([])
      setChatHistory([])
      setError(null)
      setConversationEnded(false)
      setShowTicketForm(false)
      setTicketQuery('')
      setIsEscalation(false)
      setDownloadableTicket(null)
      setShowDownloads(false)
      setShowIntelligentQuestions(false)
      setTargetedQuestions([])
      setPartialTicketData({})
      
      // Set new user info
      setCustomerEmail(email)
      
      // Call backend initialization API using chatService
      const { chatService } = await import('./services/chatService')
      const response = await chatService.initializeProcessor(email)
      
      console.log('Backend initialization response:', response)
      
      setIsInitialized(true)
      // Store the full organization data from the backend
      setCurrentUser(response.organization_data || { email: email })
      
      // Generate new session ID for this login session
      const newSessionId = generateSessionId()
      setSessionId(newSessionId)
      console.log('🆔 Generated new session ID:', newSessionId)
      
      // Store in localStorage
      localStorage.setItem('nquiry_isInitialized', 'true')
      localStorage.setItem('nquiry_currentUser', JSON.stringify(response.organization_data || { email: email }))
      localStorage.setItem('nquiry_customerEmail', email)
      localStorage.setItem('nquiry_sessionId', newSessionId)
      localStorage.setItem('nquiry_lastActivity', Date.now().toString()) // Set initial activity timestamp
      
      // Trigger sidebar refresh for new user
      setSidebarRefreshTrigger(prev => prev + 1)
      
    } catch (error) {
      console.error('Failed to initialize backend:', error)
      setError(`Failed to initialize: ${error.message}`)
      
      // For now, still allow local initialization even if backend fails
      setIsInitialized(true)
      setCurrentUser({ email: email })
      
      // Generate session ID even on fallback
      const newSessionId = generateSessionId()
      setSessionId(newSessionId)
      console.log('🆔 Generated new session ID (fallback):', newSessionId)
      
      // Store in localStorage even on fallback
      localStorage.setItem('nquiry_isInitialized', 'true')
      localStorage.setItem('nquiry_currentUser', JSON.stringify({ email: email }))
      localStorage.setItem('nquiry_customerEmail', email)
      localStorage.setItem('nquiry_sessionId', newSessionId)
      localStorage.setItem('nquiry_lastActivity', Date.now().toString()) // Set initial activity timestamp
      
      // Still trigger sidebar refresh even on fallback
      setSidebarRefreshTrigger(prev => prev + 1)
      
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    // Reset all state to initial values
    setIsInitialized(false)
    setCurrentUser(null)
    setCustomerEmail('')
    setSessionId(null) // Clear session ID on logout
    setMessages([])
    setChatHistory([])
    setIsLoading(false)
    setError(null)
    setConversationEnded(false)
    setShowTicketForm(false)
    setTicketQuery('')
    setIsEscalation(false)
    setDownloadableTicket(null)
    setShowDownloads(false)
    setShowIntelligentQuestions(false)
    setTargetedQuestions([])
    setPartialTicketData({})
    setSidebarRefreshTrigger(prev => prev + 1)
    
    // Clear localStorage
    localStorage.removeItem('nquiry_isInitialized')
    localStorage.removeItem('nquiry_currentUser')
    localStorage.removeItem('nquiry_customerEmail')
    localStorage.removeItem('nquiry_sessionId')
    localStorage.removeItem('nquiry_lastActivity') // Clear activity timestamp
    
    console.log('User logged out - all state and localStorage cleared')
  }

  // Handle feedback submission for continuous learning
  const handleFeedbackSubmitted = (feedbackType, feedbackCategory) => {
    console.log('Feedback submitted:', { feedbackType, feedbackCategory })
    // You can show a toast notification or update UI state here
    // The feedback has already been sent to the backend by FeedbackButtons component
  }

  const handleAudioToggleForMessage = useCallback((messageId, enabled) => {
    // For now, we'll use individual message audio settings
    // In the future, this could store per-message audio preferences
    console.log(`Audio ${enabled ? 'enabled' : 'disabled'} for message ${messageId}`)
    // Optionally store per-message preferences in localStorage or state
  }, [])

  // Persist authentication state to localStorage
  useEffect(() => {
    localStorage.setItem('nquiry_isInitialized', isInitialized.toString())
  }, [isInitialized])

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem('nquiry_currentUser', JSON.stringify(currentUser))
    } else {
      localStorage.removeItem('nquiry_currentUser')
    }
  }, [currentUser])

  useEffect(() => {
    localStorage.setItem('nquiry_customerEmail', customerEmail)
  }, [customerEmail])

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('nquiry_sessionId', sessionId)
    } else {
      localStorage.removeItem('nquiry_sessionId')
    }
  }, [sessionId])

  // Restore conversation on page refresh if user is authenticated
  useEffect(() => {
    if (isInitialized && currentUser?.email && sessionId) {
      reloadCurrentConversation()
      setSidebarRefreshTrigger(prev => prev + 1)
    }
  }, []) // Run only once on mount

  const handleSendMessage = async (message, images = []) => {
    if (!message.trim() && (!images || images.length === 0)) return

    // Clear downloads section when sending a new message (unless it's a ticket confirmation)
    const isTicketRequest = /^(yes|y|yeah|yep|yes create|create ticket|create|ticket|yes please|yes pls|sure|okay|ok|confirm|proceed|go ahead|create support ticket|create a support ticket|do it)$/i.test(message.trim())
    
    if (!isTicketRequest) {
      // Clear downloads when user sends a new query
      setShowDownloads(false)
      setDownloadableTicket(null)
    }

    // Add user message to chat immediately for better UX
    const userMessage = {
      id: Date.now(),
      type: MESSAGE_TYPES.USER,
      content: message,
      timestamp: getISTTimestamp(),
      images: images
    }
    setMessages(prev => [...prev, userMessage])

    setIsLoading(true)
    setError(null)

    try {
      // Add loading message with streaming indicator
      const loadingMessageId = Date.now() + 1
      const loadingMessage = {
        id: loadingMessageId,
        type: MESSAGE_TYPES.BOT,
        content: '🤖 Nquiry is thinking...',
        timestamp: getISTTimestamp(),
        isLoading: true
      }
      setMessages(prev => [...prev, loadingMessage])

      // Call chat API using chatService with streaming
      const { chatService } = await import('./services/chatService')
      await chatService.sendMessageStream(
        message, 
        customerEmail || 'demo_user',
        currentUser, // Pass the full organization data
        sessionId, // Pass the session ID
        images, // Pass the images
        // onStatusUpdate callback
        (statusData) => {
          console.log('Status update:', statusData)
          setMessages(prev => prev.map(msg => 
            msg.id === loadingMessageId 
              ? { ...msg, content: statusData.status }
              : msg
          ))
        },
        // onFinalResponse callback
        (data) => {
          console.log('Final response received:', data)
          
          // Replace loading message with final response
          const finalMessage = {
            id: loadingMessageId,
            type: MESSAGE_TYPES.BOT,
            content: data.response,
            timestamp: getISTTimestamp(),
            isLoading: false
          }
          setMessages(prev => prev.map(msg => 
            msg.id === loadingMessageId ? finalMessage : msg
          ))

          // Handle automatic ticket creation
          if (data.auto_ticket_created && data.ticket_data) {
            console.log('🤖 Automatic ticket was created by AI')
            // The response message already contains the ticket details
            // Just setup downloads
            // Generate comprehensive ticket content with all fields
            const generateTicketContent = (ticketData) => {
              let content = `AUTOMATIC AI TICKET
===================

Ticket ID: ${ticketData.ticket_id}
Category: ${ticketData.category}
Customer: ${ticketData.customer}
Priority: ${ticketData.priority}
Description: ${ticketData.description}

AUTO-POPULATED FIELDS FROM ${ticketData.category} CATEGORY:
`
              
              // Add all additional fields from the ticket data
              Object.entries(ticketData).forEach(([key, value]) => {
                if (!['ticket_id', 'category', 'customer', 'priority', 'description'].includes(key) && value) {
                  // Format field name (convert snake_case to Title Case)
                  const fieldName = key.split('_').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1)
                  ).join(' ')
                  content += `• ${fieldName}: ${value}\n`
                }
              })
              
              content += `\nThis ticket was created automatically using AI analysis.`
              return content
            }
            
            setDownloadableTicket({
              ticket_data: data.ticket_data,
              downloadable_content: generateTicketContent(data.ticket_data),
              filename: `auto_ticket_${data.ticket_data.category}_${Date.now()}.txt`
            })
            setShowDownloads(true)
            setSidebarRefreshTrigger(prev => prev + 1)
            return // Skip other form-related logic
          }

          // Handle targeted questions for intelligent ticket creation
          if (data.needs_questions && data.questions) {
            console.log('❓ AI needs targeted questions for ticket creation')
            // Show a special UI for targeted questions instead of full form
            setShowIntelligentQuestions(true)
            setTargetedQuestions(data.questions)
            setPartialTicketData(data.ticket_data)
            return // Skip other form-related logic
          }

          // Check if backend wants to show ticket form (traditional flow)
          if (data.show_ticket_form) {
            console.log('Backend requested ticket form to be shown')
            setShowTicketForm(true)
            setTicketQuery(message)
            setIsEscalation(false) // Default to non-escalation
          }
        }
      )

      // Refresh sidebar for new conversation
      setSidebarRefreshTrigger(prev => prev + 1)

    } catch (error) {
      console.error('Failed to send message:', error)
      setError(error.message)
      
      // Replace loading message with error message
      setMessages(prev => prev.map(msg => 
        msg.isLoading 
          ? {
              ...msg,
              content: `❌ Sorry, I encountered an error: ${error.message}`,
              isLoading: false
            }
          : msg
      ))
      
      // Error message speech will be handled by useEffect
    } finally {
      setIsLoading(false)
    }
  }

  const handleTicketCreated = (response) => {
    // Extract ticket data from the API response
    const ticketData = response.ticket_data || response;
    
    // Add ticket creation confirmation to chat
    const confirmationMessage = {
      id: Date.now(),
      type: MESSAGE_TYPES.BOT,
      content: `🎫 **Ticket Created Successfully!**

**Ticket ID:** ${ticketData.ticket_id || 'N/A'}
**JIRA Ticket:** ${ticketData.jira_ticket_id || 'N/A'}
**Category:** ${ticketData.category || 'N/A'}
**Customer:** ${ticketData.customer || 'N/A'}

✅ Your support ticket has been created and will be processed by our support team.
📄 Complete ticket details have been generated.

**📥 Downloads Available:**
- Download ticket details
- Download chat transcript

Use the download buttons that will appear below.`,
      timestamp: getISTTimestamp()
    }

    setMessages(prev => [...prev, confirmationMessage])
    setShowTicketForm(false)
    setTicketQuery('')
    setIsEscalation(false)
    setSidebarRefreshTrigger(prev => prev + 1)
    
    // Store download data
    setDownloadableTicket(response)
    setShowDownloads(true)
  }

  const handleTicketCancelled = () => {
    setShowTicketForm(false)
    setTicketQuery('')
    setIsEscalation(false)
  }

  const handleIntelligentQuestionsCompleted = (response) => {
    // Handle the ticket creation response from intelligent questions
    console.log('✅ Intelligent ticket creation completed:', response)
    
    // Add success message to chat
    const successMessage = {
      id: Date.now(),
      type: MESSAGE_TYPES.BOT,
      content: response.message || 'Ticket created successfully using intelligent analysis!',
      timestamp: getISTTimestamp()
    }
    setMessages(prev => [...prev, successMessage])
    
    // Setup downloads if available
    if (response.downloadable_content) {
      setDownloadableTicket(response)
      setShowDownloads(true)
    }
    
    // Close the questions dialog
    setShowIntelligentQuestions(false)
    setTargetedQuestions([])
    setPartialTicketData({})
    
    // Refresh sidebar
    setSidebarRefreshTrigger(prev => prev + 1)
  }

  const handleIntelligentQuestionsCancelled = () => {
    setShowIntelligentQuestions(false)
    setTargetedQuestions([])
    setPartialTicketData({})
    
    // Add cancellation message
    const cancelMessage = {
      id: Date.now(),
      type: MESSAGE_TYPES.BOT,
      content: "No problem! If you need assistance later, just let me know and I'll be happy to help create a ticket for you.",
      timestamp: getISTTimestamp()
    }
    setMessages(prev => [...prev, cancelMessage])
  }

  const downloadTicketDetails = () => {
    if (!downloadableTicket) return
    
    const content = downloadableTicket.downloadable_content || 'No ticket content available'
    const filename = downloadableTicket.filename || 'ticket_details.txt'
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const downloadChatTranscript = async () => {
    try {
      // Generate transcript from current conversation messages
      if (!messages || messages.length === 0) {
        setError('No conversation to download')
        return
      }
      
      // Generate transcript content
      const transcriptLines = []
      transcriptLines.push("NQUIRY CHAT TRANSCRIPT")
      transcriptLines.push("=".repeat(50))
      transcriptLines.push("")
      transcriptLines.push(`Generated: ${getISTDateTime()}`)
      transcriptLines.push(`Customer: ${customerEmail || 'demo_user'}`)
      transcriptLines.push(`Session Messages: ${messages.length}`)
      transcriptLines.push("")
      transcriptLines.push("CONVERSATION LOG:")
      transcriptLines.push("-".repeat(30))
      transcriptLines.push("")
      
      // Add each message from current conversation
      messages.forEach((message, index) => {
        const role = message.type === 'user' ? 'USER' : 'NQUIRY'
        const icon = message.type === 'user' ? '👤' : '🤖'
        const timestamp = message.timestamp || ''
        
        transcriptLines.push(`[${timestamp}] ${icon} ${role}:`)
        
        // Clean content of markdown for plain text
        let content = message.content || ''
        content = content.replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold
        content = content.replace(/\*([^*]+)\*/g, '$1') // Remove italic
        content = content.replace(/#{1,6}\s?/g, '') // Remove headers
        content = content.replace(/`([^`]+)`/g, '$1') // Remove code formatting
        
        // Split long responses into multiple lines for readability
        const lines = content.split('\n')
        lines.forEach(line => {
          if (line.trim()) {
            transcriptLines.push(`    ${line.trim()}`)
          }
        })
        
        transcriptLines.push("") // Empty line between messages
      })
      
      const transcriptContent = transcriptLines.join('\n')
      const filename = `chat_transcript_${customerEmail?.replace('@', '_at_') || 'demo_user'}_${new Date().toISOString().slice(0, 19).replace(/:/g, '')}.txt`
      
      // Download the file
      const blob = new Blob([transcriptContent], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
    } catch (error) {
      console.error('Error downloading chat transcript:', error)
      setError('Failed to download chat transcript')
    }
  }

  const clearDownloads = () => {
    setDownloadableTicket(null)
    setShowDownloads(false)
    setShowIntelligentQuestions(false)
    setTargetedQuestions([])
    setPartialTicketData({})
  }

  const handleNewConversation = () => {
    setMessages([])
    setConversationEnded(false)
    setShowTicketForm(false)
    setTicketQuery('')
    setIsEscalation(false)
    setError(null)
    setShowIntelligentQuestions(false)
    setTargetedQuestions([])
    setPartialTicketData({})
  }

  const handleLoadConversation = (conversation) => {
    // Remove any potential duplicates by checking message content and timestamp
    const uniqueMessages = []
    const seenMessages = new Set()
    
    conversation.messages?.forEach(msg => {
      // Create a unique key based on content and type (ignore exact timestamp due to small differences)
      const key = `${msg.type}-${msg.content.substring(0, 100)}`
      
      if (!seenMessages.has(key)) {
        seenMessages.add(key)
        uniqueMessages.push(msg)
      }
    })
    
    setMessages(uniqueMessages)
    setConversationEnded(false)
    setShowTicketForm(false)
    setError(null)
  }

  // Show authentication form if not initialized
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
        <Header />
        <AuthenticationForm 
          onInitialize={handleInitialize}
          isLoading={isLoading}
          error={error}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar
        currentUser={currentUser}
        onNewConversation={handleNewConversation}
        onLoadConversation={handleLoadConversation}
        refreshTrigger={sidebarRefreshTrigger}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <Header user={currentUser} onLogout={handleLogout} />
        
        {/* Chat Container */}
        <ChatContainer 
          messages={messages}
          isLoading={isLoading}
          userId={customerEmail}
          sessionId={sessionId}
          onFeedbackSubmitted={handleFeedbackSubmitted}
          audioEnabled={true}
          onAudioToggleForMessage={handleAudioToggleForMessage}
        />

        {/* Chat Input */}
        {showTicketForm && (
          <TicketForm
            query={ticketQuery}
            isEscalation={isEscalation}
            customerEmail={customerEmail}
            chatHistory={messages}
            onTicketCreated={handleTicketCreated}
            onCancel={handleTicketCancelled}
          />
        )}

        {/* Intelligent Questions for Automatic Ticket Creation */}
        {showIntelligentQuestions && (
          <IntelligentQuestions
            questions={targetedQuestions}
            originalQuery={ticketQuery}
            partialTicketData={partialTicketData}
            customerEmail={customerEmail}
            onCompleted={handleIntelligentQuestionsCompleted}
            onCancel={handleIntelligentQuestionsCancelled}
          />
        )}

        {/* Downloads Section */}
        {showDownloads && downloadableTicket && (
          <div className="p-6 bg-green-50 border-t border-green-200">
            <div className="max-w-4xl mx-auto">
              <h3 className="text-lg font-semibold text-green-800 mb-4">📥 Downloads</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={downloadTicketDetails}
                  className="flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg transition-colors duration-200"
                >
                  <span>📄</span>
                  <span>Download Ticket Details</span>
                </button>
                
                <button
                  onClick={downloadChatTranscript}
                  className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg transition-colors duration-200"
                >
                  <span>💬</span>
                  <span>Download Chat Transcript</span>
                </button>
                
                <button
                  onClick={clearDownloads}
                  className="flex items-center justify-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-3 rounded-lg transition-colors duration-200"
                >
                  <span>✅</span>
                  <span>Clear Downloads</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Chat Input */}
        {!conversationEnded && (
          <ChatInputFixed
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            disabled={isLoading}
          />
        )}

        {/* Conversation Ended Message */}
        {conversationEnded && messages.length > 0 && (
          <div className="p-6 bg-blue-50 border-t border-blue-200">
            <div className="max-w-4xl mx-auto text-center">
              <p className="text-blue-700">
                💬 This conversation has ended. Use the sidebar to start a new conversation if you have more questions!
              </p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border-t border-red-200">
            <div className="max-w-4xl mx-auto">
              <p className="text-red-700">❌ {error}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App