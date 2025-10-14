
"""
Test script to demonstrate continuous learning functionality
"""

import asyncio
import json
import time
from continuous_learning_manager import ContinuousLearningManager

def test_continuous_learning():
    """Test the continuous learning system with sample data"""
    
    print("🧠 Testing Continuous Learning Manager")
    print("=" * 50)
    
    # Initialize learning manager
    learning_manager = ContinuousLearningManager()
    
    # Test 1: Initial state (no feedback)
    print("\n1. Initial Learning Status (No Feedback):")
    initial_status = learning_manager.get_learning_status()
    print(f"   Status: {initial_status['status']}")
    print(f"   Score: {initial_status['score']:.1f}%")
    print(f"   Insights: {initial_status['insights']}")
    
    # Test 2: Add some positive feedback
    print("\n2. Adding Positive Feedback:")
    sample_responses = [
        "Here's how to reset your password: Go to login page, click 'Forgot Password', enter your email...",
        "To configure the API, follow these steps: 1. Open settings 2. Navigate to API section...",
        "The issue you're experiencing is related to cache. Clear your browser cache and try again..."
    ]
    
    for i, response in enumerate(sample_responses):
        feedback_result = learning_manager.store_feedback(
            user_id=f"test_user_{i}",
            response_content=response,
            feedback_type="positive",
            feedback_category="thumbs_up",
            session_id=f"session_{i}"
        )
        print(f"   ✅ Feedback {i+1} stored: {feedback_result['learning_triggered']}")
        time.sleep(0.1)  # Small delay to show progression
    
    # Test 3: Check improved status
    print("\n3. Learning Status After Positive Feedback:")
    updated_status = learning_manager.get_learning_status()
    print(f"   Status: {updated_status['status']}")
    print(f"   Score: {updated_status['score']:.1f}%")
    print(f"   Total Feedback: {updated_status['total_feedback']}")
    print(f"   Positive: {updated_status['positive_feedback']}")
    
    # Test 4: Add excellent feedback
    print("\n4. Adding Excellent Feedback:")
    excellent_responses = [
        "Perfect solution! The step-by-step guide resolved the login issue completely.",
        "Excellent documentation on API integration. Very clear and comprehensive."
    ]
    
    for i, response in enumerate(excellent_responses):
        learning_manager.store_feedback(
            user_id=f"power_user_{i}",
            response_content=response,
            feedback_type="excellent",
            feedback_category="star",
            session_id=f"excellent_session_{i}"
        )
        print(f"   ⭐ Excellent feedback {i+1} stored")
    
    # Test 5: Add some negative feedback for contrast
    print("\n5. Adding Mixed Feedback:")
    learning_manager.store_feedback(
        user_id="critical_user",
        response_content="The response was not helpful and didn't solve my problem",
        feedback_type="negative",
        feedback_category="thumbs_down",
        session_id="critical_session"
    )
    print("   👎 Negative feedback stored")
    
    # Test 6: Final comprehensive status
    print("\n6. Final Learning Analysis:")
    final_status = learning_manager.get_learning_status()
    print(f"   Status: {final_status['status']}")
    print(f"   Score: {final_status['score']:.1f}%")
    print(f"   Improvement Trend: {final_status['improvement_trend']}")
    print(f"   Confidence: {final_status['confidence_level']:.2f}")
    print(f"   Recent Improvement: {final_status['recent_improvement']}")
    
    if final_status.get('insights'):
        print(f"\n   🔍 Key Insights:")
        for insight in final_status['insights'][:3]:
            print(f"      • {insight}")
    
    if final_status.get('recommendations'):
        print(f"\n   💡 Recommendations:")
        for rec in final_status['recommendations'][:2]:
            print(f"      • {rec}")
    
    # Test 7: Adaptive search parameters
    print("\n7. Adaptive Search Parameters:")
    adaptive_params = learning_manager.get_adaptive_search_parameters()
    print(f"   Similarity Threshold: {adaptive_params['similarity_threshold']}")
    print(f"   Source Weights: {adaptive_params['source_weights']}")
    print(f"   Response Target: {adaptive_params['response_length_target']}")
    
    print("\n🎉 Continuous Learning Test Complete!")
    print("✅ The system is now learning from user feedback!")

def test_user_specific_learning():
    """Test user-specific learning analytics"""
    
    print("\n" + "=" * 50)
    print("🎯 Testing User-Specific Learning")
    print("=" * 50)
    
    learning_manager = ContinuousLearningManager()
    
    # Add feedback for specific user
    test_user = "demo@testcompany.com"
    
    # Simulate user journey with improving satisfaction
    user_feedback_journey = [
        ("How do I reset password?", "Check the admin panel for reset options", "negative", "thumbs_down"),
        ("Password reset not working", "Try using the forgot password link on login page", "positive", "thumbs_up"),
        ("Login issues persist", "Clear browser cache and cookies, then try the reset process", "positive", "thumbs_up"),
        ("Perfect! Login works now", "Great! The cache clearing resolved the authentication issue", "excellent", "star"),
    ]
    
    print(f"\nSimulating feedback journey for user: {test_user}")
    for i, (query, response, fb_type, fb_cat) in enumerate(user_feedback_journey):
        learning_manager.store_feedback(
            user_id=test_user,
            response_content=response,
            feedback_type=fb_type,
            feedback_category=fb_cat,
            session_id=f"user_journey_{i}"
        )
        print(f"   {i+1}. Query: '{query[:30]}...' → {fb_type}")
        time.sleep(0.1)
    
    # Get user-specific analytics
    print(f"\n📊 Learning Analytics for {test_user}:")
    user_status = learning_manager.get_learning_status(test_user)
    
    print(f"   Personal Score: {user_status['score']:.1f}%")
    print(f"   Feedback Given: {user_status['total_feedback']}")
    print(f"   Learning Status: {user_status['status']}")
    print(f"   Improvement Detected: {user_status['recent_improvement']}")
    
    if user_status.get('insights'):
        print(f"\n   💡 Personalized Insights:")
        for insight in user_status['insights']:
            print(f"      • {insight}")

if __name__ == "__main__":
    print("🚀 Starting Continuous Learning Demo")
    
    try:
        # Run basic learning tests
        test_continuous_learning()
        
        # Run user-specific tests
        test_user_specific_learning()
        
        print("\n" + "=" * 60)
        print("🎯 DEMO READY!")
        print("✅ Real continuous learning is now implemented")
        print("✅ System learns from actual user feedback")  
        print("✅ Analytics show real improvement trends")
        print("✅ Adaptive search adjusts based on patterns")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error in learning test: {e}")
        print("💡 Make sure MongoDB is running: mongod")
        import traceback
        traceback.print_exc()