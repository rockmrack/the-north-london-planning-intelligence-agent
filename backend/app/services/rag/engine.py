"""
Main RAG Engine that orchestrates retrieval and generation.
"""

import time
import uuid
from datetime import datetime
from typing import List, Optional

import structlog

from app.core.config import settings
from app.core.security import generate_session_id
from app.models.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Citation,
    MessageRole,
    SuggestedQuestion,
)
from app.models.documents import SearchResult
from app.services.cache import cache_service
from app.services.rag.generator import response_generator
from app.services.rag.reranker import reranker
from app.services.rag.retriever import hybrid_retriever
from app.services.supabase import supabase_service

logger = structlog.get_logger()


class RAGEngine:
    """
    Main RAG (Retrieval-Augmented Generation) engine.

    Orchestrates:
    1. Query understanding and refinement
    2. Hybrid document retrieval
    3. Result reranking
    4. Response generation with citations
    5. Session management
    6. Analytics tracking
    """

    def __init__(self):
        self.retriever = hybrid_retriever
        self.reranker = reranker
        self.generator = response_generator

    async def process_query(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Process a user query through the full RAG pipeline.

        Args:
            request: ChatRequest with query and options

        Returns:
            ChatResponse with answer and citations
        """
        start_time = time.time()
        query = request.message
        session_id = request.session_id or generate_session_id()

        logger.info(
            "Processing query",
            session_id=session_id,
            query_length=len(query),
        )

        try:
            # Step 1: Check cache
            cached_response = await self._check_cache(query, request.borough)
            if cached_response:
                logger.info("Returning cached response", session_id=session_id)
                cached_response.session_id = session_id
                return cached_response

            # Step 2: Get/create session and history
            session_data, chat_history = await self._get_session(session_id)
            query_count = session_data.get("query_count", 0) + 1

            # Step 3: Extract query metadata
            query_metadata = await self.retriever.extract_query_metadata(query)
            detected_borough = request.borough or query_metadata.get("borough")

            logger.info(
                "Query metadata extracted",
                session_id=session_id,
                detected_borough=detected_borough,
                detected_topic=query_metadata.get("topic"),
            )

            # Step 4: Retrieve relevant documents
            results = await self.retriever.retrieve(
                query=query,
                top_k=settings.max_chunks_per_query * 2,  # Get more for reranking
                borough=detected_borough,
            )

            logger.info(
                "Documents retrieved",
                session_id=session_id,
                result_count=len(results),
            )

            # Step 5: Rerank results
            reranked_results = await self.reranker.rerank(
                query=query,
                results=results,
                top_k=settings.max_chunks_per_query,
            )

            logger.info(
                "Results reranked",
                session_id=session_id,
                final_count=len(reranked_results),
            )

            # Step 6: Generate response
            response_text, citations = await self.generator.generate(
                query=query,
                context_results=reranked_results,
                chat_history=chat_history,
            )

            # Step 7: Generate follow-up suggestions
            suggested_questions = await self._generate_suggestions(
                chat_history, response_text
            )

            # Step 8: Update session
            await self._update_session(
                session_id=session_id,
                query=query,
                response=response_text,
                query_count=query_count,
            )

            # Step 9: Check if email required
            requires_email = (
                settings.lead_capture_enabled
                and query_count >= settings.require_email_after
                and not session_data.get("lead_id")
            )

            processing_time = (time.time() - start_time) * 1000

            # Step 10: Log analytics
            await self._log_analytics(
                session_id=session_id,
                query=query,
                response_text=response_text,
                citations=citations,
                reranked_results=reranked_results,
                query_metadata=query_metadata,
                processing_time=processing_time,
                is_follow_up=len(chat_history) > 0,
            )

            # Build response
            response = ChatResponse(
                session_id=session_id,
                message=response_text,
                citations=citations,
                suggested_questions=suggested_questions,
                detected_borough=detected_borough,
                detected_location=query_metadata.get("conservation_area"),
                query_count=query_count,
                requires_email=requires_email,
                processing_time_ms=processing_time,
            )

            # Cache the response
            await self._cache_response(query, request.borough, response)

            logger.info(
                "Query processed successfully",
                session_id=session_id,
                processing_time_ms=processing_time,
            )

            return response

        except Exception as e:
            logger.error(
                "Query processing failed",
                session_id=session_id,
                error=str(e),
            )
            raise

    async def process_streaming_query(
        self,
        request: ChatRequest,
    ):
        """
        Process a query with streaming response.

        Yields response chunks as they're generated.
        """
        session_id = request.session_id or generate_session_id()
        query = request.message

        # Get session and history
        session_data, chat_history = await self._get_session(session_id)

        # Extract metadata and retrieve
        query_metadata = await self.retriever.extract_query_metadata(query)
        detected_borough = request.borough or query_metadata.get("borough")

        results = await self.retriever.retrieve(
            query=query,
            top_k=settings.max_chunks_per_query * 2,
            borough=detected_borough,
        )

        reranked_results = await self.reranker.rerank(
            query=query,
            results=results,
            top_k=settings.max_chunks_per_query,
        )

        # Stream the response
        full_response = ""
        async for chunk in self.generator.generate_streaming(
            query=query,
            context_results=reranked_results,
            chat_history=chat_history,
        ):
            full_response += chunk
            yield chunk

        # Update session after streaming completes
        query_count = session_data.get("query_count", 0) + 1
        await self._update_session(
            session_id=session_id,
            query=query,
            response=full_response,
            query_count=query_count,
        )

    async def _check_cache(
        self,
        query: str,
        borough: Optional[str],
    ) -> Optional[ChatResponse]:
        """Check if we have a cached response."""
        cached = await cache_service.get_query_result(query, borough)
        if cached:
            return ChatResponse(**cached)
        return None

    async def _cache_response(
        self,
        query: str,
        borough: Optional[str],
        response: ChatResponse,
    ) -> None:
        """Cache the response for future queries."""
        # Don't cache personalized responses
        if response.requires_email:
            return

        await cache_service.set_query_result(
            query=query,
            result=response.model_dump(),
            borough=borough,
            ttl=3600,  # 1 hour
        )

    async def _get_session(
        self,
        session_id: str,
    ) -> tuple[dict, List[ChatMessage]]:
        """Get or create a session."""
        # Try cache first
        cached_session = await cache_service.get_session(session_id)
        if cached_session:
            messages = [
                ChatMessage(**msg) for msg in cached_session.get("messages", [])
            ]
            return cached_session, messages

        # Try database
        db_session = await supabase_service.get_session(session_id)
        if db_session:
            messages = [
                ChatMessage(**msg)
                for msg in (db_session.get("messages") or [])
            ]
            await cache_service.set_session(session_id, db_session)
            return db_session, messages

        # Create new session
        new_session = {
            "id": session_id,
            "messages": [],
            "query_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        await supabase_service.create_session(session_id, new_session)
        await cache_service.set_session(session_id, new_session)

        return new_session, []

    async def _update_session(
        self,
        session_id: str,
        query: str,
        response: str,
        query_count: int,
    ) -> None:
        """Update session with new messages."""
        session_data, messages = await self._get_session(session_id)

        # Add new messages
        messages.append(
            ChatMessage(
                role=MessageRole.USER,
                content=query,
                timestamp=datetime.utcnow(),
            )
        )
        messages.append(
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response,
                timestamp=datetime.utcnow(),
            )
        )

        # Keep only last 20 messages
        messages = messages[-20:]

        # Update session
        updated_data = {
            "messages": [msg.model_dump() for msg in messages],
            "query_count": query_count,
            "updated_at": datetime.utcnow().isoformat(),
        }

        await supabase_service.update_session(session_id, updated_data)
        session_data.update(updated_data)
        await cache_service.set_session(session_id, session_data)

    async def _generate_suggestions(
        self,
        chat_history: List[ChatMessage],
        response: str,
    ) -> List[SuggestedQuestion]:
        """Generate follow-up question suggestions."""
        if not chat_history:
            # Default suggestions for first query
            return [
                SuggestedQuestion(question="What are the permitted development rights for rear extensions?"),
                SuggestedQuestion(question="Do I need planning permission for a loft conversion?"),
                SuggestedQuestion(question="What are the rules for basement developments?"),
            ]

        # Generate contextual suggestions
        conversation_summary = "\n".join(
            f"{msg.role.value}: {msg.content[:200]}"
            for msg in chat_history[-4:]
        )

        return await self.generator.generate_follow_ups(
            conversation_summary, response
        )

    async def _log_analytics(
        self,
        session_id: str,
        query: str,
        response_text: str,
        citations: List[Citation],
        reranked_results: List[SearchResult],
        query_metadata: dict,
        processing_time: float,
        is_follow_up: bool,
    ) -> None:
        """Log query analytics."""
        if not settings.analytics_enabled:
            return

        analytics_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "query_text": query,
            "detected_borough": query_metadata.get("borough"),
            "detected_location": query_metadata.get("conservation_area"),
            "detected_topic": query_metadata.get("topic"),
            "response_length": len(response_text),
            "citations_count": len(citations),
            "documents_retrieved": len(reranked_results),
            "processing_time_ms": processing_time,
            "is_follow_up": is_follow_up,
            "created_at": datetime.utcnow().isoformat(),
        }

        try:
            await supabase_service.log_query(analytics_data)
        except Exception as e:
            logger.warning("Failed to log analytics", error=str(e))


# Global instance
rag_engine = RAGEngine()
