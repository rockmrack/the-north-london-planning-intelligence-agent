"""Chat-related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Citation(BaseModel):
    """A citation from a source document."""

    document_name: str = Field(..., description="Name of the source document")
    borough: str = Field(..., description="Borough the document belongs to")
    section: Optional[str] = Field(None, description="Section within the document")
    page_number: Optional[int] = Field(None, description="Page number in the document")
    paragraph: Optional[str] = Field(None, description="Relevant paragraph excerpt")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score 0-1")
    chunk_id: Optional[str] = Field(None, description="ID of the source chunk")


class ChatMessage(BaseModel):
    """A single chat message."""

    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the message was sent",
    )
    citations: Optional[List[Citation]] = Field(
        None,
        description="Citations for assistant messages",
    )


class ConversationHistory(BaseModel):
    """Conversation history for context."""

    session_id: str = Field(..., description="Unique session identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="List of messages in the conversation",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the conversation started",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the conversation was last updated",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question",
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation continuity",
    )
    borough: Optional[str] = Field(
        None,
        description="Filter to specific borough",
    )
    include_sources: bool = Field(
        True,
        description="Whether to include source citations",
    )
    stream: bool = Field(
        False,
        description="Whether to stream the response",
    )


class SuggestedQuestion(BaseModel):
    """A suggested follow-up question."""

    question: str = Field(..., description="The suggested question")
    category: Optional[str] = Field(None, description="Category of the question")


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""

    session_id: str = Field(..., description="Session ID for conversation continuity")
    message: str = Field(..., description="Assistant's response")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Source citations for the response",
    )
    suggested_questions: List[SuggestedQuestion] = Field(
        default_factory=list,
        description="Suggested follow-up questions",
    )
    detected_borough: Optional[str] = Field(
        None,
        description="Borough detected from the query",
    )
    detected_location: Optional[str] = Field(
        None,
        description="Specific location detected (conservation area, etc.)",
    )
    query_count: int = Field(
        0,
        description="Number of queries in this session",
    )
    requires_email: bool = Field(
        False,
        description="Whether email is required to continue",
    )
    processing_time_ms: float = Field(
        0,
        description="Time taken to process the query in milliseconds",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
