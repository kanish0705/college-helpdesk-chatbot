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
import requests
import json

# Try to import OpenAI library
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Google Generative AI library
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Groq uses OpenAI-compatible API, so we'll use requests
GROQ_AVAILABLE = True  # Always available via HTTP requests

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
    # Route to appropriate provider
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "openai":
        return get_openai_response(user_message)
    elif provider == "gemini":
        return get_gemini_response(user_message)
    elif provider == "groq":
        return get_groq_response(user_message)
    else:
        return {
            "success": False,
            "answer": config.FALLBACK_MESSAGE
        }


# =============================================================================
# OPENAI PROVIDER
# =============================================================================

def get_openai_response(user_message):
    """Get response from OpenAI GPT models."""
    
    if not OPENAI_AVAILABLE:
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your-openai-api-key-here":
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    
    try:
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=0.7
        )
        
        ai_answer = response.choices[0].message.content.strip()
        
        if not ai_answer:
            return {"success": False, "answer": config.FALLBACK_MESSAGE}
        
        if is_response_out_of_scope(ai_answer):
            return {"success": True, "answer": config.OFF_TOPIC_MESSAGE}
        
        return {"success": True, "answer": ai_answer}
        
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        return {"success": False, "answer": config.FALLBACK_MESSAGE}


# =============================================================================
# GOOGLE GEMINI PROVIDER
# =============================================================================

def get_gemini_response(user_message):
    """Get response from Google Gemini models."""
    
    if not GEMINI_AVAILABLE:
        # Try using REST API as fallback
        return get_gemini_rest_response(user_message)
    
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your-gemini-api-key-here":
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        # Combine system prompt with user message
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {user_message}"
        
        response = model.generate_content(full_prompt)
        ai_answer = response.text.strip()
        
        if not ai_answer:
            return {"success": False, "answer": config.FALLBACK_MESSAGE}
        
        if is_response_out_of_scope(ai_answer):
            return {"success": True, "answer": config.OFF_TOPIC_MESSAGE}
        
        return {"success": True, "answer": ai_answer}
        
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        return {"success": False, "answer": config.FALLBACK_MESSAGE}


def get_gemini_rest_response(user_message):
    """Fallback: Use Gemini via REST API if library not installed."""
    
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your-gemini-api-key-here":
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
        
        headers = {"Content-Type": "application/json"}
        params = {"key": config.GEMINI_API_KEY}
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {user_message}"
        
        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": config.MAX_TOKENS}
        }
        
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        if is_response_out_of_scope(ai_answer):
            return {"success": True, "answer": config.OFF_TOPIC_MESSAGE}
        
        return {"success": True, "answer": ai_answer}
        
    except Exception as e:
        print(f"Gemini REST Error: {str(e)}")
        return {"success": False, "answer": config.FALLBACK_MESSAGE}


# =============================================================================
# GROQ PROVIDER (FREE - Recommended)
# =============================================================================

def get_groq_response(user_message):
    """
    Get response from Groq (ultra-fast LLM inference).
    FREE tier available at: https://console.groq.com/keys
    """
    
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "your-groq-api-key-here":
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": config.MAX_TOKENS,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_answer = result["choices"][0]["message"]["content"].strip()
        
        if not ai_answer:
            return {"success": False, "answer": config.FALLBACK_MESSAGE}
        
        if is_response_out_of_scope(ai_answer):
            return {"success": True, "answer": config.OFF_TOPIC_MESSAGE}
        
        return {"success": True, "answer": ai_answer}
        
    except requests.exceptions.Timeout:
        print("Groq Error: Request timed out")
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    except requests.exceptions.RequestException as e:
        print(f"Groq Error: {str(e)}")
        return {"success": False, "answer": config.FALLBACK_MESSAGE}
    except Exception as e:
        print(f"Groq Error: {str(e)}")
        return {"success": False, "answer": config.FALLBACK_MESSAGE}


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
