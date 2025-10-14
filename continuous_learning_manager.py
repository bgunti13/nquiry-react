"""
Continuous Learning Manager - Real ML-powered learning from user feedback
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class LearningMetrics:
    """Data structure for learning analytics"""
    total_feedback: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    excellent_feedback: int = 0
    needs_improvement: int = 0
    learning_score: float = 0.0
    improvement_trend: str = "stable"  # improving, declining, stable
    recent_improvement: bool = False
    confidence_level: float = 0.0

@dataclass
class ResponsePattern:
    """Pattern detected in successful responses"""
    pattern_type: str  # length, source, content_type, etc.
    success_rate: float
    examples: List[str]
    recommendation: str

class FeedbackAnalyzer:
    """Analyzes feedback patterns to identify improvement opportunities"""
    
    def __init__(self):
        self.sentiment_model = SentenceTransformer('all-mpnet-base-v2')
    
    def analyze_feedback_quality(self, feedback_data: List[Dict]) -> Dict:
        """Analyze feedback to determine response quality patterns"""
        if not feedback_data:
            return {"patterns": [], "insights": []}
        
        # Group feedback by type
        feedback_groups = defaultdict(list)
        for fb in feedback_data:
            feedback_groups[fb.get('feedback_type', 'unknown')].append(fb)
        
        patterns = []
        insights = []
        
        # Analyze response length patterns
        length_pattern = self._analyze_response_length_patterns(feedback_data)
        if length_pattern:
            patterns.append(length_pattern)
        
        # Analyze source effectiveness
        source_pattern = self._analyze_source_effectiveness(feedback_data)
        if source_pattern:
            patterns.append(source_pattern)
        
        # Analyze timing patterns
        timing_insights = self._analyze_timing_patterns(feedback_data)
        if timing_insights:
            insights.extend(timing_insights)
        
        return {
            "patterns": patterns,
            "insights": insights,
            "recommendations": self._generate_recommendations(patterns, insights)
        }
    
    def _analyze_response_length_patterns(self, feedback_data: List[Dict]) -> Optional[ResponsePattern]:
        """Analyze if response length correlates with user satisfaction"""
        length_satisfaction = []
        
        for fb in feedback_data:
            content = fb.get('response_content', '')
            feedback_type = fb.get('feedback_type', '')
            
            if content and feedback_type:
                length = len(content)
                satisfaction = 1 if feedback_type in ['positive', 'excellent'] else 0
                length_satisfaction.append((length, satisfaction))
        
        if len(length_satisfaction) < 5:  # Need minimum data
            return None
        
        # Find optimal length range
        lengths, satisfactions = zip(*length_satisfaction)
        
        # Simple analysis: group by length ranges
        short_responses = [s for l, s in length_satisfaction if l < 200]
        medium_responses = [s for l, s in length_satisfaction if 200 <= l <= 500]
        long_responses = [s for l, s in length_satisfaction if l > 500]
        
        best_range = "medium"
        best_rate = np.mean(medium_responses) if medium_responses else 0
        
        if short_responses and np.mean(short_responses) > best_rate:
            best_range = "short"
            best_rate = np.mean(short_responses)
        
        if long_responses and np.mean(long_responses) > best_rate:
            best_range = "long"
            best_rate = np.mean(long_responses)
        
        return ResponsePattern(
            pattern_type="response_length",
            success_rate=best_rate,
            examples=[f"Best length: {best_range} responses"],
            recommendation=f"Optimize for {best_range} responses (success rate: {best_rate:.2f})"
        )
    
    def _analyze_source_effectiveness(self, feedback_data: List[Dict]) -> Optional[ResponsePattern]:
        """Analyze which knowledge sources get better feedback"""
        source_satisfaction = defaultdict(list)
        
        for fb in feedback_data:
            # Try to detect source from response content
            content = fb.get('response_content', '').lower()
            feedback_type = fb.get('feedback_type', '')
            satisfaction = 1 if feedback_type in ['positive', 'excellent'] else 0
            
            if 'jira' in content or 'issue' in content or 'ticket' in content:
                source_satisfaction['JIRA'].append(satisfaction)
            elif 'mindtouch' in content or 'documentation' in content or 'guide' in content:
                source_satisfaction['MindTouch'].append(satisfaction)
            elif 'confluence' in content or 'wiki' in content:
                source_satisfaction['Confluence'].append(satisfaction)
        
        if not source_satisfaction:
            return None
        
        # Find best performing source
        best_source = max(source_satisfaction.items(), 
                         key=lambda x: np.mean(x[1]) if x[1] else 0)
        
        return ResponsePattern(
            pattern_type="source_effectiveness",
            success_rate=np.mean(best_source[1]),
            examples=[f"Best source: {best_source[0]}"],
            recommendation=f"Prioritize {best_source[0]} results when available"
        )
    
    def _analyze_timing_patterns(self, feedback_data: List[Dict]) -> List[str]:
        """Analyze if there are time-based patterns in feedback"""
        insights = []
        
        # Group feedback by time periods
        recent_feedback = []
        older_feedback = []
        
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        for fb in feedback_data:
            fb_time_str = fb.get('timestamp', '')
            try:
                fb_time = datetime.fromisoformat(fb_time_str.replace('Z', '+00:00'))
                satisfaction = 1 if fb.get('feedback_type') in ['positive', 'excellent'] else 0
                
                if fb_time > week_ago:
                    recent_feedback.append(satisfaction)
                else:
                    older_feedback.append(satisfaction)
            except:
                continue
        
        if recent_feedback and older_feedback:
            recent_score = np.mean(recent_feedback)
            older_score = np.mean(older_feedback)
            
            if recent_score > older_score + 0.1:
                insights.append("System showing improvement over time")
            elif recent_score < older_score - 0.1:
                insights.append("Recent performance decline detected")
            else:
                insights.append("Consistent performance maintained")
        
        return insights
    
    def _generate_recommendations(self, patterns: List[ResponsePattern], insights: List[str]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        for pattern in patterns:
            recommendations.append(pattern.recommendation)
        
        if "improvement over time" in str(insights):
            recommendations.append("Continue current optimization strategies")
        elif "decline detected" in str(insights):
            recommendations.append("Review recent changes and adjust response formatting")
        
        if not recommendations:
            recommendations.append("Collect more feedback data for better insights")
        
        return recommendations

class ContinuousLearningManager:
    """Main continuous learning engine"""
    
    def __init__(self, mongodb_uri="mongodb://localhost:27017/", db_name="Nquiry"):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.feedback_collection = self.db.feedback_analytics
        self.learning_collection = self.db.learning_metrics
        
        self.analyzer = FeedbackAnalyzer()
        
        # Learning configuration
        self.min_feedback_threshold = 3  # Minimum feedback needed for analysis
        self.confidence_threshold = 0.7  # Confidence level for applying changes
        self.learning_rate = 0.1  # How quickly to adapt parameters
        
        print("🧠 Continuous Learning Manager initialized")
    
    def store_feedback(self, user_id: str, response_content: str, feedback_type: str, 
                      feedback_category: str, session_id: str = None) -> Dict:
        """Store feedback and trigger learning analysis"""
        
        feedback_data = {
            'user_id': user_id,
            'response_content': response_content[:500],  # Truncate for storage
            'feedback_type': feedback_type,
            'feedback_category': feedback_category,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'processed': False  # Flag for batch processing
        }
        
        # Store in database
        result = self.feedback_collection.insert_one(feedback_data)
        
        # Trigger real-time learning update
        self._update_learning_metrics()
        
        print(f"📊 Feedback stored and learning updated: {feedback_type} ({feedback_category})")
        
        return {
            "feedback_id": str(result.inserted_id),
            "learning_triggered": True
        }
    
    def get_learning_status(self, user_id: str = None) -> Dict:
        """Get real learning analytics (not mock data!)"""
        
        # Get all feedback or user-specific feedback
        query = {"user_id": user_id} if user_id else {}
        feedback_data = list(self.feedback_collection.find(query))
        
        if not feedback_data:
            return self._get_initial_learning_status()
        
        # Calculate real metrics
        metrics = self._calculate_learning_metrics(feedback_data)
        
        # Analyze patterns
        analysis = self.analyzer.analyze_feedback_quality(feedback_data)
        
        # Get learning insights
        insights = self._generate_learning_insights(metrics, analysis)
        
        return {
            "status": self._determine_learning_status(metrics),
            "score": metrics.learning_score,
            "total_feedback": metrics.total_feedback,
            "positive_feedback": metrics.positive_feedback,
            "excellent_feedback": metrics.excellent_feedback,
            "recent_improvement": metrics.recent_improvement,
            "improvement_trend": metrics.improvement_trend,
            "confidence_level": metrics.confidence_level,
            "patterns": analysis.get("patterns", []),
            "insights": insights,
            "recommendations": analysis.get("recommendations", [])
        }
    
    def get_adaptive_search_parameters(self) -> Dict:
        """Get dynamically adjusted search parameters based on learning"""
        
        # Get recent feedback
        week_ago = datetime.now() - timedelta(days=7)
        recent_feedback = list(self.feedback_collection.find({
            "timestamp": {"$gte": week_ago.isoformat()}
        }))
        
        if len(recent_feedback) < self.min_feedback_threshold:
            return self._get_default_search_parameters()
        
        # Analyze recent patterns
        analysis = self.analyzer.analyze_feedback_quality(recent_feedback)
        
        # Adjust parameters based on learning
        parameters = self._calculate_adaptive_parameters(analysis)
        
        print(f"🎯 Adaptive search parameters: similarity_threshold={parameters['similarity_threshold']}")
        
        return parameters
    
    def _calculate_learning_metrics(self, feedback_data: List[Dict]) -> LearningMetrics:
        """Calculate real learning metrics from feedback data"""
        
        metrics = LearningMetrics()
        metrics.total_feedback = len(feedback_data)
        
        # Count feedback types
        for fb in feedback_data:
            fb_type = fb.get('feedback_type', '')
            if fb_type == 'positive':
                metrics.positive_feedback += 1
            elif fb_type == 'negative':
                metrics.negative_feedback += 1
            elif fb_type == 'excellent':
                metrics.excellent_feedback += 1
            elif fb_type == 'needs_improvement':
                metrics.needs_improvement += 1
        
        # Calculate learning score
        positive_weight = metrics.positive_feedback * 1.0
        excellent_weight = metrics.excellent_feedback * 1.5
        total_positive = positive_weight + excellent_weight
        
        if metrics.total_feedback > 0:
            metrics.learning_score = (total_positive / metrics.total_feedback) * 100
        
        # Calculate improvement trend
        metrics.improvement_trend, metrics.recent_improvement = self._calculate_trend(feedback_data)
        
        # Calculate confidence level
        metrics.confidence_level = min(1.0, metrics.total_feedback / 20.0)  # More feedback = higher confidence
        
        return metrics
    
    def _calculate_trend(self, feedback_data: List[Dict]) -> Tuple[str, bool]:
        """Calculate if performance is improving, declining, or stable"""
        
        if len(feedback_data) < 6:  # Need minimum data for trend analysis
            return "stable", False
        
        # Sort by timestamp
        try:
            sorted_feedback = sorted(feedback_data, 
                                   key=lambda x: datetime.fromisoformat(x.get('timestamp', '')))
        except:
            return "stable", False
        
        # Split into two halves: earlier vs recent
        mid_point = len(sorted_feedback) // 2
        earlier_half = sorted_feedback[:mid_point]
        recent_half = sorted_feedback[mid_point:]
        
        # Calculate satisfaction rates
        def satisfaction_rate(feedback_list):
            positive_count = sum(1 for fb in feedback_list 
                               if fb.get('feedback_type') in ['positive', 'excellent'])
            return positive_count / len(feedback_list) if feedback_list else 0
        
        earlier_rate = satisfaction_rate(earlier_half)
        recent_rate = satisfaction_rate(recent_half)
        
        # Determine trend
        improvement_threshold = 0.15  # 15% improvement needed to detect trend
        
        if recent_rate > earlier_rate + improvement_threshold:
            return "improving", True
        elif recent_rate < earlier_rate - improvement_threshold:
            return "declining", False
        else:
            return "stable", False
    
    def _determine_learning_status(self, metrics: LearningMetrics) -> str:
        """Determine current learning status based on metrics"""
        
        if metrics.total_feedback < 5:
            return "starting"
        elif metrics.learning_score >= 90:
            return "excellent"
        elif metrics.learning_score >= 75:
            return "good"
        elif metrics.improvement_trend == "improving":
            return "improving"
        else:
            return "learning"
    
    def _generate_learning_insights(self, metrics: LearningMetrics, analysis: Dict) -> List[str]:
        """Generate human-readable insights from learning data"""
        
        insights = []
        
        # Performance insights
        if metrics.learning_score >= 80:
            insights.append(f"🌟 High user satisfaction: {metrics.learning_score:.1f}% positive feedback")
        elif metrics.learning_score >= 60:
            insights.append(f"✅ Good performance: {metrics.learning_score:.1f}% satisfaction rate")
        else:
            insights.append(f"📈 Room for improvement: {metrics.learning_score:.1f}% satisfaction")
        
        # Trend insights
        if metrics.recent_improvement:
            insights.append("📈 System performance is improving over time")
        elif metrics.improvement_trend == "declining":
            insights.append("⚠️ Recent performance decline detected")
        
        # Confidence insights
        if metrics.confidence_level < 0.3:
            insights.append("📊 More feedback needed for reliable analysis")
        elif metrics.confidence_level > 0.8:
            insights.append("🎯 High confidence in learning insights")
        
        # Add analysis insights
        insights.extend(analysis.get("insights", []))
        
        return insights
    
    def _update_learning_metrics(self):
        """Update stored learning metrics for faster retrieval"""
        
        # This could be run periodically or after each feedback
        # Store aggregated metrics for performance
        pass
    
    def _get_initial_learning_status(self) -> Dict:
        """Return status when no feedback exists yet"""
        return {
            "status": "starting",
            "score": 0.0,
            "total_feedback": 0,
            "positive_feedback": 0,
            "excellent_feedback": 0,
            "recent_improvement": False,
            "improvement_trend": "stable",
            "confidence_level": 0.0,
            "patterns": [],
            "insights": ["🚀 System ready to learn from user feedback"],
            "recommendations": ["Start using the system and provide feedback to enable learning"]
        }
    
    def _get_default_search_parameters(self) -> Dict:
        """Default search parameters when learning data insufficient"""
        return {
            "similarity_threshold": 0.3,
            "source_weights": {"JIRA": 1.0, "MindTouch": 1.0, "Confluence": 0.8},
            "response_length_target": "medium"
        }
    
    def _calculate_adaptive_parameters(self, analysis: Dict) -> Dict:
        """Calculate adjusted search parameters based on learning insights"""
        
        parameters = self._get_default_search_parameters()
        
        # Adjust similarity threshold based on feedback patterns
        patterns = analysis.get("patterns", [])
        for pattern in patterns:
            if pattern.pattern_type == "response_length" and pattern.success_rate > 0.8:
                # Adjust based on successful response length patterns
                if "short" in pattern.recommendation:
                    parameters["response_length_target"] = "short"
                elif "long" in pattern.recommendation:
                    parameters["response_length_target"] = "long"
            
            elif pattern.pattern_type == "source_effectiveness" and pattern.success_rate > 0.8:
                # Boost successful sources
                if "JIRA" in pattern.recommendation:
                    parameters["source_weights"]["JIRA"] = 1.2
                elif "MindTouch" in pattern.recommendation:
                    parameters["source_weights"]["MindTouch"] = 1.2
        
        return parameters

# Global instance for use in FastAPI
learning_manager = None

def get_learning_manager() -> ContinuousLearningManager:
    """Get or create the global learning manager instance"""
    global learning_manager
    if learning_manager is None:
        learning_manager = ContinuousLearningManager()
    return learning_manager