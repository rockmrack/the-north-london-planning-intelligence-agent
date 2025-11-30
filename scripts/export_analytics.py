#!/usr/bin/env python3
"""
Export analytics data to CSV or JSON format.
Useful for reporting and external analysis.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def get_supabase_client():
    """Get Supabase client."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    return create_client(url, key)


async def export_queries(
    start_date: datetime,
    end_date: datetime,
    output_path: str,
    format: str = "csv",
):
    """Export query analytics data."""
    print(f"Exporting queries from {start_date.date()} to {end_date.date()}...")

    client = await get_supabase_client()

    result = client.table("query_analytics").select(
        "id, session_id, query_text, detected_borough, detected_topic, "
        "response_length, citations_count, processing_time_ms, "
        "user_feedback, is_follow_up, lead_captured, created_at"
    ).gte(
        "created_at", start_date.isoformat()
    ).lte(
        "created_at", end_date.isoformat()
    ).order("created_at").execute()

    data = result.data or []
    print(f"Found {len(data)} queries")

    if format == "csv":
        _write_csv(data, output_path)
    else:
        _write_json(data, output_path)

    print(f"Exported to {output_path}")
    return len(data)


async def export_leads(
    start_date: datetime,
    end_date: datetime,
    output_path: str,
    format: str = "csv",
):
    """Export leads data."""
    print(f"Exporting leads from {start_date.date()} to {end_date.date()}...")

    client = await get_supabase_client()

    result = client.table("leads").select(
        "id, email, name, phone, postcode, borough, project_type, "
        "status, query_count, source, marketing_consent, "
        "created_at, last_activity, converted_at"
    ).gte(
        "created_at", start_date.isoformat()
    ).lte(
        "created_at", end_date.isoformat()
    ).order("created_at").execute()

    data = result.data or []
    print(f"Found {len(data)} leads")

    if format == "csv":
        _write_csv(data, output_path)
    else:
        _write_json(data, output_path)

    print(f"Exported to {output_path}")
    return len(data)


async def export_sessions(
    start_date: datetime,
    end_date: datetime,
    output_path: str,
    format: str = "csv",
):
    """Export sessions data."""
    print(f"Exporting sessions from {start_date.date()} to {end_date.date()}...")

    client = await get_supabase_client()

    result = client.table("chat_sessions").select(
        "id, lead_id, query_count, detected_borough, "
        "created_at, last_activity"
    ).gte(
        "created_at", start_date.isoformat()
    ).lte(
        "created_at", end_date.isoformat()
    ).order("created_at").execute()

    data = result.data or []
    print(f"Found {len(data)} sessions")

    if format == "csv":
        _write_csv(data, output_path)
    else:
        _write_json(data, output_path)

    print(f"Exported to {output_path}")
    return len(data)


async def export_daily_summary(
    start_date: datetime,
    end_date: datetime,
    output_path: str,
    format: str = "csv",
):
    """Export daily aggregated analytics."""
    print(f"Exporting daily summary from {start_date.date()} to {end_date.date()}...")

    client = await get_supabase_client()

    result = client.table("analytics_daily").select("*").gte(
        "date", start_date.date().isoformat()
    ).lte(
        "date", end_date.date().isoformat()
    ).order("date").execute()

    data = result.data or []
    print(f"Found {len(data)} daily records")

    if format == "csv":
        _write_csv(data, output_path)
    else:
        _write_json(data, output_path)

    print(f"Exported to {output_path}")
    return len(data)


def _write_csv(data: list, output_path: str):
    """Write data to CSV file."""
    if not data:
        print("No data to export")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def _write_json(data: list, output_path: str):
    """Write data to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Export analytics data")
    parser.add_argument(
        "type",
        choices=["queries", "leads", "sessions", "daily", "all"],
        help="Type of data to export",
    )
    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now() - timedelta(days=30),
        help="Start date (YYYY-MM-DD), default: 30 days ago",
    )
    parser.add_argument(
        "--end-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now(),
        help="End date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--output-dir",
        default="./exports",
        help="Output directory, default: ./exports",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format, default: csv",
    )

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Export requested data
    if args.type in ["queries", "all"]:
        output_path = output_dir / f"queries_{timestamp}.{args.format}"
        await export_queries(args.start_date, args.end_date, str(output_path), args.format)

    if args.type in ["leads", "all"]:
        output_path = output_dir / f"leads_{timestamp}.{args.format}"
        await export_leads(args.start_date, args.end_date, str(output_path), args.format)

    if args.type in ["sessions", "all"]:
        output_path = output_dir / f"sessions_{timestamp}.{args.format}"
        await export_sessions(args.start_date, args.end_date, str(output_path), args.format)

    if args.type in ["daily", "all"]:
        output_path = output_dir / f"daily_summary_{timestamp}.{args.format}"
        await export_daily_summary(args.start_date, args.end_date, str(output_path), args.format)

    print("\nExport complete!")


if __name__ == "__main__":
    asyncio.run(main())
