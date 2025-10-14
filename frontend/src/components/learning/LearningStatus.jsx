import React, { useState, useEffect } from 'react'
import { Brain, TrendingUp, Award, BarChart3, ChevronDown, ChevronRight } from 'lucide-react'
import { feedbackService } from '../../services/feedbackService'

const LearningStatus = ({ userId }) => {
  const [learningData, setLearningData] = useState(null)
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (isExpanded && !learningData) {
      fetchLearningStatus()
    }
  }, [isExpanded, userId])

  const fetchLearningStatus = async () => {
    setIsLoading(true)
    try {
      const response = await feedbackService.getLearningStatus(userId)
      if (response.status === 'success') {
        setLearningData(response.learning_status)
      }
    } catch (error) {
      console.error('Failed to fetch learning status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'excellent':
        return { icon: '🌟', color: 'text-green-600' }
      case 'good':
        return { icon: '✅', color: 'text-green-500' }
      case 'improving':
        return { icon: '📈', color: 'text-yellow-500' }
      case 'learning':
        return { icon: '🔄', color: 'text-blue-500' }
      default:
        return { icon: '🚀', color: 'text-purple-500' }
    }
  }

  if (!learningData && !isExpanded) {
    return (
      <div className="border-t border-gray-200 pt-4">
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center justify-between w-full p-2 text-left hover:bg-gray-50 rounded-lg transition-colors"
        >
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-purple-500" />
            <span className="font-medium text-gray-700">Continuous Learning</span>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-400" />
        </button>
      </div>
    )
  }

  const statusInfo = learningData ? getStatusIcon(learningData.status) : { icon: '🧠', color: 'text-gray-500' }

  return (
    <div className="border-t border-gray-200 pt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full p-2 text-left hover:bg-gray-50 rounded-lg transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-purple-500" />
          <span className="font-medium text-gray-700">Continuous Learning</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
            </div>
          ) : learningData ? (
            <div className="space-y-3">
              {/* Status Display */}
              <div className="text-center">
                <div className="text-2xl mb-1">{statusInfo.icon}</div>
                <div className={`font-bold ${statusInfo.color}`}>
                  {learningData.status.charAt(0).toUpperCase() + learningData.status.slice(1)}
                </div>
                <div className="text-sm text-gray-600">
                  Learning Score: {learningData.score.toFixed(1)}%
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1">
                <div className="text-xs text-gray-600">Learning Progress</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${learningData.score}%` }}
                  ></div>
                </div>
              </div>

              {/* Metrics */}
              {learningData.total_feedback > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-medium text-gray-700">📊 Learning Metrics</div>
                  
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Total Feedback:</span>
                    <span className="font-medium">{learningData.total_feedback}</span>
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Positive:</span>
                    <span className="font-medium text-green-600">
                      {learningData.positive_feedback + learningData.excellent_feedback}/{learningData.total_feedback}
                    </span>
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Excellent:</span>
                    <span className="font-medium text-yellow-600">
                      {learningData.excellent_feedback}
                    </span>
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Trend:</span>
                    <span className={`font-medium ${
                      learningData.improvement_trend === 'improving' ? 'text-green-600' :
                      learningData.improvement_trend === 'declining' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {learningData.improvement_trend}
                    </span>
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Confidence:</span>
                    <span className="font-medium text-blue-600">
                      {(learningData.confidence_level * 100).toFixed(0)}%
                    </span>
                  </div>

                  {learningData.recent_improvement && (
                    <div className="flex items-center space-x-1 text-xs text-green-600 bg-green-50 p-2 rounded">
                      <TrendingUp className="w-3 h-3" />
                      <span>Recent improvement detected!</span>
                    </div>
                  )}

                  {/* Learning Insights */}
                  {learningData.insights && learningData.insights.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-gray-700">🔍 Insights</div>
                      {learningData.insights.slice(0, 3).map((insight, index) => (
                        <div key={index} className="text-xs text-gray-600 bg-blue-50 p-1 rounded">
                          {insight}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recommendations */}
                  {learningData.recommendations && learningData.recommendations.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-xs font-medium text-gray-700">💡 Recommendations</div>
                      {learningData.recommendations.slice(0, 2).map((rec, index) => (
                        <div key={index} className="text-xs text-gray-600 bg-yellow-50 p-1 rounded">
                          {rec}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Refresh Button */}
              <button
                onClick={fetchLearningStatus}
                disabled={isLoading}
                className="w-full text-xs text-purple-600 hover:text-purple-700 disabled:opacity-50 flex items-center justify-center space-x-1"
              >
                <BarChart3 className="w-3 h-3" />
                <span>Refresh Analytics</span>
              </button>
            </div>
          ) : (
            <div className="text-center text-sm text-gray-500 py-2">
              No learning data available yet
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LearningStatus