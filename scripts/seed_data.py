#!/usr/bin/env python3
"""
Seed the database with sample data for development and testing.
Creates sample boroughs, topics, documents, and test leads.
"""

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from random import choice, randint, uniform

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# Sample data
BOROUGHS = [
    {
        "name": "Camden",
        "description": "London Borough of Camden - covers areas including Hampstead, Holborn, King's Cross",
    },
    {
        "name": "Barnet",
        "description": "London Borough of Barnet - covers areas including Finchley, Hendon, Edgware",
    },
    {
        "name": "Westminster",
        "description": "City of Westminster - covers central London including Mayfair, Soho, Marylebone",
    },
    {
        "name": "Brent",
        "description": "London Borough of Brent - covers areas including Wembley, Kilburn, Willesden",
    },
    {
        "name": "Haringey",
        "description": "London Borough of Haringey - covers areas including Tottenham, Muswell Hill, Crouch End",
    },
]

TOPICS = [
    {
        "name": "extensions",
        "description": "House extensions including rear, side, and loft extensions",
        "example_questions": [
            "Can I build a rear extension without planning permission?",
            "What is the maximum height for a single storey extension?",
            "Do I need planning permission for a loft conversion?",
        ],
    },
    {
        "name": "permitted_development",
        "description": "Works allowed under permitted development rights",
        "example_questions": [
            "What can I build under permitted development?",
            "Are there restrictions on permitted development in conservation areas?",
            "Can I convert my garage under PD rights?",
        ],
    },
    {
        "name": "conservation_areas",
        "description": "Special considerations for conservation areas",
        "example_questions": [
            "What extra restrictions apply in conservation areas?",
            "Do I need permission to change windows in a conservation area?",
            "Can I install solar panels in a conservation area?",
        ],
    },
    {
        "name": "listed_buildings",
        "description": "Requirements for listed building consent",
        "example_questions": [
            "What works need listed building consent?",
            "Can I replace windows in a listed building?",
            "How long does listed building consent take?",
        ],
    },
    {
        "name": "change_of_use",
        "description": "Changing the use of a property or land",
        "example_questions": [
            "Can I convert my house to flats?",
            "Do I need permission for a home office?",
            "What is Class E use?",
        ],
    },
]

SAMPLE_QUERIES = [
    "Can I build a 4 metre rear extension?",
    "What are the rules for loft conversions in Camden?",
    "Do I need planning permission for a garden room?",
    "How close to the boundary can I build?",
    "What is the height limit for fences?",
    "Can I convert my garage into a bedroom?",
    "Do I need permission for solar panels?",
    "What are Article 4 directions?",
    "How long does planning permission take?",
    "Can I build in my front garden?",
]

SAMPLE_NAMES = [
    "John Smith", "Sarah Johnson", "Michael Brown", "Emma Wilson",
    "David Taylor", "Lucy Davies", "James Anderson", "Sophie Thomas",
    "Robert Jackson", "Emily White", "William Harris", "Olivia Martin",
]

PROJECT_TYPES = [
    "rear_extension", "loft_conversion", "side_extension",
    "change_of_use", "new_build", "renovation", "other",
]


async def get_supabase_client():
    """Get Supabase client."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    return create_client(url, key)


async def seed_boroughs(client, verbose: bool = False):
    """Seed borough reference data."""
    print("Seeding boroughs...")

    for borough in BOROUGHS:
        try:
            result = client.table("boroughs").upsert(
                borough,
                on_conflict="name"
            ).execute()
            if verbose:
                print(f"  - {borough['name']}")
        except Exception as e:
            print(f"  - Error seeding {borough['name']}: {e}")

    print(f"  Seeded {len(BOROUGHS)} boroughs")


async def seed_topics(client, verbose: bool = False):
    """Seed topic reference data."""
    print("Seeding topics...")

    for topic in TOPICS:
        try:
            result = client.table("topics").upsert(
                topic,
                on_conflict="name"
            ).execute()
            if verbose:
                print(f"  - {topic['name']}")
        except Exception as e:
            print(f"  - Error seeding {topic['name']}: {e}")

    print(f"  Seeded {len(TOPICS)} topics")


async def seed_sample_sessions(client, count: int = 50, verbose: bool = False):
    """Seed sample chat sessions."""
    print(f"Seeding {count} sample sessions...")

    sessions_created = 0
    for i in range(count):
        session_id = str(uuid.uuid4())
        borough = choice(BOROUGHS)["name"]
        created_at = datetime.utcnow() - timedelta(
            days=randint(0, 30),
            hours=randint(0, 23),
            minutes=randint(0, 59)
        )

        session_data = {
            "id": session_id,
            "detected_borough": borough,
            "query_count": randint(1, 10),
            "created_at": created_at.isoformat(),
            "last_activity": created_at.isoformat(),
        }

        try:
            client.table("chat_sessions").insert(session_data).execute()
            sessions_created += 1
            if verbose:
                print(f"  - Session {session_id[:8]}...")
        except Exception as e:
            if verbose:
                print(f"  - Error: {e}")

    print(f"  Created {sessions_created} sessions")
    return sessions_created


async def seed_sample_queries(client, count: int = 100, verbose: bool = False):
    """Seed sample query analytics."""
    print(f"Seeding {count} sample queries...")

    # Get existing sessions
    sessions_result = client.table("chat_sessions").select("id").execute()
    session_ids = [s["id"] for s in (sessions_result.data or [])]

    if not session_ids:
        print("  No sessions found, creating some first...")
        await seed_sample_sessions(client, 20)
        sessions_result = client.table("chat_sessions").select("id").execute()
        session_ids = [s["id"] for s in (sessions_result.data or [])]

    queries_created = 0
    for i in range(count):
        query_data = {
            "id": str(uuid.uuid4()),
            "session_id": choice(session_ids),
            "query_text": choice(SAMPLE_QUERIES),
            "detected_borough": choice(BOROUGHS)["name"],
            "detected_topic": choice(TOPICS)["name"],
            "response_length": randint(200, 2000),
            "citations_count": randint(0, 5),
            "processing_time_ms": randint(500, 3000),
            "user_feedback": choice([None, None, None, "positive", "negative"]),
            "is_follow_up": choice([True, False, False]),
            "created_at": (datetime.utcnow() - timedelta(
                days=randint(0, 30),
                hours=randint(0, 23)
            )).isoformat(),
        }

        try:
            client.table("query_analytics").insert(query_data).execute()
            queries_created += 1
            if verbose and queries_created % 10 == 0:
                print(f"  - Created {queries_created} queries...")
        except Exception as e:
            if verbose:
                print(f"  - Error: {e}")

    print(f"  Created {queries_created} queries")


async def seed_sample_leads(client, count: int = 20, verbose: bool = False):
    """Seed sample leads."""
    print(f"Seeding {count} sample leads...")

    leads_created = 0
    for i in range(count):
        name = choice(SAMPLE_NAMES)
        email_name = name.lower().replace(" ", ".")

        lead_data = {
            "id": str(uuid.uuid4()),
            "email": f"{email_name}+test{i}@example.com",
            "name": name,
            "phone": f"+44 7{randint(100, 999)} {randint(100, 999)} {randint(1000, 9999)}" if choice([True, False]) else None,
            "postcode": f"N{randint(1, 22)} {randint(1, 9)}{choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}",
            "borough": choice(BOROUGHS)["name"],
            "project_type": choice(PROJECT_TYPES),
            "status": choice(["new", "new", "contacted", "qualified", "converted"]),
            "query_count": randint(1, 15),
            "source": choice(["chat_widget", "chat_widget", "api", "manual"]),
            "marketing_consent": choice([True, False]),
            "created_at": (datetime.utcnow() - timedelta(
                days=randint(0, 60)
            )).isoformat(),
        }

        try:
            client.table("leads").insert(lead_data).execute()
            leads_created += 1
            if verbose:
                print(f"  - {lead_data['email']}")
        except Exception as e:
            if verbose:
                print(f"  - Error: {e}")

    print(f"  Created {leads_created} leads")


async def seed_daily_analytics(client, days: int = 30, verbose: bool = False):
    """Seed daily aggregated analytics."""
    print(f"Seeding {days} days of daily analytics...")

    records_created = 0
    for day_offset in range(days):
        date = (datetime.utcnow() - timedelta(days=day_offset)).date()

        for borough in BOROUGHS:
            record = {
                "date": date.isoformat(),
                "borough": borough["name"],
                "total_queries": randint(10, 100),
                "unique_sessions": randint(5, 50),
                "new_leads": randint(0, 5),
                "avg_response_time": uniform(800, 2500),
                "positive_feedback": randint(0, 20),
                "negative_feedback": randint(0, 5),
            }

            try:
                client.table("analytics_daily").upsert(
                    record,
                    on_conflict="date,borough"
                ).execute()
                records_created += 1
            except Exception as e:
                if verbose:
                    print(f"  - Error for {date}/{borough['name']}: {e}")

    print(f"  Created {records_created} daily records")


async def clear_data(client, tables: list = None):
    """Clear existing data from specified tables."""
    all_tables = [
        "query_analytics",
        "analytics_daily",
        "leads",
        "chat_sessions",
    ]

    tables = tables or all_tables

    print("Clearing existing data...")
    for table in tables:
        try:
            # Delete all records (using a filter that matches all)
            client.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print(f"  - Cleared {table}")
        except Exception as e:
            print(f"  - Error clearing {table}: {e}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed database with sample data")
    parser.add_argument(
        "--type",
        choices=["all", "boroughs", "topics", "sessions", "queries", "leads", "daily"],
        default="all",
        help="Type of data to seed (default: all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of records to create (where applicable)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print("=" * 50)
    print("Database Seeder")
    print("=" * 50)

    try:
        client = await get_supabase_client()
        print("Connected to Supabase\n")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        sys.exit(1)

    if args.clear:
        await clear_data(client)
        print()

    if args.type in ["all", "boroughs"]:
        await seed_boroughs(client, args.verbose)

    if args.type in ["all", "topics"]:
        await seed_topics(client, args.verbose)

    if args.type in ["all", "sessions"]:
        await seed_sample_sessions(client, args.count, args.verbose)

    if args.type in ["all", "queries"]:
        await seed_sample_queries(client, args.count * 2, args.verbose)

    if args.type in ["all", "leads"]:
        await seed_sample_leads(client, args.count // 2, args.verbose)

    if args.type in ["all", "daily"]:
        await seed_daily_analytics(client, 30, args.verbose)

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
