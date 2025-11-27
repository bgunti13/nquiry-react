import React, { useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import { MESSAGE_TYPES } from '../../utils/constants'

const ChatContainer = ({ 
  messages, 
  isLoading, 
  userId, 
  sessionId, 
  onFeedbackSubmitted, 
  audioEnabled = false,
  onAudioToggleForMessage 
}) => {
  const messagesEndRef = useRef(null)
  const containerRef = useRef(null)

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      })
    }
  }, [messages, isLoading])

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-gray-50 to-white"
    >
      {/* Welcome message when no messages */}
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-blue-500 to-green-500 rounded-2xl flex items-center justify-center">
              <span className="text-2xl text-white font-bold">N</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-3">
              Welcome to Nquiry
            </h2>
            <p className="text-gray-600 mb-6">
              Your intelligent query assistant is ready to help. Ask me anything about your products, 
              services, or need support with technical questions.
            </p>
            <div className="text-sm text-gray-500">
              💡 Try asking about software versions, configurations, troubleshooting, or support plans
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="max-w-4xl mx-auto">
        {messages.map((message, index) => (
          <ChatMessage
            key={message.id || index}
            message={message}
            isBot={message.type === MESSAGE_TYPES.BOT}
            userId={userId}
            sessionId={sessionId}
            onFeedbackSubmitted={onFeedbackSubmitted}
            audioEnabled={audioEnabled}
            onAudioToggleForMessage={onAudioToggleForMessage}
          />
        ))}

        {/* Loading indicator - only show if no messages are currently in loading state */}
        {isLoading && !messages.some(msg => msg.isLoading) && (
          <div className="mb-4 animate-slide-in-left">
            <div className="flex justify-start">
              <div className="chat-message-bot max-w-xs">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1 loading-dots">
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                  </div>
                  <span className="text-sm text-gray-500">Nquiry is thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

export default ChatContainer