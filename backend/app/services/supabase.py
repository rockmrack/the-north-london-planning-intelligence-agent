"""Supabase database service for vector storage and retrieval."""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from supabase import create_client, Client

from app.core.config import settings
from app.models.documents import DocumentChunk, DocumentMetadata, SearchResult


class SupabaseService:
    """Service for interacting with Supabase database."""

    def __init__(self):
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key,
            )
        return self._client

    # ==================== Document Operations ====================

    async def insert_document(self, metadata: DocumentMetadata) -> str:
        """Insert a new document record."""
        data = {
            "id": metadata.document_id,
            "document_name": metadata.document_name,
            "borough": metadata.borough.value if hasattr(metadata.borough, 'value') else metadata.borough,
            "category": metadata.category.value if hasattr(metadata.category, 'value') else metadata.category,
            "source_url": metadata.source_url,
            "file_path": metadata.file_path,
            "file_type": metadata.file_type,
            "total_pages": metadata.total_pages,
            "total_chunks": metadata.total_chunks,
            "publication_date": metadata.publication_date.isoformat() if metadata.publication_date else None,
            "version": metadata.version,
            "is_active": metadata.is_active,
            "extra_metadata": metadata.extra_metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = self.client.table("documents").insert(data).execute()
        return result.data[0]["id"]

    async def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get a document by ID."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )
        if result.data:
            return DocumentMetadata(**result.data)
        return None

    async def list_documents(
        self,
        borough: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
    ) -> List[DocumentMetadata]:
        """List documents with optional filters."""
        query = self.client.table("documents").select("*")

        if borough:
            query = query.eq("borough", borough)
        if category:
            query = query.eq("category", category)
        query = query.eq("is_active", is_active)

        result = query.execute()
        return [DocumentMetadata(**doc) for doc in result.data]

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks."""
        # First delete all chunks
        self.client.table("document_chunks").delete().eq(
            "document_id", document_id
        ).execute()

        # Then delete the document
        self.client.table("documents").delete().eq("id", document_id).execute()
        return True

    # ==================== Chunk Operations ====================

    async def insert_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Insert multiple document chunks."""
        data = []
        for chunk in chunks:
            chunk_data = {
                "id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata,
                "created_at": datetime.utcnow().isoformat(),
            }
            data.append(chunk_data)

        # Insert in batches of 100
        batch_size = 100
        total_inserted = 0
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            self.client.table("document_chunks").insert(batch).execute()
            total_inserted += len(batch)

        return total_inserted

    async def vector_search(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.75,
        match_count: int = 10,
        borough: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[SearchResult]:
        """Perform vector similarity search."""
        # Build the RPC call for the match_documents function
        params = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
        }

        if borough:
            params["filter_borough"] = borough
        if category:
            params["filter_category"] = category

        result = self.client.rpc("match_documents", params).execute()

        search_results = []
        for row in result.data:
            search_results.append(
                SearchResult(
                    chunk_id=row["id"],
                    document_id=row["document_id"],
                    document_name=row["document_name"],
                    borough=row["borough"],
                    content=row["content"],
                    page_number=row.get("page_number"),
                    section_title=row.get("section_title"),
                    similarity_score=row["similarity"],
                    metadata=row.get("metadata"),
                )
            )

        return search_results

    # ==================== Lead Operations ====================

    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """Create a new lead."""
        result = self.client.table("leads").insert(lead_data).execute()
        return result.data[0]["id"]

    async def get_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a lead by email address."""
        result = (
            self.client.table("leads")
            .select("*")
            .eq("email", email)
            .single()
            .execute()
        )
        return result.data if result.data else None

    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Update a lead."""
        data["updated_at"] = datetime.utcnow().isoformat()
        self.client.table("leads").update(data).eq("id", lead_id).execute()
        return True

    # ==================== Session Operations ====================

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session."""
        result = (
            self.client.table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        )
        return result.data if result.data else None

    async def create_session(self, session_id: str, data: Dict[str, Any]) -> str:
        """Create a new chat session."""
        session_data = {
            "id": session_id,
            "messages": json.dumps([]),
            "query_count": 0,
            "lead_id": data.get("lead_id"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.client.table("chat_sessions").insert(session_data).execute()
        return session_id

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update a chat session."""
        data["updated_at"] = datetime.utcnow().isoformat()
        self.client.table("chat_sessions").update(data).eq("id", session_id).execute()
        return True

    # ==================== Analytics Operations ====================

    async def log_query(self, analytics_data: Dict[str, Any]) -> str:
        """Log a query for analytics."""
        result = self.client.table("query_analytics").insert(analytics_data).execute()
        return result.data[0]["id"]

    async def update_query_feedback(
        self, query_id: str, feedback: str, comment: Optional[str] = None
    ) -> bool:
        """Update feedback for a query."""
        data = {
            "user_feedback": feedback,
            "feedback_comment": comment,
        }
        self.client.table("query_analytics").update(data).eq("id", query_id).execute()
        return True


# Global instance
supabase_service = SupabaseService()
