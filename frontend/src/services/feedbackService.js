/**
 * Feedback and Continuous Learning Service
 */

const API_BASE_URL = 'http://127.0.0.1:8000'

export const feedbackService = {
  /**
   * Collect user feedback for continuous learning
   */
  async collectFeedback(userId, responseContent, feedbackType, feedbackCategory, sessionId = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/feedback/collect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          response_content: responseContent,
          feedback_type: feedbackType, // positive, negative, excellent, needs_improvement
          feedback_category: feedbackCategory, // thumbs_up, thumbs_down, star, improve
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      console.log('Feedback collected:', result)
      return result
    } catch (error) {
      console.error('Error collecting feedback:', error)
      throw error
    }
  },

  /**
   * Get learning status and analytics
   */
  async getLearningStatus(userId = '') {
    try {
      const url = userId 
        ? `${API_BASE_URL}/api/learning/status?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE_URL}/api/learning/status`
      
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error getting learning status:', error)
      throw error
    }
  }
}

export default feedbackService