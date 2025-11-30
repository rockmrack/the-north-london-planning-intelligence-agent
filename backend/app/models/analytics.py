"""Analytics related Pydantic models."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QueryAnalytics(BaseModel):
    """Analytics for a single query."""

    query_id: str = Field(..., description="Unique query ID")
    session_id: str = Field(..., description="Session ID")
    query_text: str = Field(..., description="The user's query")
    detected_borough: Optional[str] = Field(None, description="Detected borough")
    detected_location: Optional[str] = Field(None, description="Detected location")
    detected_topic: Optional[str] = Field(None, description="Detected topic/category")
    response_length: int = Field(..., description="Length of the response")
    citations_count: int = Field(..., description="Number of citations")
    documents_retrieved: int = Field(..., description="Documents retrieved")
    processing_time_ms: float = Field(..., description="Processing time in ms")
    user_feedback: Optional[str] = Field(None, description="User feedback (thumbs up/down)")
    feedback_comment: Optional[str] = Field(None, description="Additional feedback")
    is_follow_up: bool = Field(False, description="Whether this is a follow-up query")
    lead_captured: bool = Field(False, description="Whether a lead was captured")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the query was made",
    )


class TopicCount(BaseModel):
    """Count of queries per topic."""

    topic: str = Field(..., description="Topic name")
    count: int = Field(..., description="Number of queries")
    percentage: float = Field(..., description="Percentage of total")


class BoroughCount(BaseModel):
    """Count of queries per borough."""

    borough: str = Field(..., description="Borough name")
    count: int = Field(..., description="Number of queries")
    percentage: float = Field(..., description="Percentage of total")


class TimeSeriesPoint(BaseModel):
    """A point in a time series."""

    timestamp: datetime = Field(..., description="Timestamp")
    value: int = Field(..., description="Value at this point")


class AnalyticsSummary(BaseModel):
    """Summary of analytics data."""

    period_start: datetime = Field(..., description="Start of the period")
    period_end: datetime = Field(..., description="End of the period")

    # Query metrics
    total_queries: int = Field(..., description="Total queries in period")
    unique_sessions: int = Field(..., description="Unique sessions")
    avg_queries_per_session: float = Field(..., description="Avg queries per session")
    avg_processing_time_ms: float = Field(..., description="Avg processing time")

    # Engagement metrics
    positive_feedback_rate: float = Field(..., description="Rate of positive feedback")
    negative_feedback_rate: float = Field(..., description="Rate of negative feedback")
    no_feedback_rate: float = Field(..., description="Rate of no feedback")

    # Conversion metrics
    leads_captured: int = Field(..., description="Number of leads captured")
    lead_conversion_rate: float = Field(..., description="Session to lead rate")

    # Breakdowns
    queries_by_borough: List[BoroughCount] = Field(
        default_factory=list, description="Queries by borough"
    )
    queries_by_topic: List[TopicCount] = Field(
        default_factory=list, description="Queries by topic"
    )

    # Time series
    queries_over_time: List[TimeSeriesPoint] = Field(
        default_factory=list, description="Queries over time"
    )

    # Top queries
    top_queries: List[str] = Field(
        default_factory=list, description="Most common query patterns"
    )

    # Documents
    most_cited_documents: List[Dict[str, int]] = Field(
        default_factory=list, description="Most cited documents"
    )


class FeedbackRequest(BaseModel):
    """Request to submit feedback."""

    query_id: str = Field(..., description="Query ID to provide feedback for")
    feedback: str = Field(..., description="Feedback type: positive, negative")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""

    success: bool = Field(..., description="Whether feedback was recorded")
    message: str = Field(..., description="Response message")
