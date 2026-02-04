"""
Main Flask Application for College Helpdesk Chatbot

This is the entry point of the application. It handles:
1. Setting up the web server
2. Routing requests to appropriate handlers
3. Processing chat messages
4. Returning responses to the frontend

SECURITY ARCHITECTURE:
- Student routes: Public access, read-only, NO admin links
- Admin routes: Protected with OTP-based authentication
- Strict separation between roles

Flow: User Message → Guardrails Check → Rule Engine → AI Fallback → Response
"""

# =============================================================================
# IMPORTS
# =============================================================================

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
import config

# Import our custom utility modules
from utils.guardrails import check_guardrails
from utils.rule_engine import find_answer
from utils.ai_fallback import get_ai_response

# Import admin authentication module
from utils.admin_auth import (
    authenticate_admin,
    complete_authentication,
    logout_admin,
    admin_required,
    is_admin_authenticated,
    get_current_admin
)

# =============================================================================
# FLASK APP INITIALIZATION
# =============================================================================

# Create Flask application instance
app = Flask(__name__)

# Load secret key for session management (security feature)
app.secret_key = config.SECRET_KEY

# Path to admin data file
ADMIN_DATA_FILE = os.path.join(os.path.dirname(__file__), 'admin_data.json')

# =============================================================================
# ROUTES
# =============================================================================

@app.route("/")
def home():
    """
    Home Route - Renders the main chat interface.
    
    When user visits the website, this function is called.
    It returns the HTML page with the chat interface.
    """
    return render_template("index.html", college_name=config.COLLEGE_NAME)


# =============================================================================
# PUBLIC DATA API (For Student Portal)
# =============================================================================
# This endpoint provides read-only access to dropdown data for students
# No authentication required - only exposes non-sensitive data

@app.route("/api/student-data")
def get_student_data():
    """
    Public API - Returns data needed for student profile dropdowns.
    
    Only exposes: departments, semesters, sections, notifications
    Does NOT expose: timetables, faculty details, fees, contact info
    """
    try:
        with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Return only public data needed for student dropdowns
        public_data = {
            "departments": data.get("departments", []),
            "semesters": data.get("semesters", []),
            "sections": data.get("sections", []),
            "notifications": data.get("notifications", [])
        }
        return jsonify(public_data)
    except FileNotFoundError:
        return jsonify({"departments": [], "semesters": [], "sections": [], "notifications": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ADMIN AUTHENTICATION ROUTES (Secure Access Only)
# =============================================================================
# SECURITY NOTE: All admin routes use URL prefix /secure-admin
# This URL is not linked from the student interface for security through obscurity
# Combined with OTP authentication for robust protection

@app.route("/secure-admin/login", methods=["GET", "POST"])
def admin_login():
    """
    Admin Login Route - Step 1: Username and Password verification.
    
    Security Features:
    - Rate limiting on failed attempts
    - No user enumeration (same message for invalid user/password)
    - Session-based pending authentication
    """
    # If already authenticated, redirect to dashboard
    if is_admin_authenticated():
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        success, message, otp = authenticate_admin(username, password)
        
        if success:
            # Password verified, show OTP page
            flash(message, "success")
            return render_template(
                "admin_login.html",
                college_name=config.COLLEGE_NAME,
                step="otp",
                otp=otp  # In production, OTP would be sent via SMS/Email, not displayed
            )
        else:
            flash(message, "error")
            return render_template(
                "admin_login.html",
                college_name=config.COLLEGE_NAME,
                step="login",
                username=username
            )
    
    # GET request - show login form
    return render_template(
        "admin_login.html",
        college_name=config.COLLEGE_NAME,
        step="login"
    )


@app.route("/secure-admin/verify-otp", methods=["POST"])
def admin_verify_otp():
    """
    Admin Login Route - Step 2: OTP verification.
    
    Completes the two-factor authentication process.
    """
    pending_username = session.get("pending_admin_username")
    
    if not pending_username:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for("admin_login"))
    
    otp = request.form.get("otp", "").strip()
    
    success, message = complete_authentication(pending_username, otp)
    
    if success:
        flash(message, "success")
        return redirect(url_for("admin_dashboard"))
    else:
        flash(message, "error")
        return redirect(url_for("admin_login"))


@app.route("/secure-admin/logout")
def admin_logout():
    """
    Admin Logout Route - Clears authentication session.
    """
    logout_admin()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("admin_login"))


# =============================================================================
# ADMIN DASHBOARD ROUTES (Protected)
# =============================================================================

@app.route("/secure-admin")
@admin_required
def admin_dashboard():
    """
    Admin Dashboard Route - Renders the admin panel.
    
    PROTECTED: Requires authentication via @admin_required decorator.
    
    This page allows college administrators to update:
    - Timetables and schedules
    - Room directory
    - Announcements
    - Contact information
    - Fee structure
    - Exam schedules
    """
    admin_info = get_current_admin()
    return render_template(
        "admin.html",
        college_name=config.COLLEGE_NAME,
        admin_info=admin_info
    )


@app.route("/secure-admin/data", methods=["GET"])
@admin_required
def get_admin_data():
    """
    Get Admin Data - Returns the current admin data as JSON.
    
    PROTECTED: Requires authentication.
    This is called by the admin dashboard to load existing data.
    """
    try:
        with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Admin data file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/secure-admin/data", methods=["POST"])
@admin_required
def save_admin_data():
    """
    Save Admin Data - Updates the admin data file.
    
    PROTECTED: Requires authentication.
    This is called when admin makes changes in the dashboard.
    The chatbot will use this updated data to answer questions.
    """
    try:
        data = request.get_json()
        
        with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return jsonify({"success": True, "message": "Data saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# LEGACY ADMIN ROUTE REDIRECT
# =============================================================================
# Redirect old /admin URL to secure login page
# This prevents bookmarked links from breaking

@app.route("/admin")
def admin_redirect():
    """Redirect legacy /admin URL to secure login."""
    return redirect(url_for("admin_login"))


@app.route("/chat", methods=["POST"])
def chat():
    """
    Chat Route - Processes user messages and returns bot responses.
    
    =========================================================================
    GUARDRAIL-CONTROLLED FLOW:
    =========================================================================
    
    User Message
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │ STEP 1: INPUT GUARDRAILS                                           │
    │ - Check for empty/spam messages                                    │
    │ - Filter blocked words (offensive content)                         │
    │ - Detect off-topic queries (politics, religion, etc.)              │
    │ - Block personal information sharing                               │
    │ If fails → Return warning message, NO AI called                    │
    └─────────────────────────────────────────────────────────────────────┘
         │ (passed)
         ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │ STEP 2: RULE ENGINE (Primary Response Method)                      │
    │ - Search knowledge base for matching patterns                      │
    │ - Use similarity scoring to find best match                        │
    │ If found → Return predefined answer, NO AI called                  │
    └─────────────────────────────────────────────────────────────────────┘
         │ (no match)
         ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │ STEP 3: AI FALLBACK (Used ONLY when rules fail)                    │
    │ - AI has strict system prompt limiting to college topics           │
    │ - AI response is validated for out-of-scope content                │
    │ - If AI fails, show generic fallback message                       │
    └─────────────────────────────────────────────────────────────────────┘
         │
         ▼
      Response
    
    This ensures AI is used minimally and always within guardrails.
    =========================================================================
    
    Returns:
        JSON object with 'response' key containing the bot's reply
    """
    
    # Step 1: Get user message from the POST request
    # The frontend sends data as JSON, we extract the 'message' field
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    # Extract student profile for personalized responses
    # Profile contains: dept, deptName, semester, section
    student_profile = data.get("profile", None)
    
    # Handle empty messages
    if not user_message:
        return jsonify({
            "response": "Please enter a message.",
            "source": "system"
        })
    
    # =========================================================================
    # GUARDRAIL LAYER 1: Input Validation & Content Filtering
    # This is the FIRST line of defense - blocks inappropriate content
    # before it ever reaches the rule engine or AI
    # =========================================================================
    guardrail_result = check_guardrails(user_message)
    
    if not guardrail_result["is_safe"]:
        # Message failed guardrail checks
        # AI is NEVER called for blocked messages
        return jsonify({
            "response": guardrail_result["message"],
            "source": "guardrail"
        })
    
    # =========================================================================
    # GUARDRAIL LAYER 2: Rule-Based Matching (Preferred over AI)
    # We ALWAYS try to answer from knowledge base first
    # This ensures consistent, verified answers without AI cost/risk
    # Now passes student profile for personalized responses
    # =========================================================================
    rule_result = find_answer(user_message, profile=student_profile)
    
    if rule_result["found"]:
        # Found a matching answer in the knowledge base
        # AI is NOT needed - return predefined answer
        return jsonify({
            "response": rule_result["answer"],
            "source": "knowledge_base"
        })
    
    # =========================================================================
    # GUARDRAIL LAYER 3: AI Fallback (ONLY when rules fail)
    # AI is called ONLY when:
    # 1. Message passed all guardrail checks
    # 2. No matching answer found in knowledge base
    # 
    # AI itself has additional guardrails:
    # - Strict system prompt limits topics
    # - Response is validated for off-topic content
    # - Errors result in safe fallback message
    # =========================================================================
    # Only use AI when we don't have a predefined answer
    ai_result = get_ai_response(user_message)
    
    return jsonify({
        "response": ai_result["answer"],
        "source": "ai" if ai_result["success"] else "fallback"
    })


@app.route("/health")
def health():
    """
    Health Check Route - Used to verify the server is running.
    
    Useful for:
    - Testing if the server is up
    - Monitoring in production
    - Load balancer health checks
    """
    return jsonify({"status": "healthy", "message": "Chatbot is running!"})


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors - Page not found."""
    return jsonify({"error": "Page not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors - Internal server error."""
    return jsonify({"error": "Something went wrong. Please try again."}), 500


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """
    This block runs when you execute: python app.py
    
    It starts the Flask development server.
    - host="0.0.0.0" allows access from other devices on the network
    - port=5000 is the default Flask port
    - debug=True enables auto-reload and detailed error messages
    """
    print(f"\n{'='*50}")
    print(f"  {config.COLLEGE_NAME} Helpdesk Chatbot")
    print(f"{'='*50}")
    print(f"  Server starting at: http://localhost:5000")
    print(f"  Press Ctrl+C to stop the server")
    print(f"{'='*50}\n")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=config.DEBUG_MODE
    )
