"""
Semantic text chunking with overlap.
Creates intelligent chunks that preserve context and meaning.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

import tiktoken


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    content: str
    chunk_index: int
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    start_char: int = 0
    end_char: int = 0


class SemanticChunker:
    """
    Intelligent text chunker that:
    1. Respects sentence and paragraph boundaries
    2. Maintains context with overlap
    3. Preserves section structure
    4. Optimizes for embedding quality
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size in tokens per chunk
            chunk_overlap: Number of tokens to overlap between chunks
            encoding_name: Tiktoken encoding to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

        # Patterns for splitting
        self._paragraph_pattern = re.compile(r"\n\n+")
        self._sentence_pattern = re.compile(
            r"(?<=[.!?])\s+(?=[A-Z])|(?<=\.)\s*\n"
        )

    def chunk_text(
        self,
        text: str,
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
    ) -> List[TextChunk]:
        """
        Chunk text into semantic units.

        Args:
            text: The text to chunk
            page_number: Optional page number for metadata
            section_title: Optional section title for metadata

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # First split into paragraphs
        paragraphs = self._paragraph_pattern.split(text.strip())
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: List[TextChunk] = []
        current_content: List[str] = []
        current_tokens = 0
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            para_tokens = self._count_tokens(para)

            # If paragraph alone exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # First, finalize any current chunk
                if current_content:
                    chunk_text = "\n\n".join(current_content)
                    chunks.append(
                        TextChunk(
                            content=chunk_text,
                            chunk_index=chunk_index,
                            token_count=current_tokens,
                            page_number=page_number,
                            section_title=section_title,
                            start_char=current_start,
                            end_char=current_start + len(chunk_text),
                        )
                    )
                    chunk_index += 1
                    current_content = []
                    current_tokens = 0

                # Split large paragraph into sentences
                sentence_chunks = self._chunk_large_paragraph(
                    para, chunk_index, page_number, section_title
                )
                chunks.extend(sentence_chunks)
                chunk_index += len(sentence_chunks)
                current_start = chunks[-1].end_char if chunks else 0

            # If adding paragraph would exceed limit, start new chunk
            elif current_tokens + para_tokens > self.chunk_size:
                # Finalize current chunk
                chunk_text = "\n\n".join(current_content)
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        chunk_index=chunk_index,
                        token_count=current_tokens,
                        page_number=page_number,
                        section_title=section_title,
                        start_char=current_start,
                        end_char=current_start + len(chunk_text),
                    )
                )
                chunk_index += 1

                # Start new chunk with overlap
                overlap_content = self._get_overlap(current_content)
                current_start = chunks[-1].end_char
                current_content = overlap_content + [para]
                current_tokens = self._count_tokens(
                    "\n\n".join(current_content)
                )
            else:
                current_content.append(para)
                current_tokens += para_tokens

        # Don't forget the last chunk
        if current_content:
            chunk_text = "\n\n".join(current_content)
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    page_number=page_number,
                    section_title=section_title,
                    start_char=current_start,
                    end_char=current_start + len(chunk_text),
                )
            )

        return chunks

    def chunk_pages(
        self,
        pages: List[dict],
    ) -> List[TextChunk]:
        """
        Chunk multiple pages while preserving page boundaries.

        Args:
            pages: List of dicts with 'content', 'page_number', 'section_title'

        Returns:
            List of TextChunk objects
        """
        all_chunks: List[TextChunk] = []
        global_chunk_index = 0

        for page in pages:
            page_chunks = self.chunk_text(
                text=page.get("content", ""),
                page_number=page.get("page_number"),
                section_title=page.get("section_title"),
            )

            # Update chunk indices to be global
            for chunk in page_chunks:
                chunk.chunk_index = global_chunk_index
                global_chunk_index += 1
                all_chunks.append(chunk)

        return all_chunks

    def _chunk_large_paragraph(
        self,
        paragraph: str,
        start_index: int,
        page_number: Optional[int],
        section_title: Optional[str],
    ) -> List[TextChunk]:
        """Split a large paragraph by sentences."""
        sentences = self._sentence_pattern.split(paragraph)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: List[TextChunk] = []
        current_content: List[str] = []
        current_tokens = 0
        chunk_index = start_index
        current_start = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)

            # If single sentence exceeds limit, force split
            if sentence_tokens > self.chunk_size:
                # Finalize current
                if current_content:
                    chunk_text = " ".join(current_content)
                    chunks.append(
                        TextChunk(
                            content=chunk_text,
                            chunk_index=chunk_index,
                            token_count=current_tokens,
                            page_number=page_number,
                            section_title=section_title,
                            start_char=current_start,
                            end_char=current_start + len(chunk_text),
                        )
                    )
                    chunk_index += 1
                    current_content = []
                    current_tokens = 0
                    current_start = chunks[-1].end_char

                # Force split the long sentence
                forced_chunks = self._force_split(
                    sentence, chunk_index, page_number, section_title
                )
                chunks.extend(forced_chunks)
                chunk_index += len(forced_chunks)
                current_start = chunks[-1].end_char if chunks else 0

            elif current_tokens + sentence_tokens > self.chunk_size:
                # Start new chunk
                chunk_text = " ".join(current_content)
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        chunk_index=chunk_index,
                        token_count=current_tokens,
                        page_number=page_number,
                        section_title=section_title,
                        start_char=current_start,
                        end_char=current_start + len(chunk_text),
                    )
                )
                chunk_index += 1
                current_start = chunks[-1].end_char

                # Get overlap
                overlap = self._get_sentence_overlap(current_content)
                current_content = overlap + [sentence]
                current_tokens = self._count_tokens(" ".join(current_content))
            else:
                current_content.append(sentence)
                current_tokens += sentence_tokens

        # Final chunk
        if current_content:
            chunk_text = " ".join(current_content)
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    page_number=page_number,
                    section_title=section_title,
                    start_char=current_start,
                    end_char=current_start + len(chunk_text),
                )
            )

        return chunks

    def _force_split(
        self,
        text: str,
        start_index: int,
        page_number: Optional[int],
        section_title: Optional[str],
    ) -> List[TextChunk]:
        """Force split text that can't be split semantically."""
        tokens = self.encoding.encode(text)
        chunks: List[TextChunk] = []
        chunk_index = start_index

        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i : i + self.chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)

            chunks.append(
                TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=len(chunk_tokens),
                    page_number=page_number,
                    section_title=section_title,
                )
            )
            chunk_index += 1

        return chunks

    def _get_overlap(self, paragraphs: List[str]) -> List[str]:
        """Get overlap content from end of paragraph list."""
        if not paragraphs:
            return []

        # Take last paragraph(s) up to overlap token limit
        overlap: List[str] = []
        overlap_tokens = 0

        for para in reversed(paragraphs):
            para_tokens = self._count_tokens(para)
            if overlap_tokens + para_tokens <= self.chunk_overlap:
                overlap.insert(0, para)
                overlap_tokens += para_tokens
            else:
                break

        return overlap

    def _get_sentence_overlap(self, sentences: List[str]) -> List[str]:
        """Get overlap content from end of sentence list."""
        if not sentences:
            return []

        overlap: List[str] = []
        overlap_tokens = 0

        for sent in reversed(sentences):
            sent_tokens = self._count_tokens(sent)
            if overlap_tokens + sent_tokens <= self.chunk_overlap:
                overlap.insert(0, sent)
                overlap_tokens += sent_tokens
            else:
                break

        return overlap

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
