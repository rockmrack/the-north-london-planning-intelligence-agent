"""
API Dependencies.
Shared dependencies for route handlers.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.security import check_rate_limit, verify_token
from app.services.cache import cache_service
from app.services.rag.engine import rag_engine
from app.services.supabase import supabase_service


async def get_supabase():
    """Get Supabase service instance."""
    return supabase_service


async def get_rag_engine():
    """Get RAG engine instance."""
    return rag_engine


async def get_cache():
    """Get cache service instance."""
    return cache_service


async def rate_limit_dependency(request: Request):
    """Rate limiting dependency."""
    await check_rate_limit(request)


async def get_optional_token(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Get and verify optional bearer token."""
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    payload = verify_token(token)
    return payload


async def get_required_token(
    authorization: str = Header(...),
) -> dict:
    """Get and verify required bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization[7:]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


async def get_session_id(
    request: Request,
    x_session_id: Optional[str] = Header(None),
) -> Optional[str]:
    """Get session ID from header or generate new one."""
    return x_session_id
