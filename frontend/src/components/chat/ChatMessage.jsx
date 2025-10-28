import React, { useState } from 'react'
import { Copy, CheckCircle, User, Bot } from 'lucide-react'
import FeedbackButtons from '../feedback/FeedbackButtons'

const ChatMessage = ({ message, isBot = false, userId = '', sessionId = '', onFeedbackSubmitted }) => {
  const { content, timestamp } = message
  const [copied, setCopied] = useState(false)

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''
    if (typeof timestamp === 'string' && timestamp.includes(':')) {
      return timestamp // Already formatted as HH:MM
    }
    // Convert to IST (Asia/Kolkata timezone)
    return new Date(timestamp).toLocaleTimeString('en-IN', { 
      timeZone: 'Asia/Kolkata',
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  const formatBotContent = (text) => {
    return text
      // Bold text with **
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      // Italic text with *
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      // Inline code with `
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
      // Line breaks
      .replace(/\n/g, '<br>')
      // Bullet points
      .replace(/^- (.+)$/gm, '<div class="flex items-start mt-1"><span class="text-blue-500 mr-2 mt-0.5">•</span><span>$1</span></div>')
      // Numbered lists
      .replace(/^(\d+)\. (.+)$/gm, '<div class="flex items-start mt-1"><span class="text-blue-500 mr-2 mt-0.5 font-semibold">$1.</span><span>$2</span></div>')
  }

  return (
    <div className={`mb-6 animate-fade-in ${isBot ? 'animate-slide-in-left' : 'animate-slide-in-right'}`}>
      <div className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
        <div className={`max-w-3xl w-full ${isBot ? '' : 'flex justify-end'}`}>
          <div className={`
            ${isBot 
              ? 'bg-gray-50 border-l-4 border-blue-500 text-gray-800' 
              : 'bg-blue-50 border-l-4 border-green-500 text-gray-800'
            } 
            p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 relative group
            ${isBot ? 'max-w-full' : 'max-w-2xl'}
          `}>
            {/* Message header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <div className={`
                  w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold
                  ${isBot 
                    ? 'bg-blue-100 text-blue-600' 
                    : 'bg-green-100 text-green-600'
                  }
                `}>
                  {isBot ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                </div>
                <span className="text-xs font-medium text-gray-600">
                  {isBot ? 'Nquiry Assistant' : 'You'}
                </span>
                {timestamp && (
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(timestamp)}
                  </span>
                )}
              </div>
              
              {/* Copy button */}
              <button
                onClick={handleCopy}
                className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded hover:bg-gray-200"
                title="Copy message"
              >
                {copied ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4 text-gray-500" />
                )}
              </button>
            </div>

            {/* Message content */}
            <div className="message-content">
              {isBot ? (
                <div 
                  className="prose prose-sm max-w-none text-gray-800 leading-relaxed"
                  style={{ fontSize: '14px', lineHeight: '1.6' }}
                  dangerouslySetInnerHTML={{ 
                    __html: formatBotContent(content)
                  }}
                />
              ) : (
                <p className="text-sm leading-relaxed text-gray-800">{content}</p>
              )}
            </div>

            {/* Status indicator and feedback for bot messages */}
            {isBot && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                    <span className="text-xs text-gray-500">Response generated</span>
                  </div>
                  <FeedbackButtons
                    messageId={message.id}
                    messageContent={content}
                    userId={userId}
                    sessionId={sessionId}
                    onFeedbackSubmitted={onFeedbackSubmitted}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatMessage