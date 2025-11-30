"""
Reranker for improving retrieval quality.
Uses cross-encoder models or LLM-based reranking.
"""

from typing import List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.models.documents import SearchResult


class Reranker:
    """
    Reranks search results for improved relevance.

    Supports:
    1. LLM-based reranking (using GPT-4o)
    2. Simple heuristic reranking
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.enabled = settings.rerank_enabled
        self.top_k = settings.rerank_top_k

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Rerank search results based on query relevance.

        Args:
            query: The original query
            results: Search results to rerank
            top_k: Number of results to return

        Returns:
            Reranked list of SearchResult objects
        """
        if not self.enabled or not results:
            return results[:top_k] if top_k else results

        top_k = top_k or self.top_k

        # Use heuristic reranking (faster and cheaper than LLM)
        reranked = await self._heuristic_rerank(query, results)

        return reranked[:top_k]

    async def _heuristic_rerank(
        self,
        query: str,
        results: List[SearchResult],
    ) -> List[SearchResult]:
        """
        Heuristic reranking based on multiple factors.

        Factors considered:
        1. Original similarity score
        2. Query term presence
        3. Document freshness/authority
        4. Section relevance
        """
        query_terms = set(query.lower().split())
        scored_results = []

        for result in results:
            # Base score
            score = result.combined_score or result.similarity_score

            # Boost for query term presence
            content_lower = result.content.lower()
            term_matches = sum(1 for term in query_terms if term in content_lower)
            term_boost = term_matches * 0.05
            score += term_boost

            # Boost for exact phrase matches
            if query.lower() in content_lower:
                score += 0.1

            # Boost for section title matches
            if result.section_title:
                section_lower = result.section_title.lower()
                if any(term in section_lower for term in query_terms):
                    score += 0.1

            # Slight boost for earlier pages (often more relevant)
            if result.page_number and result.page_number < 20:
                score += 0.02

            scored_results.append((score, result))

        # Sort by score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [result for _, result in scored_results]

    async def _llm_rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int,
    ) -> List[SearchResult]:
        """
        LLM-based reranking for highest quality.
        More expensive but more accurate.
        """
        if len(results) <= top_k:
            return results

        # Prepare passages for LLM
        passages = []
        for i, result in enumerate(results):
            passages.append(f"[{i}] {result.content[:500]}...")

        prompt = f"""Given the query and passages below, rank the passages by relevance.
Return ONLY the passage numbers in order of relevance, comma-separated.

Query: {query}

Passages:
{chr(10).join(passages)}

Most relevant passage numbers (comma-separated):"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0,
            )

            # Parse response
            ranking_str = response.choices[0].message.content.strip()
            indices = [int(i.strip()) for i in ranking_str.split(",") if i.strip().isdigit()]

            # Reorder results
            reranked = []
            seen = set()
            for idx in indices[:top_k]:
                if 0 <= idx < len(results) and idx not in seen:
                    reranked.append(results[idx])
                    seen.add(idx)

            # Add any remaining results
            for i, result in enumerate(results):
                if i not in seen and len(reranked) < top_k:
                    reranked.append(result)

            return reranked

        except Exception:
            # Fallback to original order
            return results[:top_k]


# Global instance
reranker = Reranker()
