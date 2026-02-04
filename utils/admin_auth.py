"""
============================================================================
Admin Authentication Module
============================================================================
Title: Secure Admin Authentication with OTP Verification
Purpose: Enforce strict role separation between Student and Admin panels

SECURITY ARCHITECTURE:
- Pre-created admin accounts only (no self-registration)
- Password hashing using werkzeug.security (bcrypt-style)
- Simulated OTP system for academic demonstration
- Session-based authentication with Flask's session
- All admin routes protected by decorator

IMPORTANT FOR PRODUCTION:
- Replace simulated OTP with real SMS/Email service (Twilio, SendGrid)
- Use environment variables for all secrets
- Implement rate limiting on login attempts
- Add HTTPS enforcement
- Consider using Flask-Login for more robust session management

============================================================================
"""

import random
import string
import time
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================================
# CONFIGURATION
# ============================================================================

# OTP validity duration in seconds (5 minutes)
OTP_VALIDITY_SECONDS = 300

# Maximum login attempts before lockout
MAX_LOGIN_ATTEMPTS = 5

# Lockout duration in seconds (15 minutes)
LOCKOUT_DURATION = 900

# ============================================================================
# PRE-CREATED ADMIN ACCOUNTS
# ============================================================================
# NOTE: In production, store these in a database with proper encryption
# Passwords are hashed using werkzeug's generate_password_hash

ADMIN_ACCOUNTS = {
    "admin": {
        "password_hash": generate_password_hash("admin123"),
        "full_name": "System Administrator",
        "email": "admin@college.edu",
        "role": "super_admin"
    },
    "hod_cse": {
        "password_hash": generate_password_hash("hodcse@2024"),
        "full_name": "HOD - Computer Science",
        "email": "hod.cse@college.edu",
        "role": "department_admin"
    },
    "staff": {
        "password_hash": generate_password_hash("staff@2024"),
        "full_name": "Staff User",
        "email": "staff@college.edu",
        "role": "editor"
    }
}

# ============================================================================
# OTP STORAGE (In-memory for demonstration)
# ============================================================================
# NOTE: In production, use Redis or database with expiration

_otp_storage = {}  # Format: {username: {"otp": "123456", "timestamp": time.time(), "verified": False}}
_login_attempts = {}  # Format: {username: {"attempts": 0, "lockout_until": timestamp}}


# ============================================================================
# PASSWORD FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using werkzeug's secure hashing.
    Uses PBKDF2 with SHA-256 by default.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return generate_password_hash(password)


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        stored_hash: The stored password hash
        provided_password: The password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    return check_password_hash(stored_hash, provided_password)


# ============================================================================
# OTP FUNCTIONS
# ============================================================================

def generate_otp(length: int = 6) -> str:
    """
    Generate a random numeric OTP.
    
    Args:
        length: Number of digits (default 6)
        
    Returns:
        OTP string (e.g., "123456")
    """
    return ''.join(random.choices(string.digits, k=length))


def create_otp_for_user(username: str) -> str:
    """
    Generate and store an OTP for the specified user.
    
    Args:
        username: The admin username
        
    Returns:
        The generated OTP (for display in demo mode)
        
    NOTE: In production, this would send OTP via SMS/Email
    and return only a success message.
    """
    otp = generate_otp()
    _otp_storage[username] = {
        "otp": otp,
        "timestamp": time.time(),
        "verified": False
    }
    
    # In production, send OTP via SMS/Email here:
    # send_sms(ADMIN_ACCOUNTS[username]["phone"], f"Your OTP is: {otp}")
    # send_email(ADMIN_ACCOUNTS[username]["email"], f"Your OTP is: {otp}")
    
    return otp


def verify_otp(username: str, provided_otp: str) -> tuple[bool, str]:
    """
    Verify the OTP provided by the user.
    
    Args:
        username: The admin username
        provided_otp: The OTP entered by user
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if username not in _otp_storage:
        return False, "No OTP generated for this user. Please login again."
    
    stored_data = _otp_storage[username]
    
    # Check if OTP has expired
    if time.time() - stored_data["timestamp"] > OTP_VALIDITY_SECONDS:
        del _otp_storage[username]
        return False, "OTP has expired. Please login again."
    
    # Check if OTP matches
    if stored_data["otp"] != provided_otp:
        return False, "Invalid OTP. Please try again."
    
    # Mark as verified and remove from storage
    del _otp_storage[username]
    return True, "OTP verified successfully."


def clear_otp(username: str) -> None:
    """
    Clear any stored OTP for the user.
    
    Args:
        username: The admin username
    """
    if username in _otp_storage:
        del _otp_storage[username]


# ============================================================================
# LOGIN ATTEMPT TRACKING (Rate Limiting)
# ============================================================================

def check_lockout(username: str) -> tuple[bool, int]:
    """
    Check if user is locked out due to too many failed attempts.
    
    Args:
        username: The admin username
        
    Returns:
        Tuple of (is_locked: bool, remaining_seconds: int)
    """
    if username not in _login_attempts:
        return False, 0
    
    attempt_data = _login_attempts[username]
    
    if "lockout_until" in attempt_data:
        remaining = attempt_data["lockout_until"] - time.time()
        if remaining > 0:
            return True, int(remaining)
        else:
            # Lockout expired, reset
            _login_attempts[username] = {"attempts": 0}
            return False, 0
    
    return False, 0


def record_failed_attempt(username: str) -> tuple[int, bool]:
    """
    Record a failed login attempt.
    
    Args:
        username: The admin username
        
    Returns:
        Tuple of (attempts_remaining: int, is_now_locked: bool)
    """
    if username not in _login_attempts:
        _login_attempts[username] = {"attempts": 0}
    
    _login_attempts[username]["attempts"] += 1
    attempts = _login_attempts[username]["attempts"]
    
    if attempts >= MAX_LOGIN_ATTEMPTS:
        _login_attempts[username]["lockout_until"] = time.time() + LOCKOUT_DURATION
        return 0, True
    
    return MAX_LOGIN_ATTEMPTS - attempts, False


def reset_login_attempts(username: str) -> None:
    """
    Reset login attempts after successful login.
    
    Args:
        username: The admin username
    """
    if username in _login_attempts:
        del _login_attempts[username]


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def authenticate_admin(username: str, password: str) -> tuple[bool, str, str | None]:
    """
    Authenticate admin with username and password.
    
    Args:
        username: The admin username
        password: The plain text password
        
    Returns:
        Tuple of (success: bool, message: str, otp: str | None)
        OTP is returned only for display in demo mode.
    """
    # Check lockout
    is_locked, remaining = check_lockout(username)
    if is_locked:
        minutes = remaining // 60
        seconds = remaining % 60
        return False, f"Account locked. Try again in {minutes}m {seconds}s.", None
    
    # Check if username exists
    if username not in ADMIN_ACCOUNTS:
        record_failed_attempt(username)
        return False, "Invalid username or password.", None
    
    # Verify password
    account = ADMIN_ACCOUNTS[username]
    if not verify_password(account["password_hash"], password):
        attempts_left, is_locked = record_failed_attempt(username)
        if is_locked:
            return False, f"Too many failed attempts. Account locked for {LOCKOUT_DURATION // 60} minutes.", None
        return False, f"Invalid username or password. {attempts_left} attempts remaining.", None
    
    # Password correct - generate OTP
    reset_login_attempts(username)
    otp = create_otp_for_user(username)
    
    # Store pending authentication in session
    session["pending_admin_username"] = username
    
    return True, "Password verified. Please enter OTP.", otp


def complete_authentication(username: str, otp: str) -> tuple[bool, str]:
    """
    Complete authentication by verifying OTP.
    
    Args:
        username: The admin username
        otp: The OTP entered by user
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    success, message = verify_otp(username, otp)
    
    if success:
        # Set authenticated session
        session["admin_authenticated"] = True
        session["admin_username"] = username
        session["admin_role"] = ADMIN_ACCOUNTS[username]["role"]
        session["admin_name"] = ADMIN_ACCOUNTS[username]["full_name"]
        session.pop("pending_admin_username", None)
        return True, f"Welcome, {ADMIN_ACCOUNTS[username]['full_name']}!"
    
    return False, message


def logout_admin() -> None:
    """
    Clear admin session data.
    """
    session.pop("admin_authenticated", None)
    session.pop("admin_username", None)
    session.pop("admin_role", None)
    session.pop("admin_name", None)
    session.pop("pending_admin_username", None)


def is_admin_authenticated() -> bool:
    """
    Check if current session has authenticated admin.
    
    Returns:
        True if admin is authenticated, False otherwise
    """
    return session.get("admin_authenticated", False)


def get_current_admin() -> dict | None:
    """
    Get current authenticated admin info.
    
    Returns:
        Dict with admin info or None if not authenticated
    """
    if not is_admin_authenticated():
        return None
    
    username = session.get("admin_username")
    if username and username in ADMIN_ACCOUNTS:
        return {
            "username": username,
            "full_name": ADMIN_ACCOUNTS[username]["full_name"],
            "email": ADMIN_ACCOUNTS[username]["email"],
            "role": ADMIN_ACCOUNTS[username]["role"]
        }
    return None


# ============================================================================
# ROUTE PROTECTION DECORATOR
# ============================================================================

def admin_required(f):
    """
    Decorator to protect routes that require admin authentication.
    
    Usage:
        @app.route('/secure-admin/dashboard')
        @admin_required
        def admin_dashboard():
            return render_template('admin.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_authenticated():
            flash("Please login to access the admin panel.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_admin_accounts_list() -> list[dict]:
    """
    Get list of admin accounts (without sensitive data).
    For display purposes only.
    
    Returns:
        List of admin account info (username, name, role)
    """
    return [
        {
            "username": username,
            "full_name": data["full_name"],
            "email": data["email"],
            "role": data["role"]
        }
        for username, data in ADMIN_ACCOUNTS.items()
    ]
