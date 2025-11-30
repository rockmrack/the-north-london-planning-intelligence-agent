#!/usr/bin/env python3
"""
Document Download Script
Downloads planning documents from council websites.

Usage:
    python scripts/download_documents.py
    python scripts/download_documents.py --borough camden
    python scripts/download_documents.py --list
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List

import httpx

# Base directory for documents
DOCUMENTS_DIR = Path(__file__).parent.parent / "documents"

# Document sources by borough
# Note: These are example URLs - actual URLs should be verified
DOCUMENT_SOURCES: Dict[str, List[dict]] = {
    "camden": [
        {
            "name": "Camden Local Plan",
            "url": "https://www.camden.gov.uk/documents/20142/0/Camden+Local+Plan.pdf",
            "category": "local_plan",
        },
        {
            "name": "Camden Planning Guidance",
            "url": "https://www.camden.gov.uk/documents/20142/0/Camden+Planning+Guidance.pdf",
            "category": "design_guide",
        },
        {
            "name": "Basement Development Guidance",
            "url": "https://www.camden.gov.uk/documents/20142/0/Basement+Guidance.pdf",
            "category": "basement",
        },
    ],
    "barnet": [
        {
            "name": "Barnet Local Plan",
            "url": "https://www.barnet.gov.uk/planning/local-plan/local-plan.pdf",
            "category": "local_plan",
        },
        {
            "name": "Residential Design Guidance",
            "url": "https://www.barnet.gov.uk/planning/design-guidance.pdf",
            "category": "design_guide",
        },
    ],
    "westminster": [
        {
            "name": "City Plan 2019-2040",
            "url": "https://www.westminster.gov.uk/planning/city-plan.pdf",
            "category": "local_plan",
        },
        {
            "name": "Basement Development SPD",
            "url": "https://www.westminster.gov.uk/planning/basement-spd.pdf",
            "category": "basement",
        },
    ],
    "brent": [
        {
            "name": "Brent Local Plan",
            "url": "https://www.brent.gov.uk/planning/local-plan.pdf",
            "category": "local_plan",
        },
        {
            "name": "Householder Design Guide",
            "url": "https://www.brent.gov.uk/planning/householder-guide.pdf",
            "category": "design_guide",
        },
    ],
    "haringey": [
        {
            "name": "Haringey Local Plan",
            "url": "https://www.haringey.gov.uk/planning/local-plan.pdf",
            "category": "local_plan",
        },
        {
            "name": "Extensions Design Guide",
            "url": "https://www.haringey.gov.uk/planning/extensions-guide.pdf",
            "category": "extensions",
        },
    ],
}


def create_directories():
    """Create document directories for each borough."""
    for borough in DOCUMENT_SOURCES.keys():
        borough_dir = DOCUMENTS_DIR / borough
        borough_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {borough_dir}")


def list_documents():
    """List all available documents."""
    print("\nAvailable documents for download:\n")
    for borough, docs in DOCUMENT_SOURCES.items():
        print(f"📁 {borough.title()}")
        for doc in docs:
            print(f"   └── {doc['name']} ({doc['category']})")
        print()


def download_document(url: str, output_path: Path) -> bool:
    """Download a single document."""
    try:
        print(f"  Downloading: {url}")
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            print(f"  ✓ Saved to: {output_path}")
            return True

    except httpx.HTTPStatusError as e:
        print(f"  ✗ HTTP error: {e.response.status_code}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


def download_borough(borough: str):
    """Download all documents for a borough."""
    if borough not in DOCUMENT_SOURCES:
        print(f"Unknown borough: {borough}")
        print(f"Available: {', '.join(DOCUMENT_SOURCES.keys())}")
        return

    print(f"\n📥 Downloading documents for {borough.title()}...\n")

    borough_dir = DOCUMENTS_DIR / borough
    borough_dir.mkdir(parents=True, exist_ok=True)

    docs = DOCUMENT_SOURCES[borough]
    success_count = 0

    for doc in docs:
        filename = f"{doc['name'].replace(' ', '_').lower()}.pdf"
        output_path = borough_dir / filename

        if output_path.exists():
            print(f"  ⏭ Skipping (exists): {doc['name']}")
            success_count += 1
            continue

        if download_document(doc["url"], output_path):
            success_count += 1

    print(f"\n✓ Downloaded {success_count}/{len(docs)} documents for {borough.title()}")


def download_all():
    """Download documents for all boroughs."""
    print("\n📥 Downloading all documents...\n")

    for borough in DOCUMENT_SOURCES.keys():
        download_borough(borough)

    print("\n✓ Download complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Download planning documents from council websites"
    )
    parser.add_argument(
        "--borough",
        "-b",
        type=str,
        help="Specific borough to download (camden, barnet, westminster, brent, haringey)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available documents without downloading",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Download all documents for all boroughs",
    )

    args = parser.parse_args()

    # Create base directories
    create_directories()

    if args.list:
        list_documents()
    elif args.borough:
        download_borough(args.borough.lower())
    elif args.all:
        download_all()
    else:
        # Default: show help
        parser.print_help()
        print("\n💡 Tip: Use --list to see available documents")


if __name__ == "__main__":
    main()
