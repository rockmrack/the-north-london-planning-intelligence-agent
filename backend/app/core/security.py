"""
Security utilities for the Planning Intelligence Agent.
Handles authentication, rate limiting, input validation, and API key management.
"""

import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

from app.core.config import settings

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# ==================== JWT Token Management ====================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token with proper claims."""
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at
        "jti": str(uuid.uuid4()),  # Unique token ID
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require_exp": True, "require_iat": True}
        )
        return payload
    except JWTError:
        return None


# ==================== API Key Management ====================

def generate_api_key() -> Tuple[str, str]:
    """
    Generate a secure API key.
    Returns (full_key, key_hash) - store only the hash.
    """
    key_id = secrets.token_hex(8)
    key_secret = secrets.token_urlsafe(32)
    full_key = f"nlpia_{key_id}_{key_secret}"
    key_hash = hash_api_key(full_key)
    return full_key, key_hash


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key_format(api_key: str) -> bool:
    """Validate API key format."""
    pattern = r"^nlpia_[a-f0-9]{16}_[A-Za-z0-9_-]{43}$"
    return bool(re.match(pattern, api_key))


# ==================== Session Management ====================

def generate_session_id() -> str:
    """Generate a unique session ID for anonymous users."""
    return f"session_{secrets.token_urlsafe(16)}"


def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    return f"req_{uuid.uuid4().hex[:16]}"


# ==================== Redis Rate Limiter ====================

class RedisRateLimiter:
    """
    Distributed rate limiter using Redis with sliding window.
    Falls back to in-memory for development.
    """

    def __init__(self):
        self._redis = None
        self._local_cache: dict[str, list[datetime]] = {}
        self._initialized = False

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._initialized:
            return self._redis

        try:
            import redis.asyncio as redis
            self._redis = await redis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                db=settings.redis_db,
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            self._initialized = True
        except Exception:
            self._redis = None
            self._initialized = True
        return self._redis

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if a key has exceeded the rate limit.

        Returns:
            (is_limited, remaining_requests, retry_after_seconds)
        """
        if not settings.rate_limit_enabled:
            return False, max_requests, 0

        redis = await self._get_redis()

        if redis:
            return await self._check_redis_rate_limit(redis, key, max_requests, window)
        else:
            return self._check_local_rate_limit(key, max_requests, window)

    async def _check_redis_rate_limit(
        self,
        redis,
        key: str,
        max_requests: int,
        window: int,
    ) -> Tuple[bool, int, int]:
        """Redis-based sliding window rate limiting."""
        now = datetime.utcnow().timestamp()
        window_start = now - window
        redis_key = f"rate_limit:{key}"

        pipe = redis.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(redis_key, 0, window_start)
        # Count current entries
        pipe.zcard(redis_key)
        # Add current request
        pipe.zadd(redis_key, {str(now): now})
        # Set expiry
        pipe.expire(redis_key, window)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= max_requests:
            # Get oldest request in window to calculate retry_after
            oldest = await redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window - now)
            else:
                retry_after = window
            return True, 0, max(0, retry_after)

        remaining = max_requests - current_count - 1
        return False, remaining, 0

    def _check_local_rate_limit(
        self,
        key: str,
        max_requests: int,
        window: int,
    ) -> Tuple[bool, int, int]:
        """In-memory fallback rate limiting."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window)

        if key not in self._local_cache:
            self._local_cache[key] = []

        # Clean old entries
        self._local_cache[key] = [
            req for req in self._local_cache[key] if req > cutoff
        ]

        current_count = len(self._local_cache[key])

        if current_count >= max_requests:
            if self._local_cache[key]:
                oldest = min(self._local_cache[key])
                retry_after = int((oldest + timedelta(seconds=window) - now).total_seconds())
            else:
                retry_after = window
            return True, 0, max(0, retry_after)

        self._local_cache[key].append(now)
        remaining = max_requests - current_count - 1
        return False, remaining, 0


# Global rate limiter instance
rate_limiter = RedisRateLimiter()


# ==================== Rate Limit Dependencies ====================

async def check_rate_limit(request: Request) -> None:
    """General rate limit check dependency."""
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")
    rate_key = api_key if api_key else f"ip:{client_ip}"

    is_limited, remaining, retry_after = await rate_limiter.is_rate_limited(
        rate_key,
        settings.rate_limit_requests,
        settings.rate_limit_window,
    )

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "remaining_requests": remaining,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


async def check_chat_rate_limit(request: Request) -> None:
    """Chat-specific rate limit (more restrictive)."""
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")
    rate_key = f"chat:{api_key if api_key else client_ip}"

    is_limited, remaining, retry_after = await rate_limiter.is_rate_limited(
        rate_key,
        settings.rate_limit_chat,
        settings.rate_limit_window,
    )

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Chat rate limit exceeded",
                "message": "You've reached the maximum number of queries. Please try again later.",
                "remaining_requests": remaining,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


async def check_ingest_rate_limit(request: Request) -> None:
    """Document ingestion rate limit (most restrictive)."""
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")
    rate_key = f"ingest:{api_key if api_key else client_ip}"

    is_limited, remaining, retry_after = await rate_limiter.is_rate_limited(
        rate_key,
        settings.rate_limit_ingest,
        settings.rate_limit_window,
    )

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Ingestion rate limit exceeded",
                "message": "Too many document uploads. Please try again later.",
                "remaining_requests": remaining,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


# ==================== Input Validation & Sanitization ====================

# Comprehensive prompt injection patterns
INJECTION_PATTERNS = [
    # Direct instruction overrides
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"forget\s+(everything|all|previous)",
    r"new\s+instructions?:",
    r"system\s*:",
    r"assistant\s*:",
    r"human\s*:",
    r"\[system\]",
    r"\[admin\]",
    r"\[execute\]",

    # Role manipulation
    r"you\s+are\s+now",
    r"pretend\s+(to\s+be|you're)",
    r"act\s+as\s+(if|a)",
    r"roleplay\s+as",
    r"simulate\s+(being|a)",

    # Jailbreak attempts
    r"dan\s+mode",
    r"jailbreak",
    r"bypass\s+(filters?|restrictions?|rules?)",
    r"override\s+(safety|filters?)",

    # Markdown/formatting injection
    r"```system",
    r"###\s*(system|instruction|admin)",

    # Unicode tricks (common obfuscation)
    r"[\u200b-\u200f\u2028-\u202f\ufeff]",  # Zero-width and invisible chars
]

# Compiled patterns for efficiency
_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.

    Uses multiple detection strategies:
    1. Pattern matching for known injection phrases
    2. Character normalization (Unicode tricks)
    3. Length validation
    """
    if not text:
        return ""

    # Normalize unicode
    text = text.strip()

    # Remove zero-width characters and other invisible chars
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\ufeff]', '', text)

    # Check against injection patterns
    for pattern in _compiled_patterns:
        if pattern.search(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid input",
                    "message": "Your message contains disallowed content. Please rephrase your question.",
                },
            )

    # Length validation
    if len(text) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Input too long",
                "message": "Your message exceeds the maximum length of 10,000 characters.",
            },
        )

    return text


def sanitize_output(text: str) -> str:
    """
    Sanitize LLM output to prevent XSS and other injection attacks.
    """
    if not text:
        return ""

    # Remove potential script tags and event handlers
    dangerous_patterns = [
        (r'<script[^>]*>.*?</script>', '', re.IGNORECASE | re.DOTALL),
        (r'<iframe[^>]*>.*?</iframe>', '', re.IGNORECASE | re.DOTALL),
        (r'on\w+\s*=\s*["\'][^"\']*["\']', '', re.IGNORECASE),
        (r'javascript:', '', re.IGNORECASE),
        (r'data:', '', re.IGNORECASE),
    ]

    for pattern, replacement, flags in dangerous_patterns:
        text = re.sub(pattern, replacement, text, flags=flags)

    return text


# ==================== File Validation ====================

# File magic bytes for type validation
FILE_SIGNATURES = {
    "application/pdf": [b"%PDF"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
    "text/html": [b"<!DOCTYPE", b"<html", b"<HTML"],
    "text/plain": [],  # No specific signature for plain text
}


def validate_file_upload(
    content: bytes,
    filename: str,
    content_type: str,
) -> Tuple[bool, str]:
    """
    Validate uploaded file for security.

    Returns:
        (is_valid, error_message)
    """
    # Check file size
    if len(content) > settings.max_upload_size_bytes:
        return False, f"File exceeds maximum size of {settings.max_upload_size_mb}MB"

    # Check content type against allowed types
    if content_type not in settings.allowed_file_types:
        return False, f"File type '{content_type}' is not allowed"

    # Validate magic bytes (if signatures exist for this type)
    if content_type in FILE_SIGNATURES and FILE_SIGNATURES[content_type]:
        valid_signature = False
        for sig in FILE_SIGNATURES[content_type]:
            if content.startswith(sig):
                valid_signature = True
                break

        if not valid_signature:
            return False, "File content does not match declared type"

    # Check for suspicious patterns in filename
    suspicious_extensions = [".exe", ".bat", ".cmd", ".sh", ".php", ".js", ".py"]
    filename_lower = filename.lower()
    for ext in suspicious_extensions:
        if ext in filename_lower:
            return False, f"Suspicious filename detected"

    return True, ""


# ==================== Request Signing ====================

def sign_response(data: str) -> str:
    """Create HMAC signature for response data."""
    return hmac.new(
        settings.secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_signature(data: str, signature: str) -> bool:
    """Verify HMAC signature."""
    expected = sign_response(data)
    return hmac.compare_digest(expected, signature)
