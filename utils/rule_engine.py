"""
Rule Engine Module for Personalized College Helpdesk Chatbot

This module handles:
1. Personalized responses based on student profile (dept/sem/section)
2. Room location queries with floor/wing info
3. Timetable queries
4. Notification matching
5. Knowledge base pattern matching
"""

import json
import os
import re
import random
from datetime import datetime
from difflib import SequenceMatcher

import config

# =============================================================================
# DATA LOADING
# =============================================================================

def load_knowledge_base():
    """Load the knowledge base from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(current_dir, "..", "knowledge_base.json")
    
    try:
        with open(kb_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"intents": []}


def load_admin_data():
    """Load admin data from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    admin_path = os.path.join(current_dir, "..", "admin_data.json")
    
    try:
        with open(admin_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# =============================================================================
# TEXT PREPROCESSING
# =============================================================================

def preprocess_text(text):
    """Clean and normalize text for matching."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = ' '.join(text.split())
    return text


def get_keywords(text):
    """Extract important keywords from text."""
    stop_words = {
        'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it',
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'can', 'may', 'might', 'must', 'shall', 'to', 'of', 'in',
        'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
        'and', 'but', 'or', 'so', 'if', 'then', 'than', 'when', 'where',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
        'am', 'about', 'please', 'tell', 'know', 'want', 'need', 'like',
        'get', 'give', 'make', 'how', 'there', 'here', 'just', 'also', 'show'
    }
    words = preprocess_text(text).split()
    return [word for word in words if word not in stop_words]


def calculate_similarity(text1, text2):
    """Calculate similarity between two texts."""
    return SequenceMatcher(None, text1, text2).ratio()


# =============================================================================
# PERSONALIZED RESPONSES
# =============================================================================

def get_personalized_timetable(admin_data, profile):
    """
    Get timetable for student's specific dept/sem/section.
    
    Args:
        admin_data (dict): Admin data
        profile (dict): Student profile with dept, semester, section
    
    Returns:
        str or None: Formatted timetable or None if not found
    """
    if not profile or not profile.get('dept'):
        return None
    
    # Build timetable key: e.g., "BCA_3_C"
    timetable_key = f"{profile['dept']}_{profile['semester']}_{profile['section']}"
    
    timetables = admin_data.get('timetables', {})
    
    if timetable_key not in timetables:
        return f"No timetable found for {profile.get('deptName', profile['dept'])} Semester {profile['semester']} Section {profile['section']}.\n\nPlease contact the admin to add your timetable."
    
    schedule = timetables[timetable_key]
    last_updated = admin_data.get('last_updated', 'N/A')
    
    response = f"**YOUR TIMETABLE**\n"
    response += f"({profile.get('deptName', profile['dept'])} | Sem {profile['semester']} | Sec {profile['section']})\n"
    response += f"Last Updated: {last_updated}\n\n"
    
    # Period timings
    period_timings = admin_data.get('period_timings', [])
    if period_timings:
        response += "**Period Timings:**\n"
        for p in period_timings:
            response += f"- Period {p['period']}: {p['start']} - {p['end']}\n"
        response += "\n"
    
    # Weekly schedule
    response += "**Weekly Schedule:**\n\n"
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for day in days:
        if day in schedule:
            classes = schedule[day]
            response += f"**{day}:**\n"
            for i, cls in enumerate(classes, 1):
                response += f"- Period {i*2-1}-{i*2}: {cls}\n"
            response += "\n"
    
    return response


def get_todays_classes(admin_data, profile):
    """Get today's classes for the student."""
    if not profile or not profile.get('dept'):
        return "Please set your profile (dept/sem/section) to see today's classes."
    
    timetable_key = f"{profile['dept']}_{profile['semester']}_{profile['section']}"
    timetables = admin_data.get('timetables', {})
    
    if timetable_key not in timetables:
        return f"No timetable found for your class."
    
    # Get today's day name
    today = datetime.now().strftime('%A')
    schedule = timetables[timetable_key]
    
    if today not in schedule:
        return f"No classes scheduled for today ({today})."
    
    classes = schedule[today]
    
    response = f"**TODAY'S CLASSES ({today})**\n"
    response += f"{profile.get('deptName', profile['dept'])} | Sem {profile['semester']} | Sec {profile['section']}\n\n"
    
    for i, cls in enumerate(classes, 1):
        response += f"- Period {i*2-1}-{i*2}: {cls}\n"
    
    return response


def get_room_location(admin_data, room_query):
    """
    Find room location details.
    
    Args:
        admin_data (dict): Admin data with room_directory
        room_query (str): User's query containing room number
    
    Returns:
        str or None: Room location details
    """
    room_directory = admin_data.get('room_directory', {})
    
    if not room_directory:
        return None
    
    # Extract room number from query
    # Match patterns like "room 808", "808", "lab 1", etc.
    room_patterns = [
        r'room\s*(?:no\.?\s*)?(\d+)',
        r'(\d{3})',
        r'(lab\s*\d+)',
    ]
    
    room_num = None
    query_lower = room_query.lower()
    
    for pattern in room_patterns:
        match = re.search(pattern, query_lower)
        if match:
            room_num = match.group(1)
            break
    
    # Also check for exact room mentions
    for room_key in room_directory.keys():
        if room_key.lower() in query_lower:
            room_num = room_key
            break
    
    if not room_num:
        # Show all rooms if asking generally about rooms
        if any(kw in query_lower for kw in ['room', 'where', 'location', 'building']):
            response = "**ROOM DIRECTORY:**\n\n"
            for room, info in list(room_directory.items())[:10]:
                response += f"- **Room {room}**: {info['floor']}, {info['wing']} ({info['type']})\n"
            response += "\n...and more. Ask about a specific room number."
            return response
        return None
    
    # Find the room (case-insensitive)
    room_info = None
    matched_key = None
    for key, info in room_directory.items():
        if key.lower() == room_num.lower() or key == room_num:
            room_info = info
            matched_key = key
            break
    
    if room_info:
        response = f"**Room {matched_key}**\n\n"
        response += f"- **Floor:** {room_info['floor']}\n"
        response += f"- **Wing:** {room_info['wing']}\n"
        response += f"- **Type:** {room_info['type']}\n"
        response += f"- **Capacity:** {room_info['capacity']} students\n"
        return response
    else:
        return f"Room {room_num} not found in directory. Please check with the admin office."


def get_student_notifications(admin_data, profile):
    """Get notifications relevant to the student."""
    if not profile or not profile.get('dept'):
        return "Please set your profile to see notifications."
    
    notifications = admin_data.get('notifications', [])
    
    if not notifications:
        return "No notifications at the moment."
    
    # Filter notifications for this student
    my_notifications = []
    for notif in notifications:
        target = notif.get('target', {})
        dept_match = target.get('dept') == 'all' or target.get('dept') == profile['dept']
        sem_match = target.get('semester') == 'all' or target.get('semester') == profile['semester']
        sec_match = target.get('section') == 'all' or target.get('section') == profile['section']
        
        if dept_match and sem_match and sec_match:
            my_notifications.append(notif)
    
    if not my_notifications:
        return "No notifications for you at the moment."
    
    response = "**YOUR NOTIFICATIONS:**\n\n"
    
    for notif in my_notifications:
        priority_tag = "[IMPORTANT] " if notif.get('priority') == 'high' else ""
        notif_type = notif.get('type', 'info').upper()
        
        response += f"**{priority_tag}{notif['title']}** ({notif_type})\n"
        response += f"{notif['message']}\n"
        response += f"Date: {notif['date']}\n\n"
    
    return response


def get_exam_schedule(admin_data, profile):
    """Get exam schedule, personalized if possible."""
    exam_schedule = admin_data.get('exam_schedule', {})
    
    if not exam_schedule:
        return None
    
    response = "**EXAMINATION SCHEDULE:**\n\n"
    
    response += f"- Internal Exams: {exam_schedule.get('internal_exams', 'N/A')}\n"
    response += f"- Odd Semester Exams: {exam_schedule.get('odd_semester_exams', 'N/A')}\n"
    response += f"- Even Semester Exams: {exam_schedule.get('even_semester_exams', 'N/A')}\n\n"
    
    upcoming = exam_schedule.get('upcoming', [])
    if upcoming:
        response += "**Upcoming Exams:**\n"
        for exam in upcoming:
            target = exam.get('target', 'all')
            # Show all or filter by profile
            if profile and profile.get('dept'):
                if target == 'all' or profile['dept'] in target:
                    response += f"- {exam['name']}: {exam['date']}\n"
            else:
                response += f"- {exam['name']}: {exam['date']}\n"
    
    return response


def get_faculty_info(admin_data, profile):
    """Get faculty information for student's department."""
    faculty_data = admin_data.get('faculty', {})
    
    if not faculty_data:
        return None
    
    dept = profile.get('dept') if profile else None
    
    if dept and dept in faculty_data:
        faculty_list = faculty_data[dept]
        response = f"**{profile.get('deptName', dept)} FACULTY:**\n\n"
        
        for f in faculty_list:
            response += f"- **{f['name']}**\n"
            response += f"  Subject: {f['subject']}\n"
            response += f"  Cabin: {f['cabin']}\n\n"
        
        return response
    else:
        # Show all departments
        response = "**FACULTY INFORMATION:**\n\n"
        for dept_name, faculty_list in faculty_data.items():
            response += f"**{dept_name} Department:**\n"
            for f in faculty_list:
                response += f"- {f['name']} ({f['subject']})\n"
            response += "\n"
        return response


def get_custom_section_response(admin_data, user_keywords):
    """Check if query matches any custom section."""
    custom_sections = admin_data.get('custom_sections', [])
    
    for section in custom_sections:
        section_keywords = set(section.get('keywords', []))
        matches = sum(1 for kw in user_keywords if kw in section_keywords)
        
        if matches >= 1:
            name = section.get('name', 'Information')
            content = section.get('content', '')
            return f"**{name.upper()}:**\n\n{content}"
    
    return None


# =============================================================================
# MAIN MATCHING FUNCTION
# =============================================================================

def find_answer(user_message, profile=None):
    """
    Find the best matching answer for a user's query.
    
    Args:
        user_message (str): The user's query
        profile (dict): Student profile with dept, semester, section
    
    Returns:
        dict: Response with found status, answer, confidence, intent
    """
    processed_query = preprocess_text(user_message)
    user_keywords = get_keywords(user_message)
    query_lower = user_message.lower()
    
    # Load admin data
    admin_data = load_admin_data()
    
    # =========================================================================
    # PRIORITY 1: Room Location Queries
    # =========================================================================
    room_keywords = {'room', 'where', 'location', 'floor', 'wing', 'lab', 'find'}
    if any(kw in user_keywords for kw in room_keywords) or re.search(r'\d{3}', query_lower):
        room_response = get_room_location(admin_data, user_message)
        if room_response:
            return {
                "found": True,
                "answer": room_response,
                "confidence": 0.95,
                "intent": "room_location"
            }
    
    # =========================================================================
    # PRIORITY 2: Today's Classes
    # =========================================================================
    if any(kw in query_lower for kw in ['today', "today's", 'now', 'current class']):
        if any(kw in user_keywords for kw in ['class', 'classes', 'timetable', 'schedule']):
            response = get_todays_classes(admin_data, profile)
            return {
                "found": True,
                "answer": response,
                "confidence": 0.95,
                "intent": "todays_classes"
            }
    
    # =========================================================================
    # PRIORITY 3: Full Timetable
    # =========================================================================
    timetable_keywords = {'timetable', 'schedule', 'classes', 'weekly'}
    if any(kw in user_keywords for kw in timetable_keywords):
        if profile and profile.get('dept'):
            response = get_personalized_timetable(admin_data, profile)
            if response:
                return {
                    "found": True,
                    "answer": response,
                    "confidence": 0.95,
                    "intent": "timetable"
                }
        else:
            return {
                "found": True,
                "answer": "Please set your profile (Department, Semester, Section) to see your personalized timetable.",
                "confidence": 0.95,
                "intent": "profile_required"
            }
    
    # =========================================================================
    # PRIORITY 4: Notifications
    # =========================================================================
    notification_keywords = {'notification', 'notifications', 'notice', 'update', 'updates', 'announcement'}
    if any(kw in user_keywords for kw in notification_keywords):
        response = get_student_notifications(admin_data, profile)
        return {
            "found": True,
            "answer": response,
            "confidence": 0.95,
            "intent": "notifications"
        }
    
    # =========================================================================
    # PRIORITY 5: Exam Schedule
    # =========================================================================
    exam_keywords = {'exam', 'exams', 'examination', 'test', 'midterm', 'final'}
    if any(kw in user_keywords for kw in exam_keywords):
        response = get_exam_schedule(admin_data, profile)
        if response:
            return {
                "found": True,
                "answer": response,
                "confidence": 0.95,
                "intent": "exam_schedule"
            }
    
    # =========================================================================
    # PRIORITY 6: Faculty Info
    # =========================================================================
    faculty_keywords = {'faculty', 'teacher', 'professor', 'prof', 'staff', 'cabin'}
    if any(kw in user_keywords for kw in faculty_keywords):
        response = get_faculty_info(admin_data, profile)
        if response:
            return {
                "found": True,
                "answer": response,
                "confidence": 0.90,
                "intent": "faculty"
            }
    
    # =========================================================================
    # PRIORITY 7: Custom Sections
    # =========================================================================
    custom_response = get_custom_section_response(admin_data, user_keywords)
    if custom_response:
        return {
            "found": True,
            "answer": custom_response,
            "confidence": 0.90,
            "intent": "custom_section"
        }
    
    # =========================================================================
    # PRIORITY 8: Knowledge Base Matching
    # =========================================================================
    knowledge_base = load_knowledge_base()
    intents = knowledge_base.get("intents", [])
    
    best_match = {
        "score": 0.0,
        "intent": None,
        "responses": []
    }
    
    for intent in intents:
        patterns = intent.get("patterns", [])
        
        for pattern in patterns:
            processed_pattern = preprocess_text(pattern)
            pattern_keywords = get_keywords(pattern)
            
            string_similarity = calculate_similarity(processed_query, processed_pattern)
            
            if pattern_keywords:
                keyword_matches = sum(1 for kw in user_keywords if kw in pattern_keywords)
                keyword_similarity = keyword_matches / len(pattern_keywords)
            else:
                keyword_similarity = 0
            
            combined_score = (string_similarity * 0.4) + (keyword_similarity * 0.6)
            
            if pattern_keywords and all(kw in user_keywords for kw in pattern_keywords):
                combined_score = max(combined_score, 0.85)
            
            if combined_score > best_match["score"]:
                best_match["score"] = combined_score
                best_match["intent"] = intent.get("tag", "unknown")
                best_match["responses"] = intent.get("responses", [])
    
    if best_match["score"] >= config.SIMILARITY_THRESHOLD and best_match["responses"]:
        selected_response = random.choice(best_match["responses"])
        
        return {
            "found": True,
            "answer": selected_response,
            "confidence": round(best_match["score"], 2),
            "intent": best_match["intent"]
        }
    
    return {
        "found": False,
        "answer": None,
        "confidence": round(best_match["score"], 2),
        "intent": None
    }
