#!/usr/bin/env python3
"""
Cache cleanup utility for the Planning Intelligence Agent.
Clears Redis cache and optionally other cached data.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def clear_redis_cache(pattern: str = "*", verbose: bool = False):
    """Clear Redis cache entries matching the pattern."""
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        print("Redis not configured (REDIS_URL not set)")
        return 0

    try:
        import redis.asyncio as redis

        client = redis.from_url(redis_url, decode_responses=True)

        # Test connection
        await client.ping()
        print(f"Connected to Redis at {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")

        # Find keys matching pattern
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)

        if not keys:
            print(f"No keys found matching pattern: {pattern}")
            await client.close()
            return 0

        if verbose:
            print(f"\nKeys to delete ({len(keys)}):")
            for key in keys[:20]:  # Show first 20
                print(f"  - {key}")
            if len(keys) > 20:
                print(f"  ... and {len(keys) - 20} more")

        # Delete keys
        deleted = await client.delete(*keys)
        print(f"\nDeleted {deleted} cache entries")

        await client.close()
        return deleted

    except ImportError:
        print("Redis package not installed. Run: pip install redis")
        return 0
    except Exception as e:
        print(f"Redis error: {e}")
        return 0


async def clear_session_cache(verbose: bool = False):
    """Clear session-specific cache entries."""
    print("\nClearing session cache...")
    return await clear_redis_cache("session:*", verbose)


async def clear_rate_limit_cache(verbose: bool = False):
    """Clear rate limit entries."""
    print("\nClearing rate limit cache...")
    return await clear_redis_cache("ratelimit:*", verbose)


async def clear_query_cache(verbose: bool = False):
    """Clear query/response cache entries."""
    print("\nClearing query cache...")
    return await clear_redis_cache("query:*", verbose)


async def clear_embedding_cache(verbose: bool = False):
    """Clear embedding cache entries."""
    print("\nClearing embedding cache...")
    return await clear_redis_cache("embedding:*", verbose)


async def clear_temp_files(temp_dir: str = None, verbose: bool = False):
    """Clear temporary files."""
    if temp_dir is None:
        temp_dir = Path(__file__).parent.parent / "backend" / "temp"

    temp_path = Path(temp_dir)

    if not temp_path.exists():
        print(f"Temp directory does not exist: {temp_path}")
        return 0

    print(f"\nClearing temporary files from {temp_path}...")

    deleted = 0
    for file in temp_path.glob("*"):
        if file.is_file():
            try:
                if verbose:
                    print(f"  Deleting: {file.name}")
                file.unlink()
                deleted += 1
            except Exception as e:
                print(f"  Error deleting {file.name}: {e}")

    print(f"Deleted {deleted} temporary files")
    return deleted


async def show_cache_stats():
    """Show current cache statistics."""
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        print("Redis not configured")
        return

    try:
        import redis.asyncio as redis

        client = redis.from_url(redis_url, decode_responses=True)
        await client.ping()

        # Get info
        info = await client.info("memory")
        keyspace = await client.info("keyspace")

        print("\n" + "=" * 40)
        print("Cache Statistics")
        print("=" * 40)
        print(f"Used memory: {info.get('used_memory_human', 'N/A')}")
        print(f"Peak memory: {info.get('used_memory_peak_human', 'N/A')}")

        # Count keys by pattern
        patterns = {
            "session:*": "Sessions",
            "ratelimit:*": "Rate limits",
            "query:*": "Queries",
            "embedding:*": "Embeddings",
        }

        print("\nKey counts:")
        for pattern, name in patterns.items():
            count = 0
            async for _ in client.scan_iter(match=pattern):
                count += 1
            print(f"  {name}: {count}")

        # Total keys
        db_info = keyspace.get("db0", {})
        if isinstance(db_info, dict):
            total_keys = db_info.get("keys", 0)
        else:
            total_keys = "N/A"
        print(f"\nTotal keys: {total_keys}")

        await client.close()

    except ImportError:
        print("Redis package not installed")
    except Exception as e:
        print(f"Error getting stats: {e}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cache cleanup utility")
    parser.add_argument(
        "action",
        choices=["all", "sessions", "ratelimit", "queries", "embeddings", "temp", "stats"],
        nargs="?",
        default="stats",
        help="What to clear (default: show stats)",
    )
    parser.add_argument(
        "--pattern",
        default=None,
        help="Custom Redis key pattern to clear",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompts",
    )

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print("=" * 50)
    print("Cache Cleanup Utility")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if args.action == "stats":
        await show_cache_stats()
        return

    # Confirm before clearing
    if not args.force:
        if args.action == "all":
            msg = "This will clear ALL cached data. Continue?"
        else:
            msg = f"This will clear {args.action} cache. Continue?"

        response = input(f"\n{msg} [y/N]: ")
        if response.lower() != "y":
            print("Cancelled.")
            return

    total_deleted = 0

    if args.pattern:
        # Custom pattern
        deleted = await clear_redis_cache(args.pattern, args.verbose)
        total_deleted += deleted

    elif args.action == "all":
        # Clear everything
        total_deleted += await clear_session_cache(args.verbose)
        total_deleted += await clear_rate_limit_cache(args.verbose)
        total_deleted += await clear_query_cache(args.verbose)
        total_deleted += await clear_embedding_cache(args.verbose)
        total_deleted += await clear_temp_files(verbose=args.verbose)

    elif args.action == "sessions":
        total_deleted = await clear_session_cache(args.verbose)

    elif args.action == "ratelimit":
        total_deleted = await clear_rate_limit_cache(args.verbose)

    elif args.action == "queries":
        total_deleted = await clear_query_cache(args.verbose)

    elif args.action == "embeddings":
        total_deleted = await clear_embedding_cache(args.verbose)

    elif args.action == "temp":
        total_deleted = await clear_temp_files(verbose=args.verbose)

    print("\n" + "=" * 50)
    print(f"Total items cleared: {total_deleted}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
