import React, { useState, useEffect } from 'react'
import { 
  ChevronDown, 
  Users, 
  MessageCircle, 
  Trash2, 
  Plus, 
  Settings, 
  Clock,
  Download,
  FileText,
  Ticket,
  Search,
  Calendar,
  User
} from 'lucide-react'
import { MESSAGE_TYPES } from '../../utils/constants'

const Sidebar = ({ 
  currentUser, 
  onNewConversation,
  onLoadConversation,
  refreshTrigger
}) => {
  const [conversations, setConversations] = useState([])
  const [recentTickets, setRecentTickets] = useState([])
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [activeTab, setActiveTab] = useState('conversations') // 'conversations' or 'tickets'
  
  // Search functionality
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredConversations, setFilteredConversations] = useState([])
  const [filteredTickets, setFilteredTickets] = useState([])

  // Function to generate intelligent conversation titles
  const generateConversationTitle = (messages) => {
    if (!messages || messages.length === 0) {
      return 'New Conversation'
    }

    // Find the first meaningful user message (skip greetings)
    const meaningfulMessage = messages.find(msg => {
      if (msg.type !== MESSAGE_TYPES.USER || !msg.content) return false
      
      const content = msg.content.toLowerCase().trim()
      
      // Skip common greetings
      const greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
      if (greetings.includes(content)) return false
      
      // Skip very short messages
      if (content.length < 10) return false
      
      return true
    })

    if (meaningfulMessage) {
      let title = meaningfulMessage.content.trim()
      
      // Extract key topics and generate smart titles
      const content = title.toLowerCase()
      
      // Technical issues
      if (content.includes('error') || content.includes('issue') || content.includes('problem')) {
        if (content.includes('sync')) return '🔄 Sync Issue Help'
        if (content.includes('login') || content.includes('authentication')) return '🔐 Login Problem'
        if (content.includes('deployment')) return '🚀 Deployment Issue'
        if (content.includes('database') || content.includes('db')) return '🗄️ Database Problem'
        if (content.includes('api')) return '🔌 API Issue'
        return '⚠️ Technical Issue'
      }
      
      // Configuration questions
      if (content.includes('how to') || content.includes('configure') || content.includes('setup')) {
        if (content.includes('salesforce')) return '🏢 Salesforce Setup'
        if (content.includes('database')) return '🗄️ Database Configuration'
        if (content.includes('user') || content.includes('account')) return '👥 User Management'
        return '⚙️ Configuration Help'
      }
      
      // Version and update queries
      if (content.includes('version') || content.includes('update') || content.includes('upgrade')) {
        return '📦 Version & Updates'
      }
      
      // Support and ticket requests
      if (content.includes('support') || content.includes('ticket') || content.includes('help')) {
        return '🎫 Support Request'
      }
      
      // Data related
      if (content.includes('data') || content.includes('report')) {
        if (content.includes('sync')) return '📊 Data Sync Query'
        if (content.includes('missing') || content.includes('not showing')) return '📊 Data Missing'
        return '📊 Data Question'
      }
      
      // Account and user management
      if (content.includes('account') || content.includes('user') || content.includes('permission')) {
        return '👥 Account Management'
      }
      
      // General questions
      if (content.includes('what') || content.includes('why') || content.includes('when')) {
        // Extract the main topic after question words
        const words = title.split(' ')
        const topicWords = words.slice(1, 4).join(' ')
        return `❓ ${topicWords.charAt(0).toUpperCase()}${topicWords.slice(1)}`
      }
      
      // Fallback: use first meaningful part of the message
      const words = title.split(' ')
      let shortTitle = words.slice(0, 4).join(' ')
      
      // Remove common stop words from the end
      shortTitle = shortTitle.replace(/\b(the|and|or|but|in|on|at|to|for|of|with|by)\s*$/i, '').trim()
      
      // Capitalize first letter
      shortTitle = shortTitle.charAt(0).toUpperCase() + shortTitle.slice(1)
      
      return shortTitle.length > 35 ? shortTitle.substring(0, 35) + '...' : shortTitle
    }
    
    // If no meaningful message found, try to use the first non-greeting message
    const firstMessage = messages.find(msg => msg.type === MESSAGE_TYPES.USER && msg.content)
    if (firstMessage) {
      const title = firstMessage.content.trim()
      return title.length > 35 ? title.substring(0, 35) + '...' : title
    }
    
    return 'New Conversation'
  }

  // Load conversation history and recent tickets
  useEffect(() => {
    console.log('🔄 Sidebar useEffect triggered:', { 
      currentUser: currentUser?.email, 
      refreshTrigger,
      timestamp: new Date().toISOString()
    });
    
    if (currentUser?.email) {
      console.log('👤 Loading data for user:', currentUser.email);
      // Clear previous user's data first
      console.log('🧹 Clearing previous user data');
      setConversations([])
      setRecentTickets([])
      setSelectedConversation(null)
      
      // Small delay to ensure state is cleared
      setTimeout(() => {
        console.log('📊 Loading new user data for:', currentUser.email);
        loadConversationHistory()
        loadRecentTickets()
      }, 100)
    } else {
      console.log('❌ No user found, clearing all data');
      // If no user, clear all data
      setConversations([])
      setRecentTickets([])
      setSelectedConversation(null)
    }
  }, [currentUser?.email, refreshTrigger]) // Use currentUser.email specifically

  // Search filtering effect
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredConversations(conversations)
      setFilteredTickets(recentTickets)
    } else {
      // Filter conversations
      const filteredConvos = conversations.filter(conversation => 
        conversation.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conversation.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredConversations(filteredConvos)

      // Filter tickets
      const filteredTix = recentTickets.filter(ticket =>
        ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ticket.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ticket.status.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredTickets(filteredTix)
    }
  }, [searchQuery, conversations, recentTickets])

  const loadConversationHistory = async () => {
    try {
      console.log('🔍 Starting loadConversationHistory for user:', currentUser.email);
      
      // Call API to load conversation history - using correct port 8000
      // Add timestamp to prevent caching issues between users
      const timestamp = Date.now()
      const apiUrl = `http://localhost:8000/api/chat/history/${currentUser.email}?_t=${timestamp}`
      console.log('📡 Making API call to:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      })
      console.log('📨 API response status:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json()
        console.log('📋 Chat history response for', currentUser.email, ':', data);
        
        if (data.history && Array.isArray(data.history)) {
          console.log('✅ Found', data.history.length, 'history items for user:', currentUser.email);
          
          // Transform MongoDB individual messages into conversation sessions
          // MongoDB returns: [{"role": "user", "message": "Hello", "timestamp": "..."}, ...]
          // We need to group these into conversations
          
          if (data.history.length === 0) {
            console.log('📭 No messages found for user:', currentUser.email);
            setConversations([]);
            return;
          }
          
          // Group messages into conversations based on session IDs and time gaps (30 minutes)
          const conversations = [];
          let currentConversation = null;
          let conversationId = 1;
          const CONVERSATION_GAP_MINUTES = 30;
          
          for (let i = 0; i < data.history.length; i++) {
            const msg = data.history[i];
            
            // Check if this message has the expected structure
            if (!msg.role || !msg.message) {
              console.warn('⚠️ Skipping malformed message:', msg);
              continue;
            }

            const msgTimestamp = new Date(msg.timestamp);
            
            // Check if we should start a new conversation
            let shouldStartNewConversation = false;
            
            if (!currentConversation) {
              // First message
              shouldStartNewConversation = true;
            } else {
              // Check if session_id changed (different login session)
              if (msg.session_id && currentConversation.session_id && msg.session_id !== currentConversation.session_id) {
                shouldStartNewConversation = true;
              } 
              // Check time gap from last message in current conversation
              else {
                const lastMessage = currentConversation.messages[currentConversation.messages.length - 1];
                const lastTimestamp = new Date(lastMessage.originalTimestamp);
                const timeDiffMinutes = (msgTimestamp - lastTimestamp) / (1000 * 60);
                
                if (timeDiffMinutes > CONVERSATION_GAP_MINUTES) {
                  shouldStartNewConversation = true;
                }
              }
            }
            
            if (shouldStartNewConversation) {
              // Save the previous conversation
              if (currentConversation) {
                conversations.push(currentConversation);
              }
              
              // Start a new conversation
              currentConversation = {
                id: conversationId++,
                title: 'New Conversation', // Will be updated with intelligent title later
                timestamp: msg.timestamp || new Date().toISOString(),
                messageCount: 0,
                lastMessage: '',
                messages: [],
                session_id: msg.session_id || null // Track session ID for conversation grouping
              };
            }
            
            // Format timestamp for display (in IST)
            const formattedTime = msg.timestamp ? 
              new Date(msg.timestamp).toLocaleTimeString('en-IN', { 
                timeZone: 'Asia/Kolkata',
                hour: '2-digit', 
                minute: '2-digit' 
              }) : 
              new Date().toLocaleTimeString('en-IN', { 
                timeZone: 'Asia/Kolkata',
                hour: '2-digit', 
                minute: '2-digit' 
              });
            
            // Skip feedback messages - don't display them in chat history
            if (msg.message && msg.message.startsWith('[FEEDBACK]')) {
              continue;
            }
            
            // Debug: Log every message being processed
            console.log('📝 Processing message:', {
              role: msg.role,
              messageType: msg.role === 'user' ? MESSAGE_TYPES.USER : MESSAGE_TYPES.BOT,
              content: msg.message?.substring(0, 50) + (msg.message?.length > 50 ? '...' : ''),
              timestamp: msg.timestamp,
              session_id: msg.session_id
            });
            
            // Add message to current conversation
            const messageType = msg.role === 'user' ? MESSAGE_TYPES.USER : MESSAGE_TYPES.BOT;
            const messageData = {
              id: Date.now() + Math.random() + i, // Unique ID for the message
              type: messageType,
              content: msg.message,
              timestamp: formattedTime,
              originalTimestamp: msg.timestamp // Keep original timestamp for comparison
            };
            
            // Preserve images if they exist (for user messages)
            if (msg.images && msg.images.length > 0) {
              messageData.images = msg.images;
              console.log('🖼️ Preserving', msg.images.length, 'images for message:', msg.message.substring(0, 50));
            }
            
            currentConversation.messages.push(messageData);
            
            // Debug: Log when message is added to conversation
            console.log(`➕ Added ${messageType} message to conversation:`, {
              messageContent: msg.message?.substring(0, 30) + '...',
              conversationTitle: currentConversation.title?.substring(0, 30) + '...',
              totalMessagesInConv: currentConversation.messages.length
            });
            
            currentConversation.messageCount++;
            currentConversation.lastMessage = msg.message.substring(0, 100) + (msg.message.length > 100 ? '...' : '');
            
            // Always update conversation timestamp to the latest message timestamp
            currentConversation.timestamp = msg.timestamp || new Date().toISOString();
          }
          
          // Don't forget the last conversation
          if (currentConversation) {
            conversations.push(currentConversation);
          }
          
          // Generate intelligent titles for all conversations
          conversations.forEach(conversation => {
            conversation.title = generateConversationTitle(conversation.messages);
          });
          
          // Reverse to show most recent conversations first and limit to 5
          const sortedConversations = conversations.reverse().slice(0, 5);
          
          console.log('🔄 Setting conversations for user', currentUser.email, ':', sortedConversations);
          setConversations(sortedConversations);
          console.log(`✅ Loaded ${sortedConversations.length} conversations from MongoDB for user: ${currentUser.email}`);
        } else {
          console.log('⚠️ No history found in response for user:', currentUser.email, 'using fallback');
          setConversations([]);
        }
      } else {
        console.log('API response not ok, using fallback mock data');
        // Fallback to mock data if API fails
        const mockConversations = [
          {
            id: 1,
            title: "🔄 Salesforce Sync Issue",
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            messageCount: 6,
            lastMessage: "Would you like me to create a support ticket?"
          },
          {
            id: 2,
            title: "📊 Data Missing from Reports",
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
            messageCount: 4,
            lastMessage: "Please check the data configuration"
          },
          {
            id: 3,
            title: "🚀 Database Deployment Help",
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
            messageCount: 8,
            lastMessage: "I'll help you with the deployment process"
          }
        ]
        setConversations(mockConversations)
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error)
      // Fallback to mock data on error
      const mockConversations = [
        {
          id: 1,
          title: "Salesforce accounts sync issue",
          timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
          messageCount: 6,
          lastMessage: "Would you like me to create a support ticket?"
        }
      ]
      setConversations(mockConversations)
    }
  }

  const loadRecentTickets = async () => {
    try {
      // Extract organization from current user
      const organization = getOrganizationFromEmail(currentUser.email)
      console.log('🎫 Loading recent tickets for organization:', organization);
      
      // Call API to load recent tickets for this organization
      // Add timestamp to prevent caching issues between users
      const timestamp = Date.now()
      const apiUrl = `http://127.0.0.1:8000/api/tickets/recent/${organization}?_t=${timestamp}`
      console.log('📡 Making API call to:', apiUrl);
      
      const response = await fetch(apiUrl)
      console.log('📨 Recent tickets API response status:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json()
        console.log('🎫 Recent tickets response:', data);
        // Limit to 5 most recent tickets
        const recentTicketsLimited = (data.tickets || []).slice(0, 5)
        setRecentTickets(recentTicketsLimited)
        console.log(`✅ Loaded ${recentTicketsLimited.length} real tickets for ${organization}`);
      } else {
        console.log('⚠️ API response not ok, using fallback mock data');
        // Fallback to mock data based on organization (limit to 5)
        const mockTickets = getMockTicketsForOrganization(organization).slice(0, 5)
        setRecentTickets(mockTickets)
      }
    } catch (error) {
      console.error('❌ Failed to load recent tickets:', error)
      // Fallback to mock data (limit to 5)
      const organization = getOrganizationFromEmail(currentUser.email)
      const mockTickets = getMockTicketsForOrganization(organization).slice(0, 5)
      setRecentTickets(mockTickets)
    }
  }

  const getOrganizationFromEmail = (email) => {
    if (!email) return 'unknown'
    const domain = email.split('@')[1]?.toLowerCase()
    
    const domainToOrg = {
      'amd.com': 'AMD',
      'novartis.com': 'Novartis', 
      'wdc.com': 'WDC',
      'abbott.com': 'Abbott',
      'abbvie.com': 'AbbVie',
      'amgen.com': 'Amgen'
    }
    
    return domainToOrg[domain] || domain?.split('.')[0]?.toUpperCase() || 'UNKNOWN'
  }

  const getMockTicketsForOrganization = (organization) => {
    const baseTickets = {
      'AMD': [
        {
          id: 'MNHT-7755',
          title: 'CDM Workbench sync configuration',
          status: 'In Progress',
          created: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
          category: 'MNHT',
          priority: 'Medium'
        },
        {
          id: 'COPS-4521',
          title: 'Database refresh for AMD environment',
          status: 'Completed',
          created: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
          category: 'COPS',
          priority: 'High'
        },
        {
          id: 'NOC-3388',
          title: 'Monitoring workflow access request',
          status: 'Open',
          created: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
          category: 'NOC',
          priority: 'Low'
        }
      ],
      'Novartis': [
        {
          id: 'MNLS-9912',
          title: 'Life Sciences data validation issue',
          status: 'In Progress',
          created: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
          category: 'MNLS',
          priority: 'High'
        },
        {
          id: 'COPS-5643',
          title: 'Production deployment for Novartis',
          status: 'Completed',
          created: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
          category: 'COPS',
          priority: 'Medium'
        }
      ]
    }
    
    return baseTickets[organization] || []
  }

  const clearChatHistory = async () => {
    if (currentUser && window.confirm('Are you sure you want to clear all chat history?')) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/chat/history/${currentUser.email}`, {
          method: 'DELETE'
        })
        if (response.ok) {
          setConversations([])
          onNewConversation()
        }
      } catch (error) {
        console.error('Failed to clear chat history:', error)
      }
    }
  }

  const handleConversationClick = (conversation) => {
    console.log('👆 Conversation clicked:', {
      id: conversation.id,
      title: conversation.title,
      messageCount: conversation.messages?.length || 0,
      firstMessage: conversation.messages?.[0]?.content?.substring(0, 30) + '...',
      lastMessage: conversation.messages?.[conversation.messages.length - 1]?.content?.substring(0, 30) + '...'
    });
    
    // Debug: Log each message in the clicked conversation
    conversation.messages?.forEach((msg, index) => {
      console.log(`📋 Conv message ${index + 1}:`, {
        type: msg.type,
        content: msg.content?.substring(0, 40) + '...',
        timestamp: msg.timestamp
      });
    });
    
    setSelectedConversation(conversation.id)
    onLoadConversation(conversation)
  }

  // Utility function to convert UTC timestamp to IST
  const convertToIST = (timestamp) => {
    // Return the date as-is, let browser handle timezone conversion
    return new Date(timestamp);
  }

  const formatTimestamp = (timestamp) => {
    try {
      // Handle different timestamp formats
      let date;
      if (typeof timestamp === 'string') {
        // Handle JIRA timestamp format: 2025-10-09T03:26:18.941-0700
        date = new Date(timestamp);
      } else {
        date = new Date(timestamp);
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid timestamp:', timestamp);
        return 'Invalid Date';
      }
      
      const now = new Date()
      const diffInHours = (now - date) / (1000 * 60 * 60)
      
      if (diffInHours < 1) {
        return `${Math.floor(diffInHours * 60)}m ago`
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)}h ago`
      } else if (diffInHours < 168) { // 7 days
        return `${Math.floor(diffInHours / 24)}d ago`
      } else {
        // Convert to IST for display
        return date.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' })
      }
    } catch (error) {
      console.error('Error formatting timestamp:', error, timestamp);
      return 'Invalid Date';
    }
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'in progress':
        return 'bg-blue-100 text-blue-800'
      case 'open':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'text-red-600'
      case 'medium':
        return 'text-yellow-600'
      case 'low':
        return 'text-green-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Nquiry Assistant</h2>
            <div className="flex items-center space-x-2 mt-1">
              <User className="w-3 h-3 text-gray-500" />
              <p className="text-xs text-gray-600">
                {getOrganizationFromEmail(currentUser?.email)} • {currentUser?.email || 'Not authenticated'}
              </p>
            </div>
          </div>
          <button
            onClick={onNewConversation}
            className="p-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors"
            title="New Conversation"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              console.log('🔄 Manual refresh triggered for user:', currentUser?.email);
              setConversations([]);
              setRecentTickets([]);
              setSelectedConversation(null);
              setTimeout(() => {
                loadConversationHistory();
                loadRecentTickets();
              }, 100);
            }}
            className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200 transition-colors ml-2"
            title="Refresh Data"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('conversations')}
            className={`flex-1 px-3 py-2 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'conversations'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <MessageCircle className="w-4 h-4 inline mr-2" />
            Chats
          </button>
          <button
            onClick={() => setActiveTab('tickets')}
            className={`flex-1 px-3 py-2 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'tickets'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Ticket className="w-4 h-4 inline mr-2" />
            Tickets
          </button>
        </div>

        {/* Search Input */}
        <div className="mt-3 relative">
          <input
            type="text"
            placeholder={`Search ${activeTab === 'conversations' ? 'conversations...' : 'tickets...'}`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 pl-10 text-sm bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'conversations' ? (
          // Conversations Tab - ChatGPT Style
          filteredConversations.length > 0 ? (
            <div className="p-2 space-y-1">
              {filteredConversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => handleConversationClick(conversation)}
                  className={`w-full text-left p-3 rounded-lg transition-all duration-200 group hover:bg-white ${
                    selectedConversation === conversation.id
                      ? 'bg-white shadow-sm border border-gray-200'
                      : 'hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900 truncate flex-1 pr-2 leading-tight">
                      {conversation.title || 'New conversation'}
                    </h4>
                    <span className="text-xs text-gray-500 whitespace-nowrap">
                      {formatTimestamp(conversation.timestamp)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 truncate mb-2">
                    {conversation.lastMessage || 'No messages yet'}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1">
                      <MessageCircle className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {conversation.messageCount || 0}
                      </span>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <Clock className="w-3 h-3 text-gray-400" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center p-6">
              <MessageCircle className="w-12 h-12 text-gray-300 mb-3" />
              <h3 className="text-sm font-medium text-gray-600 mb-1">
                {searchQuery ? 'No conversations found' : 'No conversations yet'}
              </h3>
              <p className="text-xs text-gray-500">
                {searchQuery 
                  ? `No conversations match "${searchQuery}"`
                  : 'Start a new conversation to see your chat history here'
                }
              </p>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700"
                >
                  Clear search
                </button>
              )}
            </div>
          )
        ) : (
          // Tickets Tab - Organization-specific
          <div className="p-2">
            <div className="mb-3 px-2">
              <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                {getOrganizationFromEmail(currentUser?.email)} Recent Tickets
              </h3>
            </div>
            {filteredTickets.length > 0 ? (
              <div className="space-y-1">
                {filteredTickets.map((ticket) => (
                  <div
                    key={ticket.id}
                    className="p-3 rounded-lg bg-white hover:shadow-sm transition-all duration-200 border border-gray-100"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-mono text-blue-600 bg-blue-50 px-2 py-1 rounded">
                            {ticket.id}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(ticket.status)}`}>
                            {ticket.status}
                          </span>
                        </div>
                        <h4 className="text-sm font-medium text-gray-900 leading-tight mb-1">
                          {ticket.title}
                        </h4>
                        <div className="flex items-center space-x-3 text-xs text-gray-500">
                          <div className="flex items-center space-x-1">
                            <Calendar className="w-3 h-3" />
                            <span>{formatTimestamp(ticket.created)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <span className={`font-medium ${getPriorityColor(ticket.priority)}`}>
                              {ticket.priority}
                            </span>
                          </div>
                          <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                            {ticket.category}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-center p-6">
                <Ticket className="w-12 h-12 text-gray-300 mb-3" />
                <h3 className="text-sm font-medium text-gray-600 mb-1">
                  {searchQuery ? 'No tickets found' : 'No recent tickets'}
                </h3>
                <p className="text-xs text-gray-500">
                  {searchQuery 
                    ? `No tickets match "${searchQuery}"`
                    : `No tickets found for ${getOrganizationFromEmail(currentUser?.email)}`
                  }
                </p>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-700"
                  >
                    Clear search
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-white">
        {activeTab === 'conversations' && conversations.length > 0 && !searchQuery && (
          <button
            onClick={clearChatHistory}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear Chat History</span>
          </button>
        )}
        
        {/* Search Results Count */}
        {searchQuery && (
          <div className="text-center text-xs text-gray-500 py-2">
            {activeTab === 'conversations' ? (
              <span>{filteredConversations.length} of {conversations.length} conversations</span>
            ) : (
              <span>{filteredTickets.length} of {recentTickets.length} tickets</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar