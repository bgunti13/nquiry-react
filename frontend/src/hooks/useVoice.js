import { useState, useCallback, useEffect } from 'react'

export const useVoice = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState(null)

  // Check if speech recognition is supported
  const checkSupport = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const supported = !!SpeechRecognition
    setIsSupported(supported)
    return supported
  }, [])

  // Initialize support check on mount
  useEffect(() => {
    checkSupport()
  }, [checkSupport])

  // Start voice recording
  const startRecording = useCallback((onResult, onError) => {
    if (!checkSupport()) {
      const errorMsg = 'Speech recognition is not supported in this browser'
      setError(errorMsg)
      onError?.(errorMsg)
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()

    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsRecording(true)
      setError(null)
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      onResult?.(transcript)
      setIsRecording(false)
    }

    recognition.onerror = (event) => {
      const errorMsg = `Speech recognition error: ${event.error}`
      setError(errorMsg)
      onError?.(errorMsg)
      setIsRecording(false)
    }

    recognition.onend = () => {
      setIsRecording(false)
    }

    try {
      recognition.start()
    } catch (err) {
      const errorMsg = 'Failed to start speech recognition'
      setError(errorMsg)
      onError?.(errorMsg)
      setIsRecording(false)
    }
  }, [checkSupport])

  // Speak text using browser's speech synthesis
  const speak = useCallback((text) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel()
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0
      
      // Track speaking state
      utterance.onstart = () => {
        setIsSpeaking(true)
      }
      
      utterance.onend = () => {
        setIsSpeaking(false)
      }
      
      utterance.onerror = () => {
        setIsSpeaking(false)
      }
      
      setIsSpeaking(true)
      window.speechSynthesis.speak(utterance)
    }
  }, [])

  // Stop any ongoing speech
  const stopSpeaking = useCallback(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }, [])

  return {
    isRecording,
    isSupported,
    isSpeaking,
    error,
    startRecording,
    speak,
    stopSpeaking
  }
}

export default useVoice