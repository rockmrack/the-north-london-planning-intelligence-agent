"""
Document management API endpoints.
For ingesting and managing planning documents.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_required_token
from app.models.documents import (
    Borough,
    DocumentCategory,
    DocumentMetadata,
    IngestRequest,
    IngestResponse,
)
from app.services.ingestion.pipeline import ingestion_pipeline
from app.services.supabase import supabase_service

router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    dependencies=[Depends(get_required_token)],
)
async def ingest_document(
    request: IngestRequest,
) -> IngestResponse:
    """
    Ingest a document into the knowledge base.

    Requires authentication. Documents are:
    1. Parsed (PDF, DOCX, HTML supported)
    2. Chunked into semantic units
    3. Embedded using text-embedding-3-large
    4. Stored in the vector database

    **Example Request:**
    ```json
    {
        "file_path": "/path/to/document.pdf",
        "document_name": "Camden Local Plan 2024",
        "borough": "Camden",
        "category": "local_plan"
    }
    ```
    """
    try:
        if request.file_path:
            result = await ingestion_pipeline.ingest_file(
                file_path=request.file_path,
                document_name=request.document_name,
                borough=request.borough,
                category=request.category,
                source_url=request.source_url,
                overwrite=request.overwrite,
            )
        elif request.url:
            result = await ingestion_pipeline.ingest_url(
                url=request.url,
                document_name=request.document_name,
                borough=request.borough,
                category=request.category,
                overwrite=request.overwrite,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file_path or url must be provided",
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/ingest/upload",
    response_model=IngestResponse,
    dependencies=[Depends(get_required_token)],
)
async def upload_and_ingest(
    file: UploadFile = File(...),
    document_name: str = None,
    borough: Borough = Borough.CAMDEN,
    category: DocumentCategory = DocumentCategory.OTHER,
) -> IngestResponse:
    """
    Upload and ingest a document file.

    Accepts file uploads directly (PDF, DOCX, HTML, TXT).
    """
    import tempfile
    import os

    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Use filename if document_name not provided
        doc_name = document_name or file.filename or "Uploaded Document"

        # Ingest the file
        result = await ingestion_pipeline.ingest_file(
            file_path=tmp_path,
            document_name=doc_name,
            borough=borough,
            category=category,
        )

        # Clean up temp file
        os.unlink(tmp_path)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=List[DocumentMetadata],
)
async def list_documents(
    borough: Optional[str] = None,
    category: Optional[str] = None,
    is_active: bool = True,
) -> List[DocumentMetadata]:
    """
    List all ingested documents.

    Optional filters for borough and category.
    """
    documents = await supabase_service.list_documents(
        borough=borough,
        category=category,
        is_active=is_active,
    )
    return documents


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
)
async def get_document(
    document_id: str,
) -> DocumentMetadata:
    """
    Get a specific document by ID.
    """
    document = await supabase_service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


@router.delete(
    "/{document_id}",
    dependencies=[Depends(get_required_token)],
)
async def delete_document(
    document_id: str,
):
    """
    Delete a document and all its chunks.

    Requires authentication.
    """
    try:
        await supabase_service.delete_document(document_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/stats/summary")
async def get_document_stats():
    """
    Get summary statistics about ingested documents.
    """
    documents = await supabase_service.list_documents()

    # Calculate stats
    by_borough = {}
    by_category = {}
    total_chunks = 0
    total_pages = 0

    for doc in documents:
        borough = doc.borough.value if hasattr(doc.borough, 'value') else doc.borough
        category = doc.category.value if hasattr(doc.category, 'value') else doc.category

        by_borough[borough] = by_borough.get(borough, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
        total_chunks += doc.total_chunks or 0
        total_pages += doc.total_pages or 0

    return {
        "total_documents": len(documents),
        "total_chunks": total_chunks,
        "total_pages": total_pages,
        "by_borough": by_borough,
        "by_category": by_category,
    }
