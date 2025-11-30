"""
The North London Planning Intelligence Agent
Main FastAPI Application

Enhanced with:
- Request logging middleware with tracing
- Sentry error tracking integration
- Request timeout middleware
- Graceful shutdown handling
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.security import generate_request_id

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# ==================== Sentry Integration ====================

def init_sentry():
    """Initialize Sentry for error tracking in production."""
    if settings.sentry_dsn and settings.is_production:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration

            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.environment,
                integrations=[
                    StarletteIntegration(transaction_style="endpoint"),
                    FastApiIntegration(transaction_style="endpoint"),
                ],
                traces_sample_rate=0.1,  # 10% of requests for performance monitoring
                profiles_sample_rate=0.1,
                send_default_pii=False,  # Don't send PII
            )
            logger.info("Sentry initialized successfully")
        except ImportError:
            logger.warning("sentry-sdk not installed, error tracking disabled")
        except Exception as e:
            logger.error("Failed to initialize Sentry", error=str(e))


# ==================== Request Logging Middleware ====================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging with tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = generate_request_id()
        request.state.request_id = request_id

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request start
        start_time = time.perf_counter()
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent[:100] if user_agent else None,  # Truncate long user agents
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise


# ==================== Request Timeout Middleware ====================

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeouts."""

    def __init__(self, app, timeout_seconds: int = 30):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                "Request timeout",
                request_id=request_id,
                path=request.url.path,
                timeout_seconds=self.timeout_seconds,
            )
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "detail": f"Request exceeded {self.timeout_seconds} second timeout",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )


# ==================== Security Headers Middleware ====================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


# ==================== Application Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler with graceful shutdown."""
    # Startup
    logger.info(
        "Starting North London Planning Intelligence Agent",
        environment=settings.environment,
        debug=settings.debug,
    )

    # Initialize Sentry
    init_sentry()

    # Initialize Redis connection pool (if available)
    try:
        from app.core.security import rate_limiter
        await rate_limiter._get_redis()
        if rate_limiter._redis:
            logger.info("Redis connection established for rate limiting")
        else:
            logger.warning("Redis unavailable, using in-memory rate limiting")
    except Exception as e:
        logger.warning("Failed to initialize Redis", error=str(e))

    yield

    # Shutdown
    logger.info("Initiating graceful shutdown")

    # Close Redis connection
    try:
        from app.core.security import rate_limiter
        if rate_limiter._redis:
            await rate_limiter._redis.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.warning("Error closing Redis connection", error=str(e))

    logger.info("Shutdown complete")


# ==================== Create FastAPI Application ====================

app = FastAPI(
    title=settings.app_name,
    description="""
    ## The North London Planning Intelligence Agent

    Enterprise-grade AI consultant for UK planning permission guidance.
    Powered by RAG (Retrieval-Augmented Generation) with multi-borough document intelligence.

    ### Features
    - Multi-format document ingestion (PDF, DOCX, HTML)
    - Hybrid search (vector + keyword)
    - Conversational AI with citations
    - Analytics dashboard
    - Secure API with rate limiting

    ### Boroughs Covered
    Camden, Barnet, Westminster, Brent, Haringey
    """,
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


# ==================== Add Middleware (order matters - last added is first executed) ====================

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time", "Retry-After"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add request timeout (applied before logging so timeout is logged)
app.add_middleware(TimeoutMiddleware, timeout_seconds=settings.request_timeout_seconds)

# Add request logging (first middleware, wraps everything)
app.add_middleware(RequestLoggingMiddleware)


# ==================== Exception Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with proper logging."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "Unhandled exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )

    # Report to Sentry in production
    if settings.sentry_dsn and settings.is_production:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass

    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "error_type": type(exc).__name__,
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


# ==================== Include API Router ====================

app.include_router(api_router, prefix=settings.api_v1_prefix)


# ==================== Root Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "AI-powered planning permission guidance for North London",
        "docs": f"{settings.api_v1_prefix}/docs" if settings.debug else None,
        "health": "/health",
        "boroughs": settings.supported_boroughs,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0",
    }

    # Check Redis connectivity
    try:
        from app.core.security import rate_limiter
        if rate_limiter._redis:
            await rate_limiter._redis.ping()
            health_status["redis"] = "connected"
        else:
            health_status["redis"] = "unavailable (using in-memory fallback)"
    except Exception:
        health_status["redis"] = "error"

    return health_status


# ==================== Run with Uvicorn ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=settings.debug,
    )
