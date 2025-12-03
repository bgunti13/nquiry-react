import React, { useState, useEffect } from 'react'
import { Copy, CheckCircle, User, Bot, Expand } from 'lucide-react'
import FeedbackButtons from '../feedback/FeedbackButtons'
import AudioFeedback from '../audio/AudioFeedback'

const ChatMessage = ({ 
  message, 
  isBot = false, 
  userId = '', 
  sessionId = '', 
  onFeedbackSubmitted,
  audioEnabled = false,
  onAudioToggleForMessage 
}) => {
  const { content, timestamp, images } = message
  const [copied, setCopied] = useState(false)
  const [expandedImage, setExpandedImage] = useState(null)

  // Debug: Log when component receives images
  useEffect(() => {
    if (images && images.length > 0) {
      console.log('🖼️ ChatMessage received images:', images.length, images)
    }
  }, [images])

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
              {/* Images (for user messages) */}
              {!isBot && images && images.length > 0 && (
                <div className="mb-3">
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    {images.slice(0, 4).map((image, index) => (
                      <div key={index} className="relative group">
                        <img 
                          src={image.preview || image.base64} 
                          alt={image.name}
                          className="w-full h-24 object-cover rounded-lg border cursor-pointer hover:opacity-90 transition-opacity"
                          onClick={() => setExpandedImage(image)}
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-10 rounded-lg transition-all duration-200 flex items-center justify-center">
                          <Expand className="w-4 h-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="absolute bottom-1 left-1 bg-black bg-opacity-50 text-white text-xs px-1 py-0.5 rounded truncate max-w-[calc(100%-8px)]">
                          {image.name}
                        </div>
                      </div>
                    ))}
                  </div>
                  {images.length > 4 && (
                    <p className="text-xs text-gray-500">+{images.length - 4} more images</p>
                  )}
                </div>
              )}

              {/* Text content */}
              {isBot ? (
                <div className="relative">
                  <div 
                    className={`prose prose-sm max-w-none text-gray-800 leading-relaxed transition-opacity duration-300 ${message.isLoading ? 'opacity-70' : 'opacity-100'}`}
                    style={{ fontSize: '14px', lineHeight: '1.6' }}
                    dangerouslySetInnerHTML={{ 
                      __html: formatBotContent(content)
                    }}
                  />
                  
                  {/* Loading indicator for streaming messages - smaller and under the content */}
                  {message.isLoading && (
                    <div className="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-200">
                      <div className="flex space-x-1">
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></div>
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-xs text-gray-500 italic">Processing...</span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm leading-relaxed text-gray-800">{content}</p>
              )}
            </div>

            {/* Image modal for expansion */}
            {expandedImage && (
              <div 
                className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
                onClick={() => setExpandedImage(null)}
              >
                <div className="max-w-4xl max-h-full">
                  <img 
                    src={expandedImage.preview || expandedImage.base64}
                    alt={expandedImage.name}
                    className="max-w-full max-h-full object-contain"
                  />
                  <div className="mt-2 text-center">
                    <p className="text-white text-sm">{expandedImage.name}</p>
                    <p className="text-gray-300 text-xs">Click anywhere to close</p>
                  </div>
                </div>
              </div>
            )}

            {/* Feedback for bot messages */}
            {isBot && (
              <>
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <div className="flex items-center justify-end">
                    <FeedbackButtons
                      messageId={message.id}
                      messageContent={content}
                      userId={userId}
                      sessionId={sessionId}
                      onFeedbackSubmitted={onFeedbackSubmitted}
                    />
                  </div>
                </div>
                
                {/* Audio Feedback Component */}
                <AudioFeedback
                  messageContent={content}
                  isEnabled={audioEnabled}
                  messageId={message.id}
                  onToggleForMessage={onAudioToggleForMessage}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatMessage