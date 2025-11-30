"""
Embedding service using OpenAI's text-embedding-3-large model.
Includes batching, caching, and retry logic.
"""

import asyncio
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.cache import cache_service


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI.

    Features:
    - Batch processing for efficiency
    - Caching to avoid redundant API calls
    - Automatic retries with exponential backoff
    - Dimension validation
    """

    # text-embedding-3-large outputs 3072 dimensions
    EMBEDDING_DIMENSIONS = 3072
    MAX_BATCH_SIZE = 100  # OpenAI limit
    MAX_TOKENS_PER_TEXT = 8191  # Model limit

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    async def embed_text(
        self,
        text: str,
        use_cache: bool = True,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed
            use_cache: Whether to check/use cache

        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Check cache first
        if use_cache:
            cached = await cache_service.get_embedding(text)
            if cached:
                return cached

        # Generate embedding
        embedding = await self._generate_embedding(text)

        # Cache the result
        if use_cache:
            await cache_service.set_embedding(text, embedding)

        return embedding

    async def embed_texts(
        self,
        texts: List[str],
        use_cache: bool = True,
        show_progress: bool = False,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching.

        Args:
            texts: List of texts to embed
            use_cache: Whether to check/use cache
            show_progress: Whether to log progress

        Returns:
            List of embeddings in the same order as input texts
        """
        if not texts:
            return []

        # Initialize results array
        embeddings: List[Optional[List[float]]] = [None] * len(texts)
        texts_to_embed: List[tuple[int, str]] = []

        # Check cache for each text
        if use_cache:
            for i, text in enumerate(texts):
                if text and text.strip():
                    cached = await cache_service.get_embedding(text)
                    if cached:
                        embeddings[i] = cached
                    else:
                        texts_to_embed.append((i, text))
                else:
                    # Empty texts get zero vectors
                    embeddings[i] = [0.0] * self.EMBEDDING_DIMENSIONS
        else:
            texts_to_embed = [
                (i, text) for i, text in enumerate(texts) if text and text.strip()
            ]

        # Batch process remaining texts
        if texts_to_embed:
            batches = [
                texts_to_embed[i : i + self.MAX_BATCH_SIZE]
                for i in range(0, len(texts_to_embed), self.MAX_BATCH_SIZE)
            ]

            for batch_num, batch in enumerate(batches):
                if show_progress:
                    print(
                        f"Processing batch {batch_num + 1}/{len(batches)} "
                        f"({len(batch)} texts)"
                    )

                batch_texts = [text for _, text in batch]
                batch_embeddings = await self._generate_embeddings_batch(
                    batch_texts
                )

                # Store results and cache
                for (original_idx, text), embedding in zip(
                    batch, batch_embeddings
                ):
                    embeddings[original_idx] = embedding
                    if use_cache:
                        await cache_service.set_embedding(text, embedding)

                # Small delay between batches to respect rate limits
                if batch_num < len(batches) - 1:
                    await asyncio.sleep(0.1)

        # Handle any remaining None values (should not happen)
        for i, emb in enumerate(embeddings):
            if emb is None:
                embeddings[i] = [0.0] * self.EMBEDDING_DIMENSIONS

        return embeddings  # type: ignore

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding with retry logic."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for a batch with retry logic."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between 0 and 1
        """
        import math

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


# Global instance
embedding_service = EmbeddingService()
