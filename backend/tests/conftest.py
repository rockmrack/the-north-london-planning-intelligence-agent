"""
Pytest configuration and fixtures for the Planning Intelligence Agent tests.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import Settings, get_settings
from app.main import app


# ==================== Settings Override ====================

def get_test_settings() -> Settings:
    """Get test settings with mock values."""
    return Settings(
        environment="test",
        debug=True,
        secret_key="test-secret-key-for-testing-purposes-32chars",
        openai_api_key="sk-test-key",
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_key="test-service-key",
        redis_url="redis://localhost:6379",
        rate_limit_enabled=False,  # Disable rate limiting in tests
    )


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test settings."""
    return get_test_settings()


# ==================== Event Loop ====================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== FastAPI Client ====================

@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Provide a synchronous test client."""
    app.dependency_overrides[get_settings] = get_test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client."""
    app.dependency_overrides[get_settings] = get_test_settings
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ==================== Mock Services ====================

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("openai.AsyncOpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client

        # Mock chat completions
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="This is a test response about planning permissions."
                )
            )
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock embeddings
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [
            MagicMock(embedding=[0.1] * 3072)  # text-embedding-3-large dimension
        ]
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

        yield mock_client


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("supabase.create_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client

        # Mock table operations
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])

        mock_client.table.return_value = mock_table

        # Mock RPC calls
        mock_client.rpc.return_value = MagicMock(
            execute=MagicMock(return_value=MagicMock(data=[]))
        )

        yield mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.asyncio.from_url") as mock:
        mock_redis = AsyncMock()
        mock.return_value = mock_redis

        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.zremrangebyscore.return_value = 0
        mock_redis.zcard.return_value = 0
        mock_redis.zadd.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.execute.return_value = [0, 0, 1, True]

        yield mock_redis


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "title": "Camden Planning Guidelines 2024",
        "content": "This document outlines the planning permission requirements for Camden borough.",
        "source": "camden_guidelines_2024.pdf",
        "borough": "Camden",
        "document_type": "policy",
        "metadata": {
            "page_count": 50,
            "created_at": "2024-01-15",
        },
    }


@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing."""
    return [
        {
            "content": "Planning permission is required for most building work in Camden.",
            "metadata": {
                "source": "camden_guidelines_2024.pdf",
                "page": 1,
                "chunk_index": 0,
            },
            "embedding": [0.1] * 3072,
        },
        {
            "content": "Extensions over 4 metres require full planning permission.",
            "metadata": {
                "source": "camden_guidelines_2024.pdf",
                "page": 2,
                "chunk_index": 1,
            },
            "embedding": [0.2] * 3072,
        },
    ]


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return {
        "message": "Do I need planning permission for a loft conversion in Camden?",
        "session_id": "test-session-123",
        "borough": "Camden",
    }


@pytest.fixture
def sample_lead():
    """Sample lead data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "company": "Test Company",
        "phone": "+44 20 1234 5678",
        "project_type": "loft_conversion",
        "borough": "Camden",
        "message": "I'm interested in learning more about planning permissions.",
    }
