"""
Configuration file for the College Helpdesk Chatbot.
Contains all settings and constants used across the application.
"""

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Name of your college (customize this)
COLLEGE_NAME = "ABC College of Engineering"

# Flask application settings
DEBUG_MODE = True  # Set to False in production
SECRET_KEY = "your-secret-key-change-in-production"

# =============================================================================
# AI SETTINGS
# =============================================================================

# Choose your LLM provider: "openai", "gemini", or "groq"
# - openai: GPT-3.5/GPT-4 (paid, most capable)
# - gemini: Google's Gemini (free tier available)
# - groq: Ultra-fast inference (free tier available)
LLM_PROVIDER = "groq"  # Change this to switch providers

# =============================================================================
# OpenAI Configuration
# Get your API key from: https://platform.openai.com/api-keys
# =============================================================================
OPENAI_API_KEY = "your-openai-api-key-here"
OPENAI_MODEL = "gpt-3.5-turbo"  # Options: gpt-3.5-turbo, gpt-4, gpt-4-turbo

# =============================================================================
# Google Gemini Configuration
# Get your API key from: https://makersuite.google.com/app/apikey
# =============================================================================
GEMINI_API_KEY = "your-gemini-api-key-here"
GEMINI_MODEL = "gemini-1.5-flash"  # Options: gemini-1.5-flash, gemini-1.5-pro

# =============================================================================
# Groq Configuration (FREE - Recommended for testing)
# Get your API key from: https://console.groq.com/keys
# =============================================================================
GROQ_API_KEY = "your-groq-api-key-here"
GROQ_MODEL = "llama-3.1-8b-instant"  # Options: llama-3.1-8b-instant, mixtral-8x7b-32768

# Maximum tokens for AI response (controls response length)
MAX_TOKENS = 150

# =============================================================================
# RULE ENGINE SETTINGS
# =============================================================================

# Minimum similarity score to consider a match (0.0 to 1.0)
# Higher value = more strict matching
SIMILARITY_THRESHOLD = 0.6

# =============================================================================
# GUARDRAIL SETTINGS
# =============================================================================

# =============================================================================
# GUARDRAIL 1: Abusive/Inappropriate Content Filter
# =============================================================================
# List of blocked/offensive words that indicate abusive or inappropriate input.
# When detected, the chatbot refuses to process and returns a polite decline.
# This protects the system from being used for harmful purposes.
BLOCKED_WORDS = [
    # Hacking/Security threats
    "hack", "cheat", "exploit", "crack", "breach",
    # Inappropriate content indicators
    "inappropriate", "offensive", "abuse", "harass",
    # Profanity indicators (add actual words as needed)
    "stupid", "idiot", "dumb",
    # Violence-related
    "kill", "attack", "threat", "bomb",
    # Fraud-related
    "fake", "forge", "bribe"
]

# =============================================================================
# GUARDRAIL 2: Personal Questions Filter
# =============================================================================
# Keywords that indicate personal questions about individuals.
# The chatbot should not answer questions about specific people's
# personal details, relationships, or private matters.
PERSONAL_QUESTION_KEYWORDS = [
    "girlfriend", "boyfriend", "wife", "husband", "married",
    "salary", "income", "how much earn", "personal life",
    "home address", "where does", "live", "phone number of",
    "age of", "how old is", "private", "secret"
]

# =============================================================================
# GUARDRAIL 3: Non-College Topics Filter
# =============================================================================
# Topics that are outside college scope.
# The chatbot politely declines these to stay focused on its purpose.
OFF_TOPIC_KEYWORDS = [
    # Political topics
    "politics", "election", "vote", "government", "minister", "party",
    # Religious topics
    "religion", "god", "prayer", "temple", "church", "mosque",
    # Entertainment/Personal
    "dating", "movie", "cricket", "football", "game score",
    # Financial (non-college)
    "gambling", "betting", "cryptocurrency", "bitcoin", "stock market",
    # Personal advice
    "personal advice", "relationship advice", "life advice",
    # Other inappropriate
    "illegal", "drugs", "alcohol"
]

# =============================================================================
# GUARDRAIL 4: Safe Fallback Responses
# =============================================================================
# These are safe, pre-defined responses used when guardrails are triggered.
# They are polite, non-offensive, and guide users back to appropriate queries.

# Default response when chatbot cannot help (AI failed or no match)
FALLBACK_MESSAGE = "I'm sorry, I couldn't find an answer to your question. Please contact the college admin office for further assistance."

# Response for off-topic queries (politics, religion, etc.)
OFF_TOPIC_MESSAGE = "I can only help with college-related queries. Please ask questions about admissions, courses, fees, timings, faculty, or other college matters."

# Response for blocked/abusive content
BLOCKED_CONTENT_MESSAGE = "I cannot respond to this type of query. Please keep your questions appropriate and college-related."

# Response for personal questions about individuals
PERSONAL_QUESTION_MESSAGE = "I cannot provide personal information about individuals. For faculty contact details, please visit the college website or contact the admin office."

# Response for privacy protection (when user shares personal data)
PRIVACY_MESSAGE = "For your privacy and security, please don't share personal information like phone numbers, email addresses, or ID numbers in this chat."
