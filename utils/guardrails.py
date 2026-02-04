"""
Guardrails Module for College Helpdesk Chatbot

=============================================================================
WHAT ARE GUARDRAILS?
=============================================================================
Guardrails are safety checks that filter user input BEFORE processing.
Think of them as security guards at the entrance - they check everyone
before allowing them inside.

=============================================================================
WHY DO WE NEED GUARDRAILS?
=============================================================================
1. SAFETY: Block abusive, offensive, or harmful content
2. SCOPE: Keep chatbot focused on college topics only
3. PRIVACY: Prevent sharing/collecting personal information
4. QUALITY: Filter spam and invalid inputs
5. COST: Avoid sending inappropriate queries to AI (saves API costs)

=============================================================================
GUARDRAILS IMPLEMENTED IN THIS MODULE:
=============================================================================
┌─────────────────────────────────────────────────────────────────────────┐
│ GUARDRAIL 1: Input Validation                                          │
│ - Rejects empty, too short, or too long messages                       │
│ - Ensures message contains actual text                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ GUARDRAIL 2: Spam Detection                                            │
│ - Blocks repeated characters (aaaaaaa)                                 │
│ - Blocks ALL CAPS messages (shouting)                                  │
│ - Blocks excessive punctuation (!!!!!!)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ GUARDRAIL 3: Abusive Content Filter                                    │
│ - Blocks offensive/inappropriate words                                 │
│ - Blocks hacking/security threat terms                                 │
│ - Returns polite decline message                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ GUARDRAIL 4: Personal Questions Filter                                 │
│ - Blocks questions about individuals' personal lives                   │
│ - Blocks salary, relationship, address queries                         │
│ - Protects privacy of faculty and staff                                │
├─────────────────────────────────────────────────────────────────────────┤
│ GUARDRAIL 5: Off-Topic Filter                                          │
│ - Blocks politics, religion, entertainment queries                     │
│ - Keeps chatbot focused on college matters                             │
│ - Returns helpful redirect message                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ GUARDRAIL 6: Personal Information Protection                           │
│ - Detects phone numbers, emails, Aadhar numbers                        │
│ - Prevents users from sharing sensitive data                           │
│ - Protects user privacy                                                │
└─────────────────────────────────────────────────────────────────────────┘

=============================================================================
FLOW: How Guardrails Work
=============================================================================
User Input → Guardrail 1 → Guardrail 2 → ... → Guardrail 6 → Process
                ↓              ↓                    ↓
           (if fails)     (if fails)           (if fails)
                ↓              ↓                    ↓
           Return safe    Return safe          Return safe
           error message  error message        error message

If ANY guardrail fails, processing STOPS and a safe message is returned.
The AI is NEVER called for blocked messages.
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import re
import config

# =============================================================================
# GUARDRAIL 1: INPUT VALIDATION
# =============================================================================

def is_valid_input(message):
    """
    ┌─────────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL 1: Input Validation                                       │
    ├─────────────────────────────────────────────────────────────────────┤
    │ PURPOSE: Ensure the message is a valid, processable input          │
    │                                                                     │
    │ CHECKS:                                                             │
    │ - Not empty or whitespace-only                                      │
    │ - At least 2 characters long                                        │
    │ - Not longer than 500 characters (prevents spam)                    │
    │ - Contains at least some letters (not just symbols)                 │
    │                                                                     │
    │ WHY: Invalid inputs waste processing and can cause errors           │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        message (str): The user's message
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # Check if message is empty or only whitespace
    if not message or not message.strip():
        return False, "Please enter a message."
    
    # Remove extra whitespace
    cleaned = message.strip()
    
    # Check minimum length (at least 2 characters)
    # Single character messages are usually accidental
    if len(cleaned) < 2:
        return False, "Your message is too short. Please provide more details."
    
    # Check maximum length (prevent spam/abuse)
    # Very long messages are often spam or copy-pasted content
    if len(cleaned) > 500:
        return False, "Your message is too long. Please keep it under 500 characters."
    
    # Check if message contains at least some letters
    # Messages with only numbers/symbols are usually invalid
    if not re.search(r'[a-zA-Z]', cleaned):
        return False, "Please enter a valid message with some text."
    
    return True, ""


# =============================================================================
# GUARDRAIL 2: SPAM DETECTION
# =============================================================================

def is_spam(message):
    """
    ┌─────────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL 2: Spam Detection                                         │
    ├─────────────────────────────────────────────────────────────────────┤
    │ PURPOSE: Filter out spam and low-quality messages                   │
    │                                                                     │
    │ CHECKS:                                                             │
    │ - Repeated characters (e.g., "aaaaaaaaaa", "!!!!!!!!!")             │
    │ - All uppercase messages (considered "shouting")                    │
    │ - Excessive punctuation (e.g., "what???!!!")                        │
    │                                                                     │
    │ WHY: Spam wastes resources and degrades user experience             │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        message (str): The user's message
    
    Returns:
        bool: True if spam detected, False otherwise
    """
    # Check for repeated characters (e.g., "aaaaaaaa", "!!!!!!")
    # Pattern: any character repeated 6+ times consecutively
    if re.search(r'(.)\1{5,}', message):
        return True
    
    # Check if entire message is uppercase (shouting)
    # Only apply to messages longer than 10 chars to avoid false positives
    # Short messages like "OK" or "YES" are acceptable
    if len(message) > 10 and message.isupper():
        return True
    
    # Check for excessive punctuation
    # More than 10 punctuation marks suggests spam or frustration
    punctuation_count = len(re.findall(r'[!?.,]', message))
    if punctuation_count > 10:
        return True
    
    return False


# =============================================================================
# GUARDRAIL 3: ABUSIVE/INAPPROPRIATE CONTENT FILTER
# =============================================================================

def contains_blocked_words(message):
    """
    ┌─────────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL 3: Abusive/Inappropriate Content Filter                   │
    ├─────────────────────────────────────────────────────────────────────┤
    │ PURPOSE: Block offensive, abusive, or inappropriate content         │
    │                                                                     │
    │ BLOCKS:                                                             │
    │ - Profanity and insults                                             │
    │ - Hacking/security threat terms                                     │
    │ - Violence-related words                                            │
    │ - Fraud-related terms                                               │
    │                                                                     │
    │ WHY: Protects the system from misuse and maintains professionalism  │
    │                                                                     │
    │ RESPONSE: Returns BLOCKED_CONTENT_MESSAGE from config               │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        message (str): The user's message
    
    Returns:
        bool: True if blocked words found, False otherwise
    """
    message_lower = message.lower()
    
    for word in config.BLOCKED_WORDS:
        # Use word boundary (\b) to match whole words only
        # This prevents false positives:
        # - "password" won't match "passwords" 
        # - "hack" won't match "hackathon"
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, message_lower):
            return True
    
    return False


# =============================================================================
# GUARDRAIL 4: PERSONAL QUESTIONS FILTER
# =============================================================================

def is_personal_question(message):
    """
    ┌─────────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL 4: Personal Questions Filter                              │
    ├─────────────────────────────────────────────────────────────────────┤
    │ PURPOSE: Block questions about individuals' personal lives          │
    │                                                                     │
    │ BLOCKS QUESTIONS ABOUT:                                             │
    │ - Faculty/staff personal relationships                              │
    │ - Salaries and income                                               │
    │ - Home addresses and phone numbers                                  │
    │ - Ages and private matters                                          │
    │                                                                     │
    │ WHY: Protects privacy of college faculty, staff, and students       │
    │                                                                     │
    │ RESPONSE: Returns PERSONAL_QUESTION_MESSAGE from config             │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        message (str): The user's message
    
    Returns:
        bool: True if personal question detected, False otherwise
    """
    message_lower = message.lower()
    
    # Check against personal question keywords from config
    for keyword in config.PERSONAL_QUESTION_KEYWORDS:
        if keyword in message_lower:
            return True
    
    # Additional pattern checks for personal questions
    personal_patterns = [
        r"what is .+ (phone|number|address|salary)",  # "what is professor's phone"
        r"where does .+ live",                         # "where does the HOD live"
        r"how old is",                                 # "how old is the principal"
        r"is .+ (married|single|dating)",             # relationship status
        r"tell me about .+ personal",                 # personal information requests
    ]
    
    for pattern in personal_patterns:
        if re.search(pattern, message_lower):
            return True
    
    return False


# =============================================================================
# GUARDRAIL 5: OFF-TOPIC FILTER
# =============================================================================

def is_off_topic(message):
    """
    ┌─────────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL 5: Off-Topic (Non-College) Filter                         │
    ├─────────────────────────────────────────────────────────────────────┤
    │ PURPOSE: Keep chatbot focused on college-related queries only       │
    │                                                                     │
    │ BLOCKS:                                                             │
    │ - Political discussions (elections, government, parties)            │
    │ - Religious topics (god, prayer, temples, churches)                 │
    │ - Entertainment (movies, sports scores, gaming)                     │
    │ - Financial advice (stocks, crypto, gambling)                       │
    │ - Personal life advice (relationships, life decisions)              │
    │                                                                     │
    │ WHY: The chatbot is designed for college help only.                 │
    │      Answering off-topic queries would:                             │
    │      - Confuse users about the chatbot's purpose                    │
    │      - Risk providing incorrect information                         │
    │      - Waste AI resources on non-college queries                    │
    │                                                                     │
    │ RESPONSE: Returns OFF_TOPIC_MESSAGE from config                     │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        message (str): The user's message
    
    Returns:
        bool: True if off-topic, False otherwise
    """
    message_lower = message.lower()
    
    # Check against off-topic keywords from config
    for keyword in config.OFF_TOPIC_KEYWORDS:
        if keyword in message_lower:
            return True
    
    return False


# =============================================================================
# GUARDRAIL 6: PERSONAL INFORMATION PROTECTION
# =============================================================================

def contains_personal_info(message):
    """
    ┌─────────────────────────────────────────────────────────────────────┐
    │ GUARDRAIL 6: Personal Information Protection                        │
    ├─────────────────────────────────────────────────────────────────────┤
    │ PURPOSE: Prevent users from sharing their own personal data         │
    │                                                                     │
    │ DETECTS:                                                            │
    │ - Phone numbers (Indian 10-digit format)                            │
    │ - Email addresses                                                   │
    │ - Aadhar numbers (12 digits)                                        │
    │ - Credit card patterns                                              │
    │                                                                     │
    │ WHY: We should NOT collect or store personal information.           │
    │      This protects:                                                 │
    │      - User privacy                                                 │
    │      - Compliance with data protection                              │
    │      - System from storing sensitive data                           │
    │                                                                     │
    │ RESPONSE: Returns PRIVACY_MESSAGE from config                       │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        message (str): The user's message
    
    Returns:
        bool: True if personal info detected, False otherwise
    """
    # Phone number pattern (Indian format: 10 digits starting with 6-9)
    phone_pattern = r'\b[6-9]\d{9}\b'
    if re.search(phone_pattern, message):
        return True
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, message):
        return True
    
    # Aadhar number pattern (12 digits, optionally with spaces)
    aadhar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    if re.search(aadhar_pattern, message):
        return True
    
    # Credit card pattern (16 digits, optionally with spaces/dashes)
    card_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    if re.search(card_pattern, message):
        return True
    
    return False


# =============================================================================
# MAIN GUARDRAIL CHECK
# =============================================================================

def check_guardrails(message):
    """
    Main function to run all guardrail checks on a message.
    
    This is the primary function called by the main app.
    It runs all safety checks in order.
    
    Args:
        message (str): The user's message
    
    Returns:
        dict: {
            "is_safe": bool,      # Whether message passed all checks
            "message": str,       # Error message if not safe
            "failed_check": str   # Which check failed (for logging)
        }
    """
    
    # Check 1: Validate input format
    is_valid, error_msg = is_valid_input(message)
    if not is_valid:
        return {
            "is_safe": False,
            "message": error_msg,
            "failed_check": "input_validation"
        }
    
    # Check 2: Spam detection
    if is_spam(message):
        return {
            "is_safe": False,
            "message": "Please send a proper message without excessive repetition.",
            "failed_check": "spam_detection"
        }
    
    # =========================================================================
    # Check 3: Abusive/Inappropriate Content
    # Blocks offensive words, hacking terms, violence, fraud
    # =========================================================================
    if contains_blocked_words(message):
        return {
            "is_safe": False,
            "message": config.BLOCKED_CONTENT_MESSAGE,
            "failed_check": "blocked_words"
        }
    
    # =========================================================================
    # Check 4: Personal Questions About Individuals
    # Blocks questions about faculty/staff personal lives
    # =========================================================================
    if is_personal_question(message):
        return {
            "is_safe": False,
            "message": config.PERSONAL_QUESTION_MESSAGE,
            "failed_check": "personal_question"
        }
    
    # =========================================================================
    # Check 5: Off-Topic (Non-College) Content
    # Blocks politics, religion, entertainment, etc.
    # =========================================================================
    if is_off_topic(message):
        return {
            "is_safe": False,
            "message": config.OFF_TOPIC_MESSAGE,
            "failed_check": "off_topic"
        }
    
    # =========================================================================
    # Check 6: Personal Information Protection
    # Prevents users from sharing phone numbers, emails, IDs
    # =========================================================================
    if contains_personal_info(message):
        return {
            "is_safe": False,
            "message": config.PRIVACY_MESSAGE,
            "failed_check": "personal_info"
        }
    
    # =========================================================================
    # ALL CHECKS PASSED
    # Message is safe to process through rule engine and (if needed) AI
    # =========================================================================
    return {
        "is_safe": True,
        "message": "",
        "failed_check": None
    }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    """
    Test the guardrails module.
    Run this file directly: python guardrails.py
    """
    test_messages = [
        # Valid messages (should pass)
        ("Hello, I need help", "Valid greeting"),
        ("What are the admission requirements?", "Valid college query"),
        ("Tell me about courses", "Valid college query"),
        
        # Invalid input (Guardrail 1)
        ("", "Empty message"),
        ("x", "Too short"),
        
        # Spam (Guardrail 2)
        ("aaaaaaaaaaaaaaa", "Repeated characters"),
        ("HELP ME RIGHT NOW!!!!", "All caps shouting"),
        
        # Abusive content (Guardrail 3)
        ("How can I hack the system?", "Hacking term"),
        ("You are stupid", "Insult"),
        
        # Personal questions (Guardrail 4)
        ("What is the professor's salary?", "Salary question"),
        ("Where does the HOD live?", "Address question"),
        ("Is the dean married?", "Personal life question"),
        
        # Off-topic (Guardrail 5)
        ("Tell me about politics", "Political topic"),
        ("Which god should I pray to?", "Religious topic"),
        ("What's the cricket score?", "Entertainment"),
        
        # Personal info (Guardrail 6)
        ("My phone is 9876543210", "Phone number"),
        ("Email me at test@email.com", "Email address"),
    ]
    
    print("="*70)
    print("  GUARDRAILS TEST SUITE")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for msg, description in test_messages:
        result = check_guardrails(msg)
        status = "✓ PASS" if not result['is_safe'] or description.startswith("Valid") else "✗ FAIL"
        
        print(f"\n[{description}]")
        print(f"  Message: '{msg[:50]}{'...' if len(msg) > 50 else ''}'")
        print(f"  Safe: {result['is_safe']}")
        if not result['is_safe']:
            print(f"  Blocked by: {result['failed_check']}")
            print(f"  Response: {result['message'][:60]}...")
        print("-"*70)
