import React, { useState, useEffect } from 'react'
import { 
  ChevronDown, 
  Users, 
  MessageCircle, 
  Trash2, 
  Plus, 
  Settings, 
  Clock,
  Volume2,
  VolumeX,
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
  refreshTrigger,
  audioEnabled,
  onAudioToggle
}) => {
  const [conversations, setConversations] = useState([])
  const [recentTickets, setRecentTickets] = useState([])
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [activeTab, setActiveTab] = useState('conversations') // 'conversations' or 'tickets'

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
            }            if (shouldStartNewConversation) {
              // Save the previous conversation
              if (currentConversation) {
                conversations.push(currentConversation);
              }
              
              // Start a new conversation
              const firstUserMessage = (msg.role === 'user' && !msg.message.startsWith('[FEEDBACK]')) ? msg.message : 'Conversation';
              currentConversation = {
                id: conversationId++,
                title: firstUserMessage.substring(0, 50) + (firstUserMessage.length > 50 ? '...' : ''),
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
            
            // Add message to current conversation
            const messageType = msg.role === 'user' ? MESSAGE_TYPES.USER : MESSAGE_TYPES.BOT;
            currentConversation.messages.push({
              id: Date.now() + Math.random() + i, // Unique ID for the message
              type: messageType,
              content: msg.message,
              timestamp: formattedTime,
              originalTimestamp: msg.timestamp // Keep original timestamp for comparison
            });
            
            currentConversation.messageCount++;
            currentConversation.lastMessage = msg.message.substring(0, 100) + (msg.message.length > 100 ? '...' : '');
            
            // Always update conversation timestamp to the latest message timestamp
            currentConversation.timestamp = msg.timestamp || new Date().toISOString();
            
            // Update conversation title to be the first user message in this conversation (excluding feedback)
            if (msg.role === 'user' && !msg.message.startsWith('[FEEDBACK]') && currentConversation.messages.filter(m => m.type === MESSAGE_TYPES.USER).length === 1) {
              currentConversation.title = msg.message.substring(0, 50) + (msg.message.length > 50 ? '...' : '');
            }
          }
          
          // Don't forget the last conversation
          if (currentConversation) {
            conversations.push(currentConversation);
          }
          
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
            title: "Salesforce accounts sync issue",
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            messageCount: 6,
            lastMessage: "Would you like me to create a support ticket?"
          },
          {
            id: 2,
            title: "CDM Workbench NO DATA TO REPORT",
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
            messageCount: 4,
            lastMessage: "Please check the data configuration"
          },
          {
            id: 3,
            title: "Database deployment question",
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

        {/* Audio Toggle */}
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-700">Audio Feedback</span>
            <button
              onClick={() => onAudioToggle(!audioEnabled)}
              className={`p-1 rounded transition-colors ${
                audioEnabled 
                  ? 'text-blue-600 hover:bg-blue-100' 
                  : 'text-gray-400 hover:bg-gray-200'
              }`}
              title={audioEnabled ? 'Disable audio' : 'Enable audio'}
            >
              {audioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'conversations' ? (
          // Conversations Tab - ChatGPT Style
          conversations.length > 0 ? (
            <div className="p-2 space-y-1">
              {conversations.map((conversation) => (
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
              <h3 className="text-sm font-medium text-gray-600 mb-1">No conversations yet</h3>
              <p className="text-xs text-gray-500">
                Start a new conversation to see your chat history here
              </p>
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
            {recentTickets.length > 0 ? (
              <div className="space-y-1">
                {recentTickets.map((ticket) => (
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
                <h3 className="text-sm font-medium text-gray-600 mb-1">No recent tickets</h3>
                <p className="text-xs text-gray-500">
                  No tickets found for {getOrganizationFromEmail(currentUser?.email)}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-white">
        {activeTab === 'conversations' && conversations.length > 0 && (
          <button
            onClick={clearChatHistory}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear Chat History</span>
          </button>
        )}
      </div>
    </div>
  )
}

export default Sidebar