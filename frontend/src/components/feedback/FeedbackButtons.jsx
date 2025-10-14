import React, { useState } from 'react'
import { ThumbsUp, ThumbsDown, Star, RotateCcw } from 'lucide-react'
import { feedbackService } from '../../services/feedbackService'

const FeedbackButtons = ({ 
  messageId, 
  messageContent, 
  userId, 
  sessionId,
  onFeedbackSubmitted 
}) => {
  const [feedbackGiven, setFeedbackGiven] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleFeedback = async (feedbackType, feedbackCategory) => {
    if (feedbackGiven || isSubmitting) return

    setIsSubmitting(true)
    
    try {
      await feedbackService.collectFeedback(
        userId,
        messageContent,
        feedbackType,
        feedbackCategory,
        sessionId
      )
      
      setFeedbackGiven(feedbackCategory)
      
      // Show success toast/notification
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(feedbackType, feedbackCategory)
      }
      
      // Log success message for now (can be enhanced with toast system later)
      const messages = {
        thumbs_up: "✅ Thanks for your feedback!",
        thumbs_down: "📝 Thank you. We'll improve!",
        star: "🌟 Excellent! Thanks!",
        improve: "🔧 We'll work on improving!"
      }
      
      console.log(messages[feedbackCategory])
      
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (feedbackGiven) {
    return (
      <div className="flex items-center space-x-1 text-sm text-green-600 mt-2">
        <span>✓ Feedback submitted</span>
      </div>
    )
  }

  if (feedbackGiven) {
    return (
      <div className="flex items-center space-x-1 text-sm text-green-600 mt-2">
        <span>✓ Feedback submitted</span>
      </div>
    )
  }

  return (
    <div className="flex items-center space-x-1 mt-2 opacity-70 hover:opacity-100 transition-opacity">
      {/* Thumbs Up */}
      <button
        onClick={() => handleFeedback('positive', 'thumbs_up')}
        disabled={isSubmitting}
        className="p-1 rounded hover:bg-green-100 transition-colors disabled:opacity-50"
        title="Helpful response"
      >
        <ThumbsUp className="w-4 h-4 text-green-600" />
      </button>

      {/* Thumbs Down */}
      <button
        onClick={() => handleFeedback('negative', 'thumbs_down')}
        disabled={isSubmitting}
        className="p-1 rounded hover:bg-red-100 transition-colors disabled:opacity-50"
        title="Not helpful"
      >
        <ThumbsDown className="w-4 h-4 text-red-600" />
      </button>

      {/* Excellent (Star) */}
      <button
        onClick={() => handleFeedback('excellent', 'star')}
        disabled={isSubmitting}
        className="p-1 rounded hover:bg-yellow-100 transition-colors disabled:opacity-50"
        title="Excellent response"
      >
        <Star className="w-4 h-4 text-yellow-600" />
      </button>

      {/* Needs Improvement */}
      <button
        onClick={() => handleFeedback('needs_improvement', 'improve')}
        disabled={isSubmitting}
        className="p-1 rounded hover:bg-blue-100 transition-colors disabled:opacity-50"
        title="Needs improvement"
      >
        <RotateCcw className="w-4 h-4 text-blue-600" />
      </button>

      {isSubmitting && (
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
      )}
    </div>
  )
}

export default FeedbackButtons