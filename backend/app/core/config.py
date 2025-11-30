"""
Configuration settings for the Planning Intelligence Agent.
Uses Pydantic Settings for type-safe environment variable handling.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "North London Planning Intelligence Agent"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    secret_key: str = Field(default="change-me-in-production")

    # API
    api_v1_prefix: str = Field(default="/api/v1")
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-large")
    openai_max_tokens: int = Field(default=4096)
    openai_temperature: float = Field(default=0.1)

    # Supabase
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_key: str = Field(default="")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_password: Optional[str] = Field(default=None)
    redis_db: int = Field(default=0)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=3600)

    # Document Processing
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)
    max_chunks_per_query: int = Field(default=10)
    similarity_threshold: float = Field(default=0.75)

    # Hybrid Search
    hybrid_search_enabled: bool = Field(default=True)
    vector_weight: float = Field(default=0.7)
    bm25_weight: float = Field(default=0.3)
    rerank_enabled: bool = Field(default=True)
    rerank_top_k: int = Field(default=20)

    # Lead Capture
    lead_capture_enabled: bool = Field(default=True)
    free_queries_limit: int = Field(default=3)
    require_email_after: int = Field(default=3)

    # Analytics
    analytics_enabled: bool = Field(default=True)

    # External Integrations
    sendgrid_api_key: Optional[str] = Field(default=None)
    hubspot_api_key: Optional[str] = Field(default=None)
    slack_webhook_url: Optional[str] = Field(default=None)

    # Borough Configuration
    supported_boroughs: List[str] = Field(
        default=[
            "Camden",
            "Barnet",
            "Westminster",
            "Brent",
            "Haringey",
        ]
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
