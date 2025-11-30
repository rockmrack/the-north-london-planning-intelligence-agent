"""
Hybrid retriever combining vector and keyword search.
Uses BM25 for keyword matching and cosine similarity for semantic search.
"""

import re
from typing import List, Optional, Tuple

from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.models.documents import SearchResult
from app.services.ingestion.embedder import embedding_service
from app.services.supabase import supabase_service


class HybridRetriever:
    """
    Hybrid search retriever combining:
    1. Vector similarity search (semantic understanding)
    2. BM25 keyword search (exact term matching)
    3. Optional metadata filtering (borough, category)
    """

    def __init__(self):
        self.vector_weight = settings.vector_weight
        self.bm25_weight = settings.bm25_weight
        self.use_hybrid = settings.hybrid_search_enabled

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        borough: Optional[str] = None,
        category: Optional[str] = None,
        similarity_threshold: float = None,
    ) -> List[SearchResult]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: The search query
            top_k: Number of results to return
            borough: Optional borough filter
            category: Optional category filter
            similarity_threshold: Minimum similarity score

        Returns:
            List of SearchResult objects
        """
        threshold = similarity_threshold or settings.similarity_threshold

        # Generate query embedding
        query_embedding = await embedding_service.embed_text(query)

        if self.use_hybrid:
            return await self._hybrid_search(
                query=query,
                query_embedding=query_embedding,
                top_k=top_k,
                borough=borough,
                category=category,
                threshold=threshold,
            )
        else:
            return await self._vector_search(
                query_embedding=query_embedding,
                top_k=top_k,
                borough=borough,
                category=category,
                threshold=threshold,
            )

    async def _vector_search(
        self,
        query_embedding: List[float],
        top_k: int,
        borough: Optional[str],
        category: Optional[str],
        threshold: float,
    ) -> List[SearchResult]:
        """Perform pure vector similarity search."""
        results = await supabase_service.vector_search(
            query_embedding=query_embedding,
            match_threshold=threshold,
            match_count=top_k,
            borough=borough,
            category=category,
        )
        return results

    async def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int,
        borough: Optional[str],
        category: Optional[str],
        threshold: float,
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector and BM25.

        This implementation:
        1. Gets top candidates from vector search
        2. Reranks using BM25 scores
        3. Combines scores with weighted average
        """
        # Get more candidates than needed for reranking
        candidate_count = min(top_k * 3, 50)

        # Vector search
        vector_results = await supabase_service.vector_search(
            query_embedding=query_embedding,
            match_threshold=threshold * 0.8,  # Lower threshold for candidates
            match_count=candidate_count,
            borough=borough,
            category=category,
        )

        if not vector_results:
            return []

        # Prepare texts for BM25
        texts = [r.content for r in vector_results]
        tokenized_texts = [self._tokenize(text) for text in texts]
        tokenized_query = self._tokenize(query)

        # Compute BM25 scores
        bm25 = BM25Okapi(tokenized_texts)
        bm25_scores = bm25.get_scores(tokenized_query)

        # Normalize BM25 scores to 0-1 range
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        normalized_bm25 = [s / max_bm25 for s in bm25_scores]

        # Combine scores
        combined_results = []
        for i, result in enumerate(vector_results):
            combined_score = (
                result.similarity_score * self.vector_weight
                + normalized_bm25[i] * self.bm25_weight
            )

            # Update result with combined scores
            result.bm25_score = normalized_bm25[i]
            result.combined_score = combined_score
            combined_results.append(result)

        # Sort by combined score and return top_k
        combined_results.sort(key=lambda x: x.combined_score or 0, reverse=True)
        return combined_results[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r"\b\w+\b", text.lower())
        # Remove very short tokens
        return [t for t in tokens if len(t) > 2]

    async def extract_query_metadata(
        self, query: str
    ) -> dict:
        """
        Extract metadata from query for filtering.

        Returns:
            Dict with detected borough, location, topic, etc.
        """
        query_lower = query.lower()
        metadata = {
            "borough": None,
            "conservation_area": None,
            "topic": None,
            "address": None,
            "postcode": None,
        }

        # Detect borough
        borough_patterns = {
            "Camden": ["camden", "hampstead", "belsize", "primrose hill", "kentish town"],
            "Barnet": ["barnet", "finchley", "golders green", "hendon", "mill hill"],
            "Westminster": ["westminster", "marylebone", "mayfair", "soho", "fitzrovia"],
            "Brent": ["brent", "wembley", "willesden", "kilburn", "neasden"],
            "Haringey": ["haringey", "highgate", "crouch end", "muswell hill", "hornsey"],
        }

        for borough, patterns in borough_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    metadata["borough"] = borough
                    break
            if metadata["borough"]:
                break

        # Detect postcode (UK format)
        postcode_pattern = r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b"
        postcode_match = re.search(postcode_pattern, query.upper())
        if postcode_match:
            metadata["postcode"] = postcode_match.group()

        # Detect topic
        topic_patterns = {
            "basement": ["basement", "subterranean", "cellar", "underground"],
            "extension": ["extension", "rear extension", "side extension", "wrap around"],
            "loft": ["loft", "dormer", "roof extension", "mansard"],
            "roof": ["roof", "rooflight", "skylight", "solar panel"],
            "windows": ["window", "glazing", "double glazing", "fenestration"],
            "conservation": ["conservation", "heritage", "listed", "article 4"],
            "permitted_development": ["permitted development", "pd rights", "prior approval"],
        }

        for topic, patterns in topic_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    metadata["topic"] = topic
                    break
            if metadata["topic"]:
                break

        # Detect conservation area names (common ones)
        conservation_areas = [
            "belsize park", "hampstead", "primrose hill", "south hampstead",
            "fitzjohns", "redington frognal", "west hampstead", "highgate",
        ]
        for area in conservation_areas:
            if area in query_lower:
                metadata["conservation_area"] = area.title()
                break

        return metadata


# Global instance
hybrid_retriever = HybridRetriever()
