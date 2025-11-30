#!/usr/bin/env python3
"""
Document Ingestion Script
Processes and ingests planning documents into the vector database.

Usage:
    python scripts/ingest_documents.py
    python scripts/ingest_documents.py --source ./documents/camden
    python scripts/ingest_documents.py --file ./documents/camden/local_plan.pdf
    python scripts/ingest_documents.py --batch-size 50
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.models.documents import Borough, DocumentCategory
from app.services.ingestion.pipeline import IngestionPipeline

# Default paths
DOCUMENTS_DIR = Path(__file__).parent.parent / "documents"

# Borough mapping from directory names
BOROUGH_MAP = {
    "camden": Borough.CAMDEN,
    "barnet": Borough.BARNET,
    "westminster": Borough.WESTMINSTER,
    "brent": Borough.BRENT,
    "haringey": Borough.HARINGEY,
}

# Category detection patterns
CATEGORY_PATTERNS = {
    "local_plan": ["local plan", "local-plan", "localplan"],
    "conservation_area": ["conservation", "appraisal"],
    "design_guide": ["design guide", "design guidance", "design-guide"],
    "basement": ["basement", "subterranean"],
    "extensions": ["extension", "householder"],
    "roof": ["roof", "dormer", "loft"],
    "heritage": ["heritage", "listed building"],
    "sustainability": ["sustainability", "sustainable", "environment"],
}


def detect_category(filename: str) -> DocumentCategory:
    """Detect document category from filename."""
    filename_lower = filename.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in filename_lower:
                return DocumentCategory(category)
    return DocumentCategory.OTHER


def detect_borough(filepath: Path) -> Borough:
    """Detect borough from file path."""
    path_str = str(filepath).lower()
    for borough_name, borough_enum in BOROUGH_MAP.items():
        if borough_name in path_str:
            return borough_enum
    return Borough.CAMDEN  # Default


async def ingest_file(
    pipeline: IngestionPipeline,
    filepath: Path,
    borough: Borough = None,
    category: DocumentCategory = None,
):
    """Ingest a single file."""
    if borough is None:
        borough = detect_borough(filepath)
    if category is None:
        category = detect_category(filepath.name)

    print(f"\n📄 Ingesting: {filepath.name}")
    print(f"   Borough: {borough.value}")
    print(f"   Category: {category.value}")

    result = await pipeline.ingest_file(
        file_path=str(filepath),
        document_name=filepath.stem.replace("_", " ").title(),
        borough=borough,
        category=category,
    )

    if result.success:
        print(f"   ✓ Created {result.chunks_created} chunks ({result.total_tokens} tokens)")
        print(f"   ✓ Processing time: {result.processing_time_seconds:.2f}s")
    else:
        print(f"   ✗ Failed: {result.errors}")

    return result


async def ingest_directory(
    pipeline: IngestionPipeline,
    directory: Path,
    borough: Borough = None,
    recursive: bool = True,
):
    """Ingest all documents in a directory."""
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return []

    # Find all supported files
    patterns = ["*.pdf", "*.docx", "*.doc", "*.html", "*.htm", "*.txt"]
    files = []
    for pattern in patterns:
        if recursive:
            files.extend(directory.rglob(pattern))
        else:
            files.extend(directory.glob(pattern))

    if not files:
        print(f"No documents found in: {directory}")
        return []

    print(f"\n📁 Found {len(files)} documents in {directory}")

    results = []
    for filepath in files:
        result = await ingest_file(pipeline, filepath, borough)
        results.append(result)

    # Summary
    success_count = sum(1 for r in results if r.success)
    print(f"\n{'='*50}")
    print(f"✓ Ingested {success_count}/{len(results)} documents")

    total_chunks = sum(r.chunks_created for r in results if r.success)
    total_tokens = sum(r.total_tokens for r in results if r.success)
    print(f"✓ Total chunks: {total_chunks}")
    print(f"✓ Total tokens: {total_tokens}")

    return results


async def main():
    parser = argparse.ArgumentParser(
        description="Ingest planning documents into the vector database"
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=str(DOCUMENTS_DIR),
        help="Source directory containing documents",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Single file to ingest",
    )
    parser.add_argument(
        "--borough",
        "-b",
        type=str,
        choices=["camden", "barnet", "westminster", "brent", "haringey"],
        help="Override borough detection",
    )
    parser.add_argument(
        "--category",
        "-c",
        type=str,
        help="Override category detection",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding generation",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't search subdirectories",
    )

    args = parser.parse_args()

    # Initialize pipeline
    print("🚀 Initializing ingestion pipeline...")
    pipeline = IngestionPipeline()

    # Parse optional overrides
    borough = BOROUGH_MAP.get(args.borough) if args.borough else None
    category = DocumentCategory(args.category) if args.category else None

    if args.file:
        # Ingest single file
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"File not found: {filepath}")
            sys.exit(1)
        await ingest_file(pipeline, filepath, borough, category)
    else:
        # Ingest directory
        directory = Path(args.source)
        await ingest_directory(
            pipeline,
            directory,
            borough,
            recursive=not args.no_recursive,
        )


if __name__ == "__main__":
    asyncio.run(main())
