#!/usr/bin/env python3
"""
Database backup utility for the Planning Intelligence Agent.
Exports data from Supabase to local JSON files for backup.
"""

import argparse
import asyncio
import gzip
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# Tables to backup with their configurations
BACKUP_TABLES = {
    "documents": {
        "select": "id, filename, borough, document_type, title, url, file_size, page_count, status, created_at, updated_at",
        "order": "created_at",
        "batch_size": 100,
    },
    "document_chunks": {
        "select": "id, document_id, chunk_index, content, metadata, created_at",
        "order": "document_id, chunk_index",
        "batch_size": 500,
        "large_table": True,
    },
    "leads": {
        "select": "*",
        "order": "created_at",
        "batch_size": 100,
    },
    "chat_sessions": {
        "select": "*",
        "order": "created_at",
        "batch_size": 200,
    },
    "query_analytics": {
        "select": "id, session_id, query_text, detected_borough, detected_topic, response_length, citations_count, processing_time_ms, user_feedback, is_follow_up, created_at",
        "order": "created_at",
        "batch_size": 500,
        "large_table": True,
    },
    "analytics_daily": {
        "select": "*",
        "order": "date",
        "batch_size": 100,
    },
    "boroughs": {
        "select": "*",
        "order": "name",
        "batch_size": 50,
    },
    "topics": {
        "select": "*",
        "order": "name",
        "batch_size": 50,
    },
}


async def get_supabase_client():
    """Get Supabase client."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    return create_client(url, key)


async def backup_table(
    client,
    table_name: str,
    config: dict,
    output_dir: Path,
    compress: bool = False,
    verbose: bool = False,
) -> dict:
    """Backup a single table."""
    print(f"\nBacking up {table_name}...")

    select_fields = config.get("select", "*")
    order_field = config.get("order", "created_at")
    batch_size = config.get("batch_size", 100)
    is_large = config.get("large_table", False)

    all_data = []
    offset = 0
    total_fetched = 0

    while True:
        try:
            query = client.table(table_name).select(select_fields)

            # Handle ordering
            if "," in order_field:
                # Multiple order fields - just use the first one
                primary_order = order_field.split(",")[0].strip()
                query = query.order(primary_order)
            else:
                query = query.order(order_field)

            query = query.range(offset, offset + batch_size - 1)
            result = query.execute()

            batch_data = result.data or []
            batch_count = len(batch_data)

            if batch_count == 0:
                break

            all_data.extend(batch_data)
            total_fetched += batch_count
            offset += batch_size

            if verbose:
                print(f"  Fetched {total_fetched} records...")

            # Safety limit for large tables
            if is_large and total_fetched >= 10000:
                print(f"  Reached 10,000 record limit for {table_name}")
                break

        except Exception as e:
            print(f"  Error fetching batch at offset {offset}: {e}")
            break

    print(f"  Total records: {total_fetched}")

    # Write to file
    output_file = output_dir / f"{table_name}.json"
    if compress:
        output_file = output_dir / f"{table_name}.json.gz"

    if compress:
        with gzip.open(output_file, "wt", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, default=str)
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, default=str)

    file_size = output_file.stat().st_size
    print(f"  Saved to: {output_file.name} ({file_size:,} bytes)")

    return {
        "table": table_name,
        "records": total_fetched,
        "file": str(output_file),
        "size": file_size,
    }


async def backup_all(
    tables: list = None,
    output_dir: str = None,
    compress: bool = False,
    verbose: bool = False,
) -> dict:
    """Backup all specified tables."""
    # Default to all tables
    if tables is None:
        tables = list(BACKUP_TABLES.keys())

    # Create output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.parent / "backups" / timestamp

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Backup directory: {output_path}")

    # Connect to Supabase
    client = await get_supabase_client()
    print("Connected to Supabase")

    # Backup each table
    results = []
    for table_name in tables:
        if table_name not in BACKUP_TABLES:
            print(f"\nSkipping unknown table: {table_name}")
            continue

        config = BACKUP_TABLES[table_name]
        try:
            result = await backup_table(
                client, table_name, config, output_path, compress, verbose
            )
            results.append(result)
        except Exception as e:
            print(f"\nError backing up {table_name}: {e}")
            results.append({
                "table": table_name,
                "error": str(e),
            })

    # Write manifest
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "tables": results,
        "total_records": sum(r.get("records", 0) for r in results),
        "total_size": sum(r.get("size", 0) for r in results),
    }

    manifest_file = output_path / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


async def restore_table(
    client,
    table_name: str,
    backup_file: Path,
    clear_existing: bool = False,
    verbose: bool = False,
) -> int:
    """Restore a single table from backup."""
    print(f"\nRestoring {table_name}...")

    # Read backup file
    if backup_file.suffix == ".gz":
        with gzip.open(backup_file, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    if not data:
        print(f"  No data to restore")
        return 0

    print(f"  Records to restore: {len(data)}")

    # Clear existing data if requested
    if clear_existing:
        try:
            client.table(table_name).delete().neq(
                "id", "00000000-0000-0000-0000-000000000000"
            ).execute()
            print(f"  Cleared existing data")
        except Exception as e:
            print(f"  Warning: Could not clear existing data: {e}")

    # Insert data in batches
    batch_size = 100
    restored = 0

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        try:
            client.table(table_name).upsert(batch).execute()
            restored += len(batch)
            if verbose:
                print(f"  Restored {restored}/{len(data)} records...")
        except Exception as e:
            print(f"  Error restoring batch {i}: {e}")

    print(f"  Restored {restored} records")
    return restored


async def restore_all(
    backup_dir: str,
    tables: list = None,
    clear_existing: bool = False,
    verbose: bool = False,
):
    """Restore all tables from a backup directory."""
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        print(f"Backup directory not found: {backup_path}")
        return

    # Read manifest
    manifest_file = backup_path / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"Restoring backup from: {manifest.get('timestamp', 'unknown')}")
    else:
        print("Warning: No manifest found, proceeding with available files")

    # Connect to Supabase
    client = await get_supabase_client()
    print("Connected to Supabase")

    # Find and restore backup files
    total_restored = 0

    for backup_file in sorted(backup_path.glob("*.json*")):
        if backup_file.name == "manifest.json":
            continue

        # Extract table name
        table_name = backup_file.stem
        if table_name.endswith(".json"):
            table_name = table_name[:-5]

        # Check if we should restore this table
        if tables and table_name not in tables:
            continue

        try:
            restored = await restore_table(
                client, table_name, backup_file, clear_existing, verbose
            )
            total_restored += restored
        except Exception as e:
            print(f"\nError restoring {table_name}: {e}")

    print(f"\nTotal records restored: {total_restored}")


async def list_backups(backups_dir: str = None):
    """List available backups."""
    if backups_dir is None:
        backups_dir = Path(__file__).parent.parent / "backups"

    backups_path = Path(backups_dir)

    if not backups_path.exists():
        print("No backups directory found")
        return

    print("\nAvailable backups:")
    print("-" * 60)

    for backup_dir in sorted(backups_path.iterdir(), reverse=True):
        if not backup_dir.is_dir():
            continue

        manifest_file = backup_dir / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            timestamp = manifest.get("timestamp", "unknown")
            records = manifest.get("total_records", 0)
            size = manifest.get("total_size", 0)

            print(f"\n{backup_dir.name}:")
            print(f"  Created: {timestamp}")
            print(f"  Records: {records:,}")
            print(f"  Size: {size:,} bytes")
        else:
            print(f"\n{backup_dir.name}: (no manifest)")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database backup utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument(
        "--tables",
        nargs="+",
        help="Specific tables to backup (default: all)",
    )
    backup_parser.add_argument(
        "--output",
        help="Output directory",
    )
    backup_parser.add_argument(
        "--compress",
        "-c",
        action="store_true",
        help="Compress output files with gzip",
    )
    backup_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument(
        "backup_dir",
        help="Backup directory to restore from",
    )
    restore_parser.add_argument(
        "--tables",
        nargs="+",
        help="Specific tables to restore (default: all)",
    )
    restore_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before restoring",
    )
    restore_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument(
        "--dir",
        help="Backups directory",
    )

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print("=" * 50)
    print("Database Backup Utility")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if args.command == "backup":
        manifest = await backup_all(
            tables=args.tables,
            output_dir=args.output,
            compress=args.compress,
            verbose=args.verbose,
        )

        print("\n" + "=" * 50)
        print("Backup Summary")
        print("=" * 50)
        print(f"Total records: {manifest['total_records']:,}")
        print(f"Total size: {manifest['total_size']:,} bytes")
        print("=" * 50)

    elif args.command == "restore":
        # Confirm before restoring
        if args.clear:
            response = input("\nThis will CLEAR existing data before restoring. Continue? [y/N]: ")
            if response.lower() != "y":
                print("Cancelled.")
                return

        await restore_all(
            backup_dir=args.backup_dir,
            tables=args.tables,
            clear_existing=args.clear,
            verbose=args.verbose,
        )

    elif args.command == "list":
        await list_backups(args.dir)

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
