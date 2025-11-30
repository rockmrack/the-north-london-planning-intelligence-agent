"""Document-related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentCategory(str, Enum):
    """Categories of planning documents."""

    LOCAL_PLAN = "local_plan"
    CONSERVATION_AREA = "conservation_area"
    DESIGN_GUIDE = "design_guide"
    SPD = "supplementary_planning_document"
    BASEMENT = "basement"
    EXTENSIONS = "extensions"
    ROOF = "roof"
    WINDOWS = "windows"
    HERITAGE = "heritage"
    SUSTAINABILITY = "sustainability"
    OTHER = "other"


class Borough(str, Enum):
    """Supported London boroughs."""

    CAMDEN = "Camden"
    BARNET = "Barnet"
    WESTMINSTER = "Westminster"
    BRENT = "Brent"
    HARINGEY = "Haringey"


class DocumentMetadata(BaseModel):
    """Metadata for a planning document."""

    document_id: str = Field(..., description="Unique document identifier")
    document_name: str = Field(..., description="Name of the document")
    borough: Borough = Field(..., description="Borough the document belongs to")
    category: DocumentCategory = Field(..., description="Document category")
    source_url: Optional[str] = Field(None, description="Original source URL")
    publication_date: Optional[datetime] = Field(
        None, description="When the document was published"
    )
    file_path: Optional[str] = Field(None, description="Path to the source file")
    file_type: Optional[str] = Field(None, description="File type (pdf, html, docx)")
    total_pages: Optional[int] = Field(None, description="Total pages in document")
    total_chunks: Optional[int] = Field(None, description="Number of chunks created")
    ingested_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the document was ingested",
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the document was last updated",
    )
    is_active: bool = Field(True, description="Whether the document is active")
    version: str = Field(default="1.0", description="Document version")
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class DocumentChunk(BaseModel):
    """A chunk of a document with its embedding."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Text content of the chunk")
    page_number: Optional[int] = Field(None, description="Page number in source")
    section_title: Optional[str] = Field(None, description="Section title if detected")
    chunk_index: int = Field(..., description="Index of chunk in document")
    token_count: int = Field(..., description="Number of tokens in chunk")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the chunk was created",
    )


class SearchResult(BaseModel):
    """A search result from the vector database."""

    chunk_id: str = Field(..., description="Chunk ID")
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document name")
    borough: str = Field(..., description="Borough")
    content: str = Field(..., description="Chunk content")
    page_number: Optional[int] = Field(None, description="Page number")
    section_title: Optional[str] = Field(None, description="Section title")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    bm25_score: Optional[float] = Field(None, description="BM25 score if hybrid search")
    combined_score: Optional[float] = Field(None, description="Combined hybrid score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class IngestRequest(BaseModel):
    """Request to ingest a document."""

    file_path: Optional[str] = Field(None, description="Path to the file")
    url: Optional[str] = Field(None, description="URL to fetch the document from")
    document_name: str = Field(..., description="Name for the document")
    borough: Borough = Field(..., description="Borough the document belongs to")
    category: DocumentCategory = Field(..., description="Document category")
    source_url: Optional[str] = Field(None, description="Original source URL")
    overwrite: bool = Field(
        False, description="Whether to overwrite existing document"
    )


class IngestResponse(BaseModel):
    """Response from document ingestion."""

    success: bool = Field(..., description="Whether ingestion succeeded")
    document_id: str = Field(..., description="ID of the ingested document")
    document_name: str = Field(..., description="Name of the document")
    chunks_created: int = Field(..., description="Number of chunks created")
    total_tokens: int = Field(..., description="Total tokens processed")
    processing_time_seconds: float = Field(..., description="Time taken to process")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(
        default_factory=list, description="Any warnings generated"
    )
