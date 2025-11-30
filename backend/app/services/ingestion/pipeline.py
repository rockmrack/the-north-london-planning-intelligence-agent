"""
Document ingestion pipeline.
Orchestrates parsing, chunking, embedding, and storage.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import structlog

from app.core.config import settings
from app.models.documents import (
    Borough,
    DocumentCategory,
    DocumentChunk,
    DocumentMetadata,
    IngestResponse,
)
from app.services.ingestion.chunker import SemanticChunker, TextChunk
from app.services.ingestion.embedder import embedding_service
from app.services.ingestion.parser import DocumentParser, ParsedDocument
from app.services.supabase import supabase_service

logger = structlog.get_logger()


class IngestionPipeline:
    """
    Complete document ingestion pipeline.

    Workflow:
    1. Parse document (PDF, DOCX, HTML)
    2. Chunk into semantic units
    3. Generate embeddings
    4. Store in Supabase
    """

    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = SemanticChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def ingest_file(
        self,
        file_path: str,
        document_name: str,
        borough: Borough,
        category: DocumentCategory,
        source_url: Optional[str] = None,
        overwrite: bool = False,
    ) -> IngestResponse:
        """
        Ingest a document from a file path.

        Args:
            file_path: Path to the document file
            document_name: Human-readable name for the document
            borough: Borough the document belongs to
            category: Category of the document
            source_url: Original source URL if applicable
            overwrite: Whether to overwrite existing document

        Returns:
            IngestResponse with results
        """
        start_time = time.time()
        errors: List[str] = []
        warnings: List[str] = []

        try:
            # Validate file exists
            path = Path(file_path)
            if not path.exists():
                return IngestResponse(
                    success=False,
                    document_id="",
                    document_name=document_name,
                    chunks_created=0,
                    total_tokens=0,
                    processing_time_seconds=time.time() - start_time,
                    errors=[f"File not found: {file_path}"],
                )

            # Generate document ID
            document_id = str(uuid.uuid4())

            logger.info(
                "Starting document ingestion",
                document_id=document_id,
                file_path=file_path,
                borough=borough.value if hasattr(borough, 'value') else borough,
            )

            # Step 1: Parse the document
            logger.info("Parsing document", document_id=document_id)
            parsed_doc = await self.parser.parse(file_path)

            if not parsed_doc.pages:
                return IngestResponse(
                    success=False,
                    document_id=document_id,
                    document_name=document_name,
                    chunks_created=0,
                    total_tokens=0,
                    processing_time_seconds=time.time() - start_time,
                    errors=["No content extracted from document"],
                )

            logger.info(
                "Document parsed",
                document_id=document_id,
                total_pages=parsed_doc.total_pages,
            )

            # Step 2: Chunk the document
            logger.info("Chunking document", document_id=document_id)
            pages_data = [
                {
                    "content": page.content,
                    "page_number": page.page_number,
                    "section_title": page.section_title,
                }
                for page in parsed_doc.pages
            ]
            text_chunks = self.chunker.chunk_pages(pages_data)

            if not text_chunks:
                return IngestResponse(
                    success=False,
                    document_id=document_id,
                    document_name=document_name,
                    chunks_created=0,
                    total_tokens=0,
                    processing_time_seconds=time.time() - start_time,
                    errors=["No chunks created from document"],
                )

            logger.info(
                "Document chunked",
                document_id=document_id,
                total_chunks=len(text_chunks),
            )

            # Step 3: Generate embeddings
            logger.info(
                "Generating embeddings",
                document_id=document_id,
                chunk_count=len(text_chunks),
            )
            chunk_contents = [chunk.content for chunk in text_chunks]
            embeddings = await embedding_service.embed_texts(
                chunk_contents, show_progress=True
            )

            # Step 4: Create document chunks
            document_chunks = []
            total_tokens = 0

            for i, (text_chunk, embedding) in enumerate(
                zip(text_chunks, embeddings)
            ):
                chunk_id = f"{document_id}-{i:05d}"
                total_tokens += text_chunk.token_count

                document_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        content=text_chunk.content,
                        page_number=text_chunk.page_number,
                        section_title=text_chunk.section_title,
                        chunk_index=text_chunk.chunk_index,
                        token_count=text_chunk.token_count,
                        embedding=embedding,
                        metadata={
                            "borough": borough.value if hasattr(borough, 'value') else borough,
                            "category": category.value if hasattr(category, 'value') else category,
                            "document_name": document_name,
                        },
                    )
                )

            # Step 5: Store in database
            logger.info(
                "Storing in database",
                document_id=document_id,
                chunk_count=len(document_chunks),
            )

            # Create document metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                document_name=document_name,
                borough=borough,
                category=category,
                source_url=source_url,
                file_path=file_path,
                file_type=parsed_doc.file_type,
                total_pages=parsed_doc.total_pages,
                total_chunks=len(document_chunks),
                ingested_at=datetime.utcnow(),
            )

            await supabase_service.insert_document(metadata)
            await supabase_service.insert_chunks(document_chunks)

            processing_time = time.time() - start_time

            logger.info(
                "Ingestion complete",
                document_id=document_id,
                chunks_created=len(document_chunks),
                total_tokens=total_tokens,
                processing_time=processing_time,
            )

            return IngestResponse(
                success=True,
                document_id=document_id,
                document_name=document_name,
                chunks_created=len(document_chunks),
                total_tokens=total_tokens,
                processing_time_seconds=processing_time,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(
                "Ingestion failed",
                error=str(e),
                file_path=file_path,
            )
            return IngestResponse(
                success=False,
                document_id="",
                document_name=document_name,
                chunks_created=0,
                total_tokens=0,
                processing_time_seconds=time.time() - start_time,
                errors=[str(e)],
            )

    async def ingest_url(
        self,
        url: str,
        document_name: str,
        borough: Borough,
        category: DocumentCategory,
        overwrite: bool = False,
    ) -> IngestResponse:
        """
        Ingest a document from a URL.

        Args:
            url: URL to fetch the document from
            document_name: Human-readable name for the document
            borough: Borough the document belongs to
            category: Category of the document
            overwrite: Whether to overwrite existing document

        Returns:
            IngestResponse with results
        """
        start_time = time.time()

        try:
            document_id = str(uuid.uuid4())

            logger.info(
                "Starting URL ingestion",
                document_id=document_id,
                url=url,
            )

            # Parse from URL
            parsed_doc = await self.parser.parse_from_url(url)

            if not parsed_doc.pages:
                return IngestResponse(
                    success=False,
                    document_id=document_id,
                    document_name=document_name,
                    chunks_created=0,
                    total_tokens=0,
                    processing_time_seconds=time.time() - start_time,
                    errors=["No content extracted from URL"],
                )

            # Rest of the pipeline is same as file ingestion
            pages_data = [
                {
                    "content": page.content,
                    "page_number": page.page_number,
                    "section_title": page.section_title,
                }
                for page in parsed_doc.pages
            ]
            text_chunks = self.chunker.chunk_pages(pages_data)

            chunk_contents = [chunk.content for chunk in text_chunks]
            embeddings = await embedding_service.embed_texts(chunk_contents)

            document_chunks = []
            total_tokens = 0

            for i, (text_chunk, embedding) in enumerate(
                zip(text_chunks, embeddings)
            ):
                chunk_id = f"{document_id}-{i:05d}"
                total_tokens += text_chunk.token_count

                document_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        content=text_chunk.content,
                        page_number=text_chunk.page_number,
                        section_title=text_chunk.section_title,
                        chunk_index=text_chunk.chunk_index,
                        token_count=text_chunk.token_count,
                        embedding=embedding,
                        metadata={
                            "borough": borough.value if hasattr(borough, 'value') else borough,
                            "category": category.value if hasattr(category, 'value') else category,
                            "document_name": document_name,
                            "source_url": url,
                        },
                    )
                )

            metadata = DocumentMetadata(
                document_id=document_id,
                document_name=document_name,
                borough=borough,
                category=category,
                source_url=url,
                file_type=parsed_doc.file_type,
                total_pages=parsed_doc.total_pages,
                total_chunks=len(document_chunks),
            )

            await supabase_service.insert_document(metadata)
            await supabase_service.insert_chunks(document_chunks)

            return IngestResponse(
                success=True,
                document_id=document_id,
                document_name=document_name,
                chunks_created=len(document_chunks),
                total_tokens=total_tokens,
                processing_time_seconds=time.time() - start_time,
            )

        except Exception as e:
            logger.error("URL ingestion failed", error=str(e), url=url)
            return IngestResponse(
                success=False,
                document_id="",
                document_name=document_name,
                chunks_created=0,
                total_tokens=0,
                processing_time_seconds=time.time() - start_time,
                errors=[str(e)],
            )

    async def ingest_directory(
        self,
        directory: str,
        borough: Borough,
        category: DocumentCategory,
        recursive: bool = True,
    ) -> List[IngestResponse]:
        """
        Ingest all documents from a directory.

        Args:
            directory: Path to directory containing documents
            borough: Borough for all documents
            category: Category for all documents
            recursive: Whether to search subdirectories

        Returns:
            List of IngestResponse objects
        """
        results: List[IngestResponse] = []
        path = Path(directory)

        if not path.exists() or not path.is_dir():
            return [
                IngestResponse(
                    success=False,
                    document_id="",
                    document_name=directory,
                    chunks_created=0,
                    total_tokens=0,
                    processing_time_seconds=0,
                    errors=[f"Directory not found: {directory}"],
                )
            ]

        # Get all supported files
        patterns = ["*.pdf", "*.docx", "*.doc", "*.html", "*.htm", "*.txt"]
        files = []
        for pattern in patterns:
            if recursive:
                files.extend(path.rglob(pattern))
            else:
                files.extend(path.glob(pattern))

        logger.info(
            "Found files for ingestion",
            directory=directory,
            file_count=len(files),
        )

        for file_path in files:
            result = await self.ingest_file(
                file_path=str(file_path),
                document_name=file_path.stem,
                borough=borough,
                category=category,
            )
            results.append(result)

        return results


# Global instance
ingestion_pipeline = IngestionPipeline()
