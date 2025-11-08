# security.py
import bcrypt
import re
from typing import Optional
import secrets  # --- NEW IMPORT ---
from datetime import datetime, timedelta  # --- NEW IMPORT ---

# --- Password Hashing ---
def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- NEW: Password Reset Token ---
def create_reset_token() -> (str, datetime):
    """Generates a secure reset token and its expiry time."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1) # Token is valid for 1 hour
    return token, expires_at

# --- Input Validation (Sanitization) ---
def sanitize_input(input_string: str) -> str:
    """
    Sanitizes user input to prevent XSS and SQL injection.
    This is a basic example; more robust solutions might use libraries
    or specific encoding based on context (e.g., HTML escaping).
    """
    if not isinstance(input_string, str):
        return ""
    # Basic HTML escaping for XSS prevention
    sanitized = input_string.replace("&", "&amp;")
    sanitized = sanitized.replace("<", "&lt;")
    sanitized = sanitized.replace(">", "&gt;")
    sanitized = sanitized.replace("'", "&#x27;")
    sanitized = sanitized.replace('"', "&quot;")
    # Note: For SQL Injection, parameterized queries are the primary defense.
    # This function helps for general display, but not a replacement for parameterized queries.
    return sanitized

# --- Password Strength Meter (Basic Example) ---
def get_password_strength(password: str) -> dict:
    """
    Evaluates password strength. Returns a dictionary with score and messages.
    Score: 0-100 (higher is stronger)
    """
    strength = {
        "score": 0,
        "feedback": []
    }

    if len(password) < 8:
        strength["feedback"].append("Password should be at least 8 characters long.")
        strength["score"] += 10
    else:
        strength["score"] += 20

    if re.search(r"[a-z]", password):
        strength["score"] += 15
    else:
        strength["feedback"].append("Password should contain lowercase letters.")

    if re.search(r"[A-Z]", password):
        strength["score"] += 15
    else:
        strength["feedback"].append("Password should contain uppercase letters.")

    if re.search(r"\d", password):
        strength["score"] += 15
    else:
        strength["feedback"].append("Password should contain numbers.")

    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        strength["score"] += 20
    else:
        strength["feedback"].append("Password should contain special characters.")

    if len(password) >= 12:
        strength["score"] += 15 # Bonus for extra length

    # Cap score at 100
    strength["score"] = min(strength["score"], 100)

    if not strength["feedback"]:
        strength["feedback"].append("Excellent password!")

    return strength

# --- CSRF/XSS/XSRF Prevention Strategies ---
# (These are strategies, not functions to be called directly in every input)

# 1. CSRF (Cross-Site Request Forgery):
#    - Use CSRF tokens: Generate a unique, unpredictable token on the server for each form
#      submission or state-changing request. Embed it in the form/request.
#      Verify the token on the server side. FastAPI has middleware or dependencies
#      to help with this (e.g., `fastapi-csrf-protect`).
#    - SameSite cookies: Set `SameSite=Lax` or `Strict` on session cookies.

# 2. XSS (Cross-Site Scripting):
#    - Input Validation/Sanitization: Sanitize all user-generated content before storing it
#      and especially before rendering it back to the browser.
#      (The `sanitize_input` function above is a basic start for display).
#    - Content Security Policy (CSP): Implement a strong CSP header to restrict
#      which scripts, styles, and other resources the browser is allowed to load.
#      This is configured in FastAPI responses or middleware.

# 3. XSRF (Cross-Site Request Forgery):
#    - This is often used interchangeably with CSRF. The same measures apply:
#      CSRF tokens and SameSite cookies.

# 4. Prompt Injection:
#    - This is more relevant for AI/LLM applications. For a traditional web app,
#      it's about validating and sanitizing any input that might be fed into
#      a system that interprets it (e.g., a search query that goes to an LLM).
#      For this project, it's primarily covered by general input validation.

# 5. SQL Injection:
#    - **Crucial**: Always use parameterized queries (prepared statements) for all
#      database interactions where user input is involved. The `sqlite3` module
#      in Python supports this by using `?` placeholders.
#      Example: `cursor.execute("SELECT * FROM users WHERE username = ?", (username,))`
#      NEVER do `cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")`

# 6. Session Management:
#    - Use secure, short-lived session tokens.
#    - Store session data server-side, not in client-side cookies.
#    - Invalidate sessions on logout.
#    - FastAPI will use `starlette.middleware.sessions` for session management.

# 7. HTTPS:
#    - Ensure your website is served over HTTPS in production to protect data in transit.
#      This is usually handled by your deployment environment (e.g., Nginx, Caddy).