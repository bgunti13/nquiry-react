import React, { useState } from 'react'
import { Mic, Send, Loader2 } from 'lucide-react'
import { useVoice } from '../../hooks/useVoice'
import { EXAMPLE_QUERIES } from '../../utils/constants'

const ChatInput = ({ onSendMessage, isLoading, disabled = false }) => {
  const [message, setMessage] = useState('')
  const [showExamples, setShowExamples] = useState(false)
  const { isRecording, isSupported: voiceSupported, startRecording } = useVoice()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
      setShowExamples(false)
    }
  }

  const handleVoiceInput = () => {
    if (!voiceSupported) {
      alert('Voice input is not supported in this browser')
      return
    }

    startRecording(
      (transcript) => {
        setMessage(transcript)
      },
      (error) => {
        console.error('Voice input error:', error)
      }
    )
  }

  const handleExampleClick = (example) => {
    setMessage(example)
    setShowExamples(false)
  }

  const toggleExamples = () => {
    setShowExamples(!showExamples)
  }

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      {/* Example queries */}
      {showExamples && (
        <div className="mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">💡 Try asking:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {EXAMPLE_QUERIES.slice(0, 6).map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="text-left p-2 text-sm text-gray-600 hover:text-blue-600 hover:bg-white border border-transparent hover:border-blue-200 rounded-lg transition-all duration-200"
              >
                🔍 {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        <div className="flex-1">
          <div className="relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={disabled ? "Please initialize nQuiry first..." : "Type your question here..."}
              disabled={disabled || isLoading}
              rows={1}
              className="input-field resize-none pr-12 min-h-[3rem] max-h-32"
              style={{ 
                resize: 'none',
                overflowY: message.length > 100 ? 'auto' : 'hidden'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            
            {/* Voice input button */}
            {voiceSupported && (
              <button
                type="button"
                onClick={handleVoiceInput}
                disabled={disabled || isLoading || isRecording}
                className={`absolute right-3 top-3 p-1.5 rounded-lg transition-all duration-200 ${
                  isRecording 
                    ? 'bg-red-100 text-red-600 animate-pulse' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                title={isRecording ? 'Recording...' : 'Click to use voice input'}
              >
                <Mic className="w-4 h-4" />
              </button>
            )}
          </div>
          
          {/* Character count and examples toggle */}
          <div className="flex justify-between items-center mt-2">
            <button
              type="button"
              onClick={toggleExamples}
              className="text-xs text-blue-600 hover:text-blue-700 transition-colors"
            >
              {showExamples ? 'Hide examples' : 'Show example queries'}
            </button>
            <span className="text-xs text-gray-500">
              {message.length}/1000
            </span>
          </div>
        </div>

        {/* Send button */}
        <button
          type="submit"
          disabled={!message.trim() || isLoading || disabled}
          className="btn-primary min-w-[3rem] h-12 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>

      {/* Voice recording indicator */}
      {isRecording && (
        <div className="mt-3 flex items-center justify-center space-x-2 text-red-600">
          <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
          <span className="text-sm">Recording... Speak now</span>
        </div>
      )}
    </div>
  )
}

export default ChatInput