import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Mic, MicOff, Paperclip, X, Image as ImageIcon } from 'lucide-react'
import { EXAMPLE_QUERIES } from '../../utils/constants'

const ChatInputFixed = ({ 
  onSendMessage, 
  isLoading, 
  disabled = false, 
  audioEnabled = false 
}) => {
  const [message, setMessage] = useState('')
  const [showExamples, setShowExamples] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [voiceSupported, setVoiceSupported] = useState(false)
  const [selectedImages, setSelectedImages] = useState([])
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const mediaRecorderRef = useRef(null)

  // Check voice support on mount
  useEffect(() => {
    setVoiceSupported(
      'webkitSpeechRecognition' in window || 
      'SpeechRecognition' in window ||
      navigator.mediaDevices?.getUserMedia
    )
  }, [])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [message])

  const handleSubmit = (e) => {
    e.preventDefault()
    if ((message.trim() || selectedImages.length > 0) && !isLoading && !disabled) {
      onSendMessage(message.trim(), selectedImages)
      setMessage('')
      setSelectedImages([])
      setShowExamples(false)
    }
  }

  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files)
    const validImages = files.filter(file => {
      const isValidType = file.type.startsWith('image/')
      const isValidSize = file.size <= 5 * 1024 * 1024 // 5MB limit
      return isValidType && isValidSize
    })

    if (validImages.length !== files.length) {
      alert('Some files were skipped. Please select only image files under 5MB.')
    }

    // Convert to base64 for preview and API
    Promise.all(
      validImages.map(file => {
        return new Promise((resolve) => {
          const reader = new FileReader()
          reader.onload = (e) => {
            resolve({
              file,
              name: file.name,
              size: file.size,
              type: file.type,
              base64: e.target.result,
              preview: e.target.result
            })
          }
          reader.readAsDataURL(file)
        })
      })
    ).then(imageData => {
      setSelectedImages(prev => [...prev, ...imageData].slice(0, 3)) // Max 3 images
    })
  }

  const removeImage = (index) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index))
  }

  const openFileDialog = () => {
    fileInputRef.current?.click()
  }

  const handleExampleClick = (example) => {
    setMessage(example)
    setShowExamples(false)
    textareaRef.current?.focus()
  }

  const toggleExamples = () => {
    setShowExamples(!showExamples)
  }

  const startVoiceRecording = async () => {
    if (!voiceSupported) return

    try {
      // Try Web Speech API first
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        const recognition = new SpeechRecognition()
        
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = 'en-US'

        recognition.onstart = () => {
          setIsRecording(true)
        }

        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript
          setMessage(transcript)
          setIsRecording(false)
        }

        recognition.onerror = () => {
          setIsRecording(false)
        }

        recognition.onend = () => {
          setIsRecording(false)
        }

        recognition.start()
      }
    } catch (error) {
      console.error('Voice recording failed:', error)
      setIsRecording(false)
    }
  }

  const stopVoiceRecording = () => {
    setIsRecording(false)
  }

  return (
    <div className="bg-white border-t border-gray-200">
      <div className="max-w-4xl mx-auto p-6">
        {/* Example queries */}
        {showExamples && (
          <div className="mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-3">💡 Try asking:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {EXAMPLE_QUERIES.slice(0, 6).map((example, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleClick(example)}
                  className="text-left p-3 text-sm text-gray-600 hover:text-blue-600 hover:bg-white border border-transparent hover:border-blue-200 rounded-lg transition-all duration-200"
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
            {/* Image previews */}
            {selectedImages.length > 0 && (
              <div className="mb-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Attached Images ({selectedImages.length}/3)
                  </span>
                </div>
                <div className="flex space-x-2 overflow-x-auto">
                  {selectedImages.map((image, index) => (
                    <div key={index} className="relative flex-shrink-0">
                      <img 
                        src={image.preview} 
                        alt={image.name}
                        className="w-20 h-20 object-cover rounded-lg border"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(index)}
                        className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                      <div className="mt-1 text-xs text-gray-500 truncate w-20">
                        {image.name}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="relative">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={
                  selectedImages.length > 0 
                    ? "Describe your issue or ask a question about the images..." 
                    : disabled 
                      ? "Please initialize Nquiry first..." 
                      : isRecording 
                        ? "🎤 Listening..." 
                        : "Ask anything or upload an image 📸"
                }
                disabled={disabled || isLoading}
                rows={1}
                className="w-full px-4 py-3 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-colors"
                style={{ 
                  minHeight: '3rem',
                  maxHeight: '120px',
                  backgroundColor: isRecording ? '#fef3c7' : 'white'
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSubmit(e)
                  }
                }}
              />
              
              {/* File input (hidden) */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />

              {/* Action buttons container */}
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                {/* Image upload button */}
                <button
                  type="button"
                  onClick={openFileDialog}
                  disabled={disabled || isLoading || selectedImages.length >= 3}
                  className="p-1.5 rounded-lg transition-colors bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Upload images (max 3, 5MB each)"
                >
                  <ImageIcon className="w-4 h-4" />
                </button>

                {/* Voice input button */}
                {voiceSupported && (
                  <button
                    type="button"
                    onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
                    disabled={disabled || isLoading}
                    className={`p-1.5 rounded-lg transition-colors ${
                      isRecording 
                        ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                    title={isRecording ? "Stop recording" : "Start voice input"}
                  >
                    {isRecording ? (
                      <MicOff className="w-4 h-4" />
                    ) : (
                      <Mic className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>
            </div>
            
            {/* Controls row */}
            <div className="flex justify-between items-center mt-2">
              <button
                type="button"
                onClick={toggleExamples}
                className="text-xs text-blue-600 hover:text-blue-700 transition-colors"
              >
                {showExamples ? 'Hide examples' : 'Show example queries'}
              </button>
              
              <div className="flex items-center space-x-3">
                {selectedImages.length > 0 && (
                  <span className="text-xs text-blue-600">
                    📸 {selectedImages.length} image{selectedImages.length !== 1 ? 's' : ''}
                  </span>
                )}
                {voiceSupported && (
                  <span className="text-xs text-gray-500">
                    🎤 Voice input available
                  </span>
                )}
                <span className="text-xs text-gray-500">
                  {message.length}/1000
                </span>
              </div>
            </div>
          </div>

          {/* Send button */}
          <button
            type="submit"
            disabled={(!message.trim() && selectedImages.length === 0) || isLoading || disabled || isRecording}
            className="bg-blue-600 text-white p-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[3rem] h-12"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>

        {/* Recording indicator */}
        {isRecording && (
          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center justify-center space-x-2 text-yellow-700">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm">Recording... Speak clearly</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatInputFixed