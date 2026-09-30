import hashlib
import os
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

SECRET_KEY = os.environ.get("GUARDIAN_GO_SECRET") or secrets.token_urlsafe(32)

# Simple in-memory token store (Token -> User dict)
_token_sessions: Dict[str, dict] = {}

def hash_password(password: str) -> str:
    """Hash password using SHA-256 PBKDF2 with salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against stored salt:hash string."""
    if not hashed_password or ":" not in hashed_password:
        return False
    try:
        salt, stored_hash = hashed_password.split(":", 1)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(key.hex(), stored_hash)
    except Exception:
        return False

def generate_user_token(user_id: int, email: str, role: str) -> str:
    """Generate secure session token for authenticated user."""
    token = f"gg_token_{role}_{user_id}_{secrets.token_hex(16)}"
    _token_sessions[token] = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }
    return token

def get_session_by_token(token: str) -> Optional[dict]:
    """Retrieve session data by token."""
    session = _token_sessions.get(token)
    if not session:
        return None
    return session
