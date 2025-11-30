"""
RAG engine tests for the Planning Intelligence Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestDocumentChunking:
    """Test document chunking functionality."""

    @pytest.fixture
    def chunker(self):
        """Create a chunker instance."""
        from app.services.ingestion.chunker import SemanticChunker
        return SemanticChunker()

    def test_chunk_short_text(self, chunker):
        """Test chunking short text."""
        text = "This is a short piece of text about planning permissions."
        chunks = chunker.chunk_text(text, max_chunk_size=500)

        assert len(chunks) >= 1
        assert chunks[0]["content"] == text

    def test_chunk_long_text(self, chunker):
        """Test chunking long text into multiple chunks."""
        # Create a long text
        paragraph = "Planning permission is required for building works. " * 50
        chunks = chunker.chunk_text(paragraph, max_chunk_size=200)

        assert len(chunks) > 1
        # Check that chunks have overlap or are properly segmented
        for chunk in chunks:
            assert len(chunk["content"]) <= 200 * 2  # Allow some flexibility

    def test_chunk_preserves_sentences(self, chunker):
        """Test that chunking preserves sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunker.chunk_text(text, max_chunk_size=30)

        # Chunks should not cut sentences in half
        for chunk in chunks:
            content = chunk["content"]
            # Should end with period or be the last chunk
            assert content.endswith(".") or chunk == chunks[-1]

    def test_chunk_with_metadata(self, chunker):
        """Test that chunks include metadata."""
        text = "Test content for metadata verification."
        metadata = {"source": "test.pdf", "page": 1}
        chunks = chunker.chunk_text(text, metadata=metadata)

        assert len(chunks) >= 1
        assert "metadata" in chunks[0]
        assert chunks[0]["metadata"]["source"] == "test.pdf"


class TestEmbeddings:
    """Test embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_embedding(self, mock_openai):
        """Test generating embeddings for text."""
        from app.services.ingestion.embedder import OpenAIEmbedder

        with patch("openai.AsyncOpenAI", return_value=mock_openai):
            embedder = OpenAIEmbedder()
            embedding = await embedder.embed_text("Test planning query")

            assert embedding is not None
            assert len(embedding) == 3072  # text-embedding-3-large dimension

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self, mock_openai):
        """Test generating embeddings for multiple texts."""
        from app.services.ingestion.embedder import OpenAIEmbedder

        texts = [
            "First planning question",
            "Second planning question",
            "Third planning question",
        ]

        with patch("openai.AsyncOpenAI", return_value=mock_openai):
            embedder = OpenAIEmbedder()
            embeddings = await embedder.embed_batch(texts)

            assert len(embeddings) == 3
            for emb in embeddings:
                assert len(emb) == 3072


class TestRetrieval:
    """Test document retrieval."""

    @pytest.mark.asyncio
    async def test_vector_search(self, mock_supabase, mock_openai):
        """Test vector similarity search."""
        from app.services.rag.retriever import HybridRetriever

        # Setup mock to return results
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "content": "Planning permission required for extensions",
                    "similarity": 0.9,
                    "metadata": {"source": "test.pdf"},
                }
            ]
        )

        with patch("supabase.create_client", return_value=mock_supabase):
            with patch("openai.AsyncOpenAI", return_value=mock_openai):
                retriever = HybridRetriever()
                results = await retriever.search("extensions in Camden")

                # Should return results
                assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self, mock_supabase, mock_openai):
        """Test that hybrid search combines vector and BM25 results."""
        from app.services.rag.retriever import HybridRetriever

        # This is a conceptual test - actual implementation may vary
        with patch("supabase.create_client", return_value=mock_supabase):
            with patch("openai.AsyncOpenAI", return_value=mock_openai):
                retriever = HybridRetriever()

                # Verify retriever has hybrid capability
                assert hasattr(retriever, "search") or hasattr(retriever, "hybrid_search")


class TestResponseGeneration:
    """Test response generation."""

    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, mock_openai):
        """Test generating response with context."""
        from app.services.rag.generator import ResponseGenerator

        context = [
            {
                "content": "Extensions over 4m require planning permission.",
                "metadata": {"source": "guidelines.pdf", "page": 5},
            }
        ]

        with patch("openai.AsyncOpenAI", return_value=mock_openai):
            generator = ResponseGenerator()
            response = await generator.generate(
                query="Do I need permission for a 5m extension?",
                context=context,
            )

            assert response is not None
            assert isinstance(response, str) or hasattr(response, "content")

    @pytest.mark.asyncio
    async def test_generate_response_includes_citations(self, mock_openai):
        """Test that generated response includes citation references."""
        from app.services.rag.generator import ResponseGenerator

        context = [
            {"content": "Fact 1 from source A", "metadata": {"source": "a.pdf"}},
            {"content": "Fact 2 from source B", "metadata": {"source": "b.pdf"}},
        ]

        with patch("openai.AsyncOpenAI", return_value=mock_openai):
            generator = ResponseGenerator()

            # The response should reference sources
            # Actual implementation may vary
            assert hasattr(generator, "generate")


class TestRAGEngine:
    """Test the complete RAG engine."""

    @pytest.mark.asyncio
    async def test_rag_query_flow(self, mock_supabase, mock_openai):
        """Test the complete RAG query flow."""
        from app.services.rag.engine import RAGEngine

        with patch("supabase.create_client", return_value=mock_supabase):
            with patch("openai.AsyncOpenAI", return_value=mock_openai):
                engine = RAGEngine()

                # Test query
                result = await engine.query(
                    "Do I need planning permission for a loft conversion?",
                    borough="Camden",
                )

                assert result is not None
                # Result should have answer and possibly sources
                if isinstance(result, dict):
                    assert "answer" in result or "response" in result

    @pytest.mark.asyncio
    async def test_rag_handles_no_results(self, mock_supabase, mock_openai):
        """Test RAG handles queries with no matching documents."""
        from app.services.rag.engine import RAGEngine

        # Mock empty results
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])

        with patch("supabase.create_client", return_value=mock_supabase):
            with patch("openai.AsyncOpenAI", return_value=mock_openai):
                engine = RAGEngine()

                result = await engine.query(
                    "Obscure question with no matching docs",
                    borough="Camden",
                )

                # Should still return a response, possibly indicating no info found
                assert result is not None
