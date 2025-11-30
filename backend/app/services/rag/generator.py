"""
Response generator using GPT-4o.
Generates cited, accurate responses from retrieved context.
"""

import json
from typing import List, Optional, Tuple

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.prompts import (
    SYSTEM_PROMPT,
    QUERY_REFINEMENT_PROMPT,
    FOLLOW_UP_SUGGESTIONS_PROMPT,
)
from app.models.chat import ChatMessage, Citation, SuggestedQuestion
from app.models.documents import SearchResult


class ResponseGenerator:
    """
    Generates responses using GPT-4o with retrieved context.

    Features:
    1. Context-aware response generation
    2. Automatic citation extraction
    3. Follow-up question suggestions
    4. Conversation memory
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    async def generate(
        self,
        query: str,
        context_results: List[SearchResult],
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> Tuple[str, List[Citation]]:
        """
        Generate a response with citations.

        Args:
            query: User's question
            context_results: Retrieved document chunks
            chat_history: Previous conversation messages

        Returns:
            Tuple of (response text, list of citations)
        """
        # Format context
        context = self._format_context(context_results)

        # Format chat history
        history = self._format_history(chat_history) if chat_history else ""

        # Build the prompt
        prompt = SYSTEM_PROMPT.format(
            context=context,
            chat_history=history,
            question=query,
        )

        # Generate response
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        response_text = response.choices[0].message.content

        # Extract citations from context results
        citations = self._extract_citations(context_results, response_text)

        return response_text, citations

    async def generate_streaming(
        self,
        query: str,
        context_results: List[SearchResult],
        chat_history: Optional[List[ChatMessage]] = None,
    ):
        """
        Generate a streaming response.

        Yields chunks of the response as they're generated.
        """
        context = self._format_context(context_results)
        history = self._format_history(chat_history) if chat_history else ""

        prompt = SYSTEM_PROMPT.format(
            context=context,
            chat_history=history,
            question=query,
        )

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def refine_query(self, query: str) -> dict:
        """
        Refine a query for better search results.

        Returns dict with refined query and extracted metadata.
        """
        prompt = QUERY_REFINEMENT_PROMPT.format(question=query)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0,
        )

        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            return {
                "refined_query": query,
                "borough": None,
                "development_type": None,
                "keywords": query.split(),
                "filters": {},
            }

    async def generate_follow_ups(
        self,
        conversation_summary: str,
        last_response: str,
    ) -> List[SuggestedQuestion]:
        """
        Generate follow-up question suggestions.
        """
        prompt = FOLLOW_UP_SUGGESTIONS_PROMPT.format(
            conversation=conversation_summary,
            last_response=last_response[:1000],
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )

        try:
            questions = json.loads(response.choices[0].message.content)
            return [
                SuggestedQuestion(question=q)
                for q in questions
                if isinstance(q, str)
            ][:3]
        except (json.JSONDecodeError, TypeError):
            return []

    def _format_context(self, results: List[SearchResult]) -> str:
        """Format search results as context for the prompt."""
        if not results:
            return "No relevant documents found."

        formatted = []
        for i, result in enumerate(results, 1):
            chunk = f"""
--- Document {i} ---
Source: {result.document_name}
Borough: {result.borough}
Page: {result.page_number or 'N/A'}
Section: {result.section_title or 'N/A'}
Relevance Score: {result.similarity_score:.2f}

Content:
{result.content}
"""
            formatted.append(chunk)

        return "\n".join(formatted)

    def _format_history(self, messages: List[ChatMessage]) -> str:
        """Format chat history for the prompt."""
        if not messages:
            return ""

        # Only include last 5 exchanges to manage context length
        recent_messages = messages[-10:]

        formatted = []
        for msg in recent_messages:
            role = "User" if msg.role.value == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content}")

        return "\n".join(formatted)

    def _extract_citations(
        self,
        results: List[SearchResult],
        response: str,
    ) -> List[Citation]:
        """
        Extract citations from results that were likely used in the response.

        Uses simple heuristic: if document name or key terms appear in response,
        include it as a citation.
        """
        citations = []
        response_lower = response.lower()

        for result in results:
            # Check if this source was likely used
            doc_name_lower = result.document_name.lower()
            is_cited = (
                doc_name_lower in response_lower
                or result.borough.lower() in response_lower
                or (result.section_title and result.section_title.lower() in response_lower)
            )

            # Also include high-relevance results
            if is_cited or result.similarity_score > 0.85:
                citations.append(
                    Citation(
                        document_name=result.document_name,
                        borough=result.borough,
                        section=result.section_title,
                        page_number=result.page_number,
                        paragraph=result.content[:200] + "..." if len(result.content) > 200 else result.content,
                        relevance_score=result.similarity_score,
                        chunk_id=result.chunk_id,
                    )
                )

        # Deduplicate by document name
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation.document_name not in seen:
                seen.add(citation.document_name)
                unique_citations.append(citation)

        return unique_citations[:5]  # Limit to top 5 citations


# Global instance
response_generator = ResponseGenerator()
