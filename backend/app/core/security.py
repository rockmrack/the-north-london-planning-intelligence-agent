"""
Security utilities for the Planning Intelligence Agent.
Handles authentication, rate limiting, and API key validation.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

from app.core.config import settings

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"nlpia_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_session_id() -> str:
    """Generate a unique session ID for anonymous users."""
    return f"session_{secrets.token_urlsafe(16)}"


class RateLimiter:
    """Simple in-memory rate limiter. Use Redis in production."""

    def __init__(self):
        self._requests: dict[str, list[datetime]] = {}

    def _cleanup_old_requests(self, key: str, window: int):
        """Remove requests outside the time window."""
        if key not in self._requests:
            return
        cutoff = datetime.utcnow() - timedelta(seconds=window)
        self._requests[key] = [
            req for req in self._requests[key] if req > cutoff
        ]

    def is_rate_limited(
        self,
        key: str,
        max_requests: int = None,
        window: int = None,
    ) -> bool:
        """Check if a key has exceeded the rate limit."""
        if not settings.rate_limit_enabled:
            return False

        max_requests = max_requests or settings.rate_limit_requests
        window = window or settings.rate_limit_window

        self._cleanup_old_requests(key, window)

        if key not in self._requests:
            self._requests[key] = []

        if len(self._requests[key]) >= max_requests:
            return True

        self._requests[key].append(datetime.utcnow())
        return False

    def get_remaining_requests(
        self,
        key: str,
        max_requests: int = None,
        window: int = None,
    ) -> int:
        """Get the number of remaining requests for a key."""
        max_requests = max_requests or settings.rate_limit_requests
        window = window or settings.rate_limit_window

        self._cleanup_old_requests(key, window)

        if key not in self._requests:
            return max_requests

        return max(0, max_requests - len(self._requests[key]))


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request) -> None:
    """Dependency to check rate limits."""
    # Get client identifier (IP or API key)
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")

    rate_key = api_key if api_key else f"ip:{client_ip}"

    if rate_limiter.is_rate_limited(rate_key):
        remaining = rate_limiter.get_remaining_requests(rate_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please try again later.",
                "remaining_requests": remaining,
                "retry_after": settings.rate_limit_window,
            },
        )


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    # Remove potential prompt injection patterns
    dangerous_patterns = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard previous",
        "forget previous",
        "new instructions:",
        "system:",
        "###",
    ]
    lower_text = text.lower()
    for pattern in dangerous_patterns:
        if pattern in lower_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input detected",
            )
    return text.strip()
