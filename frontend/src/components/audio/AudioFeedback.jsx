import React, { useState, useEffect } from 'react'
import { Volume2, VolumeX, Play, Square } from 'lucide-react'
import { useVoice } from '../../hooks/useVoice'

const AudioFeedback = ({ 
  messageContent, 
  isEnabled = false, 
  messageId,
  onToggleForMessage 
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [audioEnabled, setAudioEnabled] = useState(isEnabled)
  const { speak, stopSpeaking, isSpeaking } = useVoice()

  useEffect(() => {
    setAudioEnabled(isEnabled)
  }, [isEnabled])

  const handlePlayAudio = () => {
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

  const handleToggleAudio = () => {
    const newState = !audioEnabled
    setAudioEnabled(newState)
    if (onToggleForMessage) {
      onToggleForMessage(messageId, newState)
    }
    
    // If disabling audio and currently playing, stop the audio
    if (!newState && isPlaying) {
      stopSpeaking()
      setIsPlaying(false)
    }
  }

  return (
    <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
      <div className="flex items-center space-x-2">
        {/* Audio Toggle for this message */}
        <button
          onClick={handleToggleAudio}
          className={`flex items-center space-x-1 px-2 py-1 rounded text-xs transition-colors ${
            audioEnabled 
              ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
          title={audioEnabled ? 'Disable audio for this response' : 'Enable audio for this response'}
        >
          {audioEnabled ? <Volume2 className="w-3 h-3" /> : <VolumeX className="w-3 h-3" />}
          <span>{audioEnabled ? 'Audio On' : 'Audio Off'}</span>
        </button>

        {/* Play/Stop Button - only show when audio is enabled */}
        {audioEnabled && (
          <button
            onClick={handlePlayAudio}
            className={`flex items-center space-x-1 px-2 py-1 rounded text-xs transition-colors ${
              isPlaying 
                ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
            title={isPlaying ? 'Stop audio' : 'Play audio'}
          >
            {isPlaying ? <Square className="w-3 h-3" /> : <Play className="w-3 h-3" />}
            <span>{isPlaying ? 'Stop' : 'Play'}</span>
          </button>
        )}
      </div>

      {/* Audio status indicator */}
      {audioEnabled && isPlaying && (
        <div className="flex items-center space-x-1 text-xs text-blue-600">
          <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></div>
          <span>Playing...</span>
        </div>
      )}
    </div>
  )
}

export default AudioFeedback