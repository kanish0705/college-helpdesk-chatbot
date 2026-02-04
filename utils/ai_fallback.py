"""
AI Fallback Module for College Helpdesk Chatbot

This module handles AI-based responses when the rule engine
doesn't find a matching answer in the knowledge base.

=============================================================================
GUARDRAIL ARCHITECTURE - How AI Usage is Controlled:
=============================================================================

LAYER 1: Conditional Activation
   - AI is ONLY called when rule_engine.find_answer() returns found=False
   - This ensures predefined answers are always preferred over AI

LAYER 2: System Prompt Constraints
   - Strict instructions limit AI to college-related topics only
   - AI is told to decline off-topic questions politely
   - AI is instructed to say "contact admin" when unsure (no hallucination)

LAYER 3: Post-Response Validation
   - After AI responds, we check if response seems out of scope
   - If AI accidentally went off-topic, we override with safe message

LAYER 4: Error Handling
   - If AI fails (API error, rate limit, etc.), fallback message is shown
   - User never sees raw errors

This multi-layer approach ensures:
1. AI is used sparingly (only when rules fail)
2. AI stays within college scope
3. Graceful degradation on failures
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import re
import config

# Try to import OpenAI library
# If not installed, AI features will be disabled
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. AI fallback disabled.")
    print("Install with: pip install openai")

# =============================================================================
# AI CONFIGURATION
# =============================================================================

# System prompt that defines how the AI should behave
# This is crucial for keeping responses within scope
SYSTEM_PROMPT = f"""You are a helpful assistant for {config.COLLEGE_NAME}'s helpdesk chatbot.

STRICT RULES YOU MUST FOLLOW:
1. Only answer questions related to college, education, and campus life
2. If asked about topics outside college scope, politely decline
3. Never make up information - if unsure, say "Please contact the college admin"
4. Keep responses concise and helpful (2-3 sentences max)
5. Be polite and professional
6. Never share personal opinions on sensitive topics
7. Don't provide information about specific students or staff
8. If asked to do something unethical, refuse politely

TOPICS YOU CAN HELP WITH:
- General college information
- Academic queries
- Campus facilities
- Student services
- Career guidance
- Study tips

TOPICS TO DECLINE:
- Personal advice unrelated to education
- Political or religious discussions
- Anything illegal or unethical
- Specific personal information about others

If you're not sure about something specific to this college, always say:
"I don't have specific information about that. Please contact the college administration for accurate details."
"""


# =============================================================================
# GUARDRAIL: Post-Response Content Filter
# =============================================================================

def is_response_out_of_scope(response):
    """
    GUARDRAIL: Validate AI response is within college scope.
    
    Even with strict system prompts, AI might occasionally drift off-topic.
    This function provides a second layer of protection by checking
    the AI's response for indicators it went out of scope.
    
    Args:
        response (str): The AI-generated response
    
    Returns:
        bool: True if response seems out of scope, False if acceptable
    """
    response_lower = response.lower()
    
    # Indicators that AI might have gone off-topic
    # (These are topics AI should have declined but might have answered)
    out_of_scope_indicators = [
        # Political/Religious
        "political party", "vote for", "election", "religious belief",
        "god", "prayer", "worship",
        # Personal/Dating
        "relationship advice", "dating tips", "love life",
        # Financial (non-college)
        "stock market", "cryptocurrency", "bitcoin", "invest in",
        # Medical (should defer to professionals)
        "medical diagnosis", "prescription", "you should take",
        # Legal advice
        "legal advice", "lawyer", "sue them",
    ]
    
    for indicator in out_of_scope_indicators:
        if indicator in response_lower:
            return True
    
    return False


def is_query_college_related(query):
    """
    GUARDRAIL: Pre-check if query seems college-related.
    
    This is an additional filter before sending to AI.
    Helps reduce unnecessary API calls for clearly off-topic queries.
    
    Args:
        query (str): The user's query
    
    Returns:
        bool: True if likely college-related, False otherwise
    """
    query_lower = query.lower()
    
    # Keywords that indicate college-related queries
    college_keywords = [
        # Academic
        "admission", "course", "class", "exam", "result", "grade",
        "assignment", "project", "semester", "syllabus", "subject",
        "lecture", "professor", "teacher", "faculty", "department",
        # Administrative
        "fee", "scholarship", "certificate", "document", "form",
        "registration", "enrollment", "attendance", "timetable",
        # Campus
        "hostel", "library", "lab", "canteen", "bus", "transport",
        "wifi", "sports", "event", "club", "fest",
        # Career
        "placement", "internship", "job", "career", "interview",
        # General
        "college", "university", "campus", "student", "study"
    ]
    
    # Check if any college keyword is present
    for keyword in college_keywords:
        if keyword in query_lower:
            return True
    
    # If no keywords found, it might still be college-related
    # Let AI handle it, but with strict system prompt
    return True  # Default to True to allow general queries


# =============================================================================
# AI RESPONSE FUNCTION
# =============================================================================

def get_ai_response(user_message):
    """
    Get a response from OpenAI's GPT model.
    
    =======================================================================
    GUARDRAIL FLOW:
    1. Check if OpenAI is available and configured
    2. Send query with strict system prompt (LAYER 2)
    3. Validate AI response for out-of-scope content (LAYER 3)
    4. Return safe response or fallback (LAYER 4)
    =======================================================================
    
    This function:
    1. Checks if OpenAI is available
    2. Sends the user's query with strict system instructions
    3. Returns the AI's response or a fallback message
    
    Args:
        user_message (str): The user's query
    
    Returns:
        dict: {
            "success": bool,  # Whether AI response was successful
            "answer": str     # The response message
        }
    """
    
    # Check if OpenAI library is available
    if not OPENAI_AVAILABLE:
        return {
            "success": False,
            "answer": config.FALLBACK_MESSAGE
        }
    
    # Check if API key is configured
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your-openai-api-key-here":
        return {
            "success": False,
            "answer": config.FALLBACK_MESSAGE
        }
    
    try:
        # Initialize OpenAI client with API key
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Make API call to GPT
        response = client.chat.completions.create(
            model=config.AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=0.7,  # Controls randomness (0=focused, 1=creative)
            top_p=0.9  # Controls diversity of responses
        )
        
        # Extract the response text
        ai_answer = response.choices[0].message.content.strip()
        
        # Validate response is not empty
        if not ai_answer:
            return {
                "success": False,
                "answer": config.FALLBACK_MESSAGE
            }
        
        # =================================================================
        # GUARDRAIL: Post-response validation
        # Even after AI responds, we verify it stays within scope
        # This is a second layer of protection against AI hallucination
        # =================================================================
        
        # Check if AI response contains out-of-scope indicators
        if is_response_out_of_scope(ai_answer):
            return {
                "success": True,
                "answer": config.OFF_TOPIC_MESSAGE
            }
        
        return {
            "success": True,
            "answer": ai_answer
        }
        
    except openai.AuthenticationError:
        # Invalid API key
        print("Error: Invalid OpenAI API key")
        return {
            "success": False,
            "answer": config.FALLBACK_MESSAGE
        }
        
    except openai.RateLimitError:
        # Too many requests or quota exceeded
        print("Error: OpenAI rate limit exceeded")
        return {
            "success": False,
            "answer": "I'm currently experiencing high demand. Please try again in a moment or contact the admin office."
        }
        
    except openai.APIConnectionError:
        # Network issues
        print("Error: Could not connect to OpenAI API")
        return {
            "success": False,
            "answer": config.FALLBACK_MESSAGE
        }
        
    except Exception as e:
        # Any other unexpected error
        print(f"Error in AI fallback: {str(e)}")
        return {
            "success": False,
            "answer": config.FALLBACK_MESSAGE
        }


# =============================================================================
# SIMPLE FALLBACK (No AI)
# =============================================================================

def get_simple_fallback(user_message):
    """
    A simple fallback without AI.
    Use this if you don't want to use OpenAI.
    
    This function provides basic responses based on keyword detection.
    
    Args:
        user_message (str): The user's query
    
    Returns:
        dict: Response dictionary
    """
    message_lower = user_message.lower()
    
    # Simple keyword-based responses
    if any(word in message_lower for word in ['help', 'assist', 'support']):
        return {
            "success": True,
            "answer": "I'm here to help! You can ask me about admissions, courses, fees, timings, and other college-related topics. What would you like to know?"
        }
    
    if any(word in message_lower for word in ['contact', 'phone', 'email', 'reach']):
        return {
            "success": True,
            "answer": f"You can reach {config.COLLEGE_NAME} at the main office. Please visit the college website or the 'Contact' section for detailed contact information."
        }
    
    if any(word in message_lower for word in ['admission', 'apply', 'join', 'enroll']):
        return {
            "success": True,
            "answer": "For admission-related queries, please visit the Admissions Office or check our website for the application process and requirements."
        }
    
    # Default fallback
    return {
        "success": False,
        "answer": config.FALLBACK_MESSAGE
    }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    """
    Test the AI fallback module.
    Run this file directly: python ai_fallback.py
    """
    print("="*60)
    print("AI Fallback Test")
    print("="*60)
    print(f"OpenAI Available: {OPENAI_AVAILABLE}")
    
    test_queries = [
        "What courses should I take for software development?",
        "How can I improve my grades?",
        "Tell me about campus life"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = get_ai_response(query)
        print(f"Success: {result['success']}")
        print(f"Answer: {result['answer']}")
        print("-"*40)
