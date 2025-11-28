import { useState, useEffect } from 'react'
import chatService from '../services/chatService'

export const useChat = () => {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)

  // Load chat history when user changes - simplified without useCallback
  useEffect(() => {
    const loadHistory = async () => {
      if (currentUser?.email) {
        try {
          const history = await chatService.getChatHistory(currentUser.email)
          const formattedMessages = history.map(msg => ({
            id: msg.id || Date.now() + Math.random(),
            type: msg.role === 'assistant' ? 'bot' : msg.role,
            content: msg.message || msg.content,
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
          }))
          setMessages(formattedMessages.reverse())
        } catch (err) {
          console.error('Failed to load chat history:', err)
          setError('Failed to load chat history')
        }
      }
    }
    
    loadHistory()
  }, [currentUser?.email])

  const sendMessage = async (messageContent) => {
    if (!messageContent.trim()) return

    setIsLoading(true)
    setError(null)

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageContent.trim(),
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])

    // Add a loading message that will be updated with streaming status
    const loadingMessageId = Date.now() + 1
    const initialLoadingMessage = {
      id: loadingMessageId,
      type: 'bot',
      content: '🤖 Nquiry is thinking...',
      timestamp: new Date(),
      isLoading: true
    }
    
    setMessages(prev => [...prev, initialLoadingMessage])

    try {
      await chatService.sendMessageStream(
        messageContent.trim(),
        currentUser?.email || 'demo_user',
        currentUser,
        null,
        null,
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
        (responseData) => {
          console.log('Final response:', responseData)
          // Replace loading message with final response
          setMessages(prev => prev.map(msg => 
            msg.id === loadingMessageId 
              ? { 
                  ...msg, 
                  content: responseData.response || 'No response received',
                  isLoading: false,
                  showTicketForm: responseData.show_ticket_form,
                  autoTicketCreated: responseData.auto_ticket_created,
                  ticketData: responseData.ticket_data
                }
              : msg
          ))
        }
      )

    } catch (err) {
      console.error('Failed to send message:', err)
      setError('Failed to send message. Please try again.')
      
      // Replace loading message with error
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessageId 
          ? { 
              ...msg, 
              content: '❌ Sorry, I encountered an error processing your request. Please try again.',
              isLoading: false
            }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
  }

  const initializeProcessor = async (organizationData) => {
    try {
      setIsLoading(true)
      await chatService.initializeProcessor(organizationData)
      setIsInitialized(true)
      setCurrentUser(organizationData)
      setError(null)
    } catch (err) {
      console.error('Failed to initialize processor:', err)
      setError('Failed to initialize. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const loadChatHistory = async (userId) => {
    try {
      const history = await chatService.getChatHistory(userId)
      const formattedMessages = history.map(msg => ({
        id: msg.id || Date.now() + Math.random(),
        type: msg.role === 'assistant' ? 'bot' : msg.role,
        content: msg.message || msg.content,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
      }))
      setMessages(formattedMessages.reverse())
    } catch (err) {
      console.error('Failed to load chat history:', err)
      setError('Failed to load chat history')
    }
  }

  return {
    messages,
    isLoading,
    error,
    isInitialized,
    currentUser,
    sendMessage,
    clearChat,
    initializeProcessor,
    setCurrentUser,
    loadChatHistory
  }
}

export default useChat