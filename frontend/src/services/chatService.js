import api from './api'

export const chatService = {
  // Send a message to the chat API
  sendMessage: async (message, userId = 'demo_user', organizationData = null, sessionId = null, images = null) => {
    try {
      const requestData = {
        message,
        user_id: userId,
        organization_data: organizationData,
        timestamp: new Date().toISOString()
      }
      
      // Add session_id if provided
      if (sessionId) {
        requestData.session_id = sessionId
      }
      
      // Add images if provided
      if (images && images.length > 0) {
        requestData.images = images.map(img => ({
          base64: img.base64,
          type: img.type,
          name: img.name,
          size: img.size
        }))
      }
      
      const response = await api.post('/chat', requestData)
      return response.data
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    }
  },

  // Get chat history for a user
  getChatHistory: async (userId = 'demo_user') => {
    try {
      const response = await api.get(`/chat/history/${userId}`)
      return response.data
    } catch (error) {
      console.error('Error getting chat history:', error)
      throw error
    }
  },

  // Clear chat history for a user
  clearChatHistory: async (userId = 'demo_user') => {
    try {
      const response = await api.delete(`/chat/history/${userId}`)
      return response.data
    } catch (error) {
      console.error('Error clearing chat history:', error)
      throw error
    }
  },

  // Initialize the query processor
  initializeProcessor: async (customerEmail) => {
    try {
      const response = await api.post('/chat/initialize', {
        customer_email: customerEmail
      })
      return response.data
    } catch (error) {
      console.error('Error initializing processor:', error)
      throw error
    }
  },

  // Create support ticket
  createTicket: async (ticketData) => {
    try {
      const response = await api.post('/tickets/create', {
        original_query: ticketData.original_query,
        customer_email: ticketData.customer_email,
        priority: ticketData.priority,
        area_affected: ticketData.area_affected,
        version_affected: ticketData.version_affected,
        environment: ticketData.environment,
        description: ticketData.description,
        is_escalation: ticketData.is_escalation || false
      })
      return response.data
    } catch (error) {
      console.error('Error creating ticket:', error)
      throw error
    }
  },

  // Get ticket details
  getTicket: async (ticketId) => {
    try {
      const response = await api.get(`/tickets/${ticketId}`)
      return response.data
    } catch (error) {
      console.error('Error getting ticket:', error)
      throw error
    }
  },

  // Get all tickets
  getTickets: async (userId = null) => {
    try {
      const response = await api.get('/tickets', {
        params: userId ? { user_id: userId } : {}
      })
      return response.data
    } catch (error) {
      console.error('Error getting tickets:', error)
      throw error
    }
  },

  // Get chat transcript for download
  getChatTranscript: async (userId = 'demo_user') => {
    try {
      const response = await api.get(`/chat/transcript/${userId}`)
      return response.data
    } catch (error) {
      console.error('Error getting chat transcript:', error)
      throw error
    }
  },

  // Get ticket fields for a specific category
  getTicketFields: async (category) => {
    try {
      const response = await api.get(`/tickets/fields/${category}`)
      return response.data
    } catch (error) {
      console.error('Error getting ticket fields:', error)
      throw error
    }
  },

  // Preview ticket category for a query
  previewTicketCategory: async (query, customerEmail) => {
    try {
      const response = await api.post('/tickets/preview', {
        query,
        customer_email: customerEmail
      })
      return response.data
    } catch (error) {
      console.error('Error previewing ticket category:', error)
      throw error
    }
  },

  // Get available organizations/users
  getUsers: async () => {
    try {
      const response = await api.get('/users')
      return response.data
    } catch (error) {
      console.error('Error getting users:', error)
      throw error
    }
  },

  // Get specific user information
  getUser: async (userId) => {
    try {
      const response = await api.get(`/users/${userId}`)
      return response.data
    } catch (error) {
      console.error('Error getting user:', error)
      throw error
    }
  },

  // Health check for system status
  healthCheck: async () => {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      console.error('Error checking health:', error)
      throw error
    }
  }
}

export default chatService