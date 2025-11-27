import React, { useState } from 'react'
import Sidebar from '../components/sidebar/Sidebar'
import ChatContainer from '../components/chat/ChatContainer'
import ChatInput from '../components/chat/ChatInput'
import TicketForm from '../components/forms/TicketForm'
import { useChat } from '../hooks/useChat'

const ChatPage = () => {
  const {
    messages,
    isLoading,
    error,
    isInitialized,
    currentUser,
    sendMessage,
    clearChat,
    initializeProcessor,
    setCurrentUser
  } = useChat()

  const [showTicketForm, setShowTicketForm] = useState(false)
  const [ticketQuery, setTicketQuery] = useState('')

  const handleUserChange = (user) => {
    setCurrentUser(user)
  }

  const handleInitialize = async (organizationData) => {
    await initializeProcessor(organizationData)
  }

  const handleSendMessage = async (message) => {
    // Always send the message to the backend first
    // The backend will handle intelligent ticket creation
    await sendMessage(message)
  }

  const handleTicketSubmit = async (ticketData) => {
    try {
      // In a real app, this would call the ticket creation API
      const ticketId = `TICK-${Math.floor(Math.random() * 10000)}`
      
      // Add the confirmation message to chat
      await sendMessage(`Created support ticket: ${ticketData.title}`)
      
    } catch (error) {
      console.error('Failed to create ticket:', error)
    }
  }

  const handleLoadConversation = (conversation) => {
    // In a real app, this would load the conversation from the API
    console.log('Loading conversation:', conversation)
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        currentUser={currentUser}
        onUserChange={handleUserChange}
        onInitialize={handleInitialize}
        isInitialized={isInitialized}
        onLoadConversation={handleLoadConversation}
        onClearChat={clearChat}
      />

      {/* Main Chat Area */}
      <div className="main-container">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Chat with nQuiry
              </h2>
              {currentUser && (
                <p className="text-sm text-gray-600">
                  Chatting as {currentUser.name}
                </p>
              )}
            </div>
            
            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isInitialized ? 'bg-green-400' : 'bg-gray-400'}`} />
              <span className="text-sm text-gray-600">
                {isInitialized ? 'Connected' : 'Not initialized'}
              </span>
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mx-6 mt-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Chat Container */}
        <ChatContainer 
          messages={messages} 
          isLoading={isLoading}
        />

        {/* Chat Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          disabled={!isInitialized}
        />
      </div>

      {/* Ticket Form Modal */}
      <TicketForm
        isOpen={showTicketForm}
        onClose={() => {
          setShowTicketForm(false)
          setTicketQuery('')
        }}
        onSubmit={handleTicketSubmit}
        initialQuery={ticketQuery}
      />
    </div>
  )
}

export default ChatPage