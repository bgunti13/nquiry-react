
"""
Environment Detection Utility for MNHT/MNLS Tickets
Auto-detects environment from user queries and implements follow-up questions when needed.
"""

import re
from typing import Dict, Optional, Tuple

def detect_environment_from_query(query: str) -> Tuple[Optional[str], float]:
    """
    Auto-detect environment from user query
    
    Args:
        query: User's query text
        
    Returns:
        Tuple of (detected_environment, confidence_score)
        - environment: 'production', 'staging', or None if not detected
        - confidence: 0.0 to 1.0 indicating detection confidence
    """
    query_lower = query.lower()
    
    # Production keywords with confidence scores
    production_keywords = {
        'production': 1.0,
        'prod': 0.9,
        'live': 0.8,
        'main': 0.6,
        'live environment': 1.0,
        'production environment': 1.0,
        'prod env': 0.9,
        'production system': 0.9,
        'live system': 0.8
    }
    
    # Staging keywords with confidence scores  
    staging_keywords = {
        'staging': 1.0,
        'stage': 0.9,
        'test': 0.7,
        'testing': 0.7,
        'dev': 0.6,
        'development': 0.8,
        'staging environment': 1.0,
        'test environment': 0.8,
        'development environment': 0.8,
        'staging env': 0.9,
        'test env': 0.7,
        'dev env': 0.6
    }
    
    max_prod_score = 0.0
    max_staging_score = 0.0
    
    # Check for production keywords
    for keyword, confidence in production_keywords.items():
        if keyword in query_lower:
            max_prod_score = max(max_prod_score, confidence)
    
    # Check for staging keywords  
    for keyword, confidence in staging_keywords.items():
        if keyword in query_lower:
            max_staging_score = max(max_staging_score, confidence)
    
    # Determine result based on highest confidence
    if max_prod_score >= max_staging_score and max_prod_score >= 0.6:
        return 'production', max_prod_score
    elif max_staging_score > max_prod_score and max_staging_score >= 0.6:
        return 'staging', max_staging_score
    else:
        # No clear environment detected
        return None, 0.0

def get_environment_follow_up_question() -> str:
    """
    Get the follow-up question to ask when environment cannot be auto-detected
    
    Returns:
        Question string to present to user
    """
    return "Which environment is affected by this issue? (production or staging)"

def validate_environment_response(response: str) -> Optional[str]:
    """
    Validate and normalize user response for environment
    
    Args:
        response: User's response to environment question
        
    Returns:
        Normalized environment ('production' or 'staging') or None if invalid
    """
    response_lower = response.lower().strip()
    
    # Production variations
    if any(word in response_lower for word in ['production', 'prod', 'live', '1']):
        return 'production'
    
    # Staging variations  
    if any(word in response_lower for word in ['staging', 'stage', 'test', 'dev', '2']):
        return 'staging'
    
    return None

def should_ask_environment_question(query: str, confidence_threshold: float = 0.7) -> bool:
    """
    Determine if we should ask environment question based on detection confidence
    
    Args:
        query: User's original query
        confidence_threshold: Minimum confidence to auto-populate (default 0.7)
        
    Returns:
        True if we should ask the question, False if auto-detection is sufficient
    """
    environment, confidence = detect_environment_from_query(query)
    
    # If no environment detected or confidence is low, ask question
    if environment is None or confidence < confidence_threshold:
        return True
    
    return False

def process_mnht_mnls_environment(query: str, user_response: str = None) -> Dict:
    """
    Complete environment processing for MNHT/MNLS tickets
    
    Args:
        query: Original user query
        user_response: Optional response if we asked follow-up question
        
    Returns:
        Dictionary with environment processing results
    """
    result = {
        'environment': None,
        'auto_detected': False,
        'confidence': 0.0,
        'needs_question': False,
        'question': None,
        'error': None
    }
    
    # If user provided response to follow-up question
    if user_response:
        validated_env = validate_environment_response(user_response)
        if validated_env:
            result['environment'] = validated_env
            result['auto_detected'] = False
            result['confidence'] = 1.0  # User provided explicit answer
            return result
        else:
            result['error'] = f"Invalid environment response: '{user_response}'. Please specify 'production' or 'staging'."
            result['needs_question'] = True
            result['question'] = get_environment_follow_up_question()
            return result
    
    # Try auto-detection from query
    detected_env, confidence = detect_environment_from_query(query)
    
    if detected_env and confidence >= 0.7:
        # High confidence auto-detection
        result['environment'] = detected_env
        result['auto_detected'] = True
        result['confidence'] = confidence
        print(f"🎯 Auto-detected environment: {detected_env} (confidence: {confidence:.1%})")
    else:
        # Low confidence or no detection - ask user
        result['needs_question'] = True
        result['question'] = get_environment_follow_up_question()
        if detected_env:
            print(f"⚠️ Low confidence environment detection: {detected_env} ({confidence:.1%}) - asking user")
        else:
            print(f"❓ No environment detected in query - asking user")
    
    return result

# Test function
if __name__ == "__main__":
    # Test cases
    test_queries = [
        "Database is slow in production",
        "Can you refresh the staging database?", 
        "Application is down in prod environment",
        "Need to test new feature in dev",
        "System error occurred",  # No environment mentioned
        "Issue with live system performance",
        "Staging deployment failed"
    ]
    
    print("🧪 Testing Environment Detection")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = process_mnht_mnls_environment(query)
        
        if result['environment']:
            detection_type = "Auto-detected" if result['auto_detected'] else "User provided"
            print(f"✅ {detection_type}: {result['environment']} (confidence: {result['confidence']:.1%})")
        elif result['needs_question']:
            print(f"❓ Needs follow-up: {result['question']}")
        
        if result['error']:
            print(f"❌ Error: {result['error']}")