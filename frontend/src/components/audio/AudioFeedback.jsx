import React, { useState } from 'react'
import { Volume2 } from 'lucide-react'
import { useVoice } from '../../hooks/useVoice'

const AudioFeedback = ({ 
  messageContent, 
  isEnabled = false, 
  messageId,
  onToggleForMessage 
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const { speak, stopSpeaking, isSpeaking } = useVoice()

  const handleSpeakerClick = () => {
    if (isPlaying || isSpeaking) {
      stopSpeaking()
      setIsPlaying(false)
    } else {
      setIsPlaying(true)
      // Clean the message content for better speech
      const cleanContent = messageContent
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
        .replace(/`(.*?)`/g, '$1') // Remove code markdown
        .replace(/#{1,6}\s/g, '') // Remove headers
        .replace(/- /g, '') // Remove bullet points
        .replace(/\n/g, ' ') // Replace line breaks with spaces
        .replace(/\s+/g, ' ') // Remove extra spaces
        .trim()

      speak(cleanContent, {
        onStart: () => setIsPlaying(true),
        onEnd: () => setIsPlaying(false),
        onError: () => setIsPlaying(false)
      })
    }
  }

  return (
    <div className="flex items-center justify-end mt-2 pt-2 border-t border-gray-100">
      <button
        onClick={handleSpeakerClick}
        className={`p-1.5 rounded-full transition-all duration-200 ${
          isPlaying 
            ? 'bg-blue-100 text-blue-600 hover:bg-blue-200 animate-pulse' 
            : 'bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700'
        }`}
        title={isPlaying ? 'Stop audio' : 'Play audio'}
      >
        <Volume2 className="w-4 h-4" />
      </button>
    </div>
  )
}

export default AudioFeedback