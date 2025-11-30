#!/usr/bin/env python3
"""
Health check script for the Planning Intelligence Agent.
Verifies all services are running and properly configured.
"""

import asyncio
import sys
from datetime import datetime

import httpx


async def check_backend_health(base_url: str = "http://localhost:8000") -> dict:
    """Check backend API health."""
    result = {
        "service": "Backend API",
        "status": "unknown",
        "details": {},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check root endpoint
            response = await client.get(f"{base_url}/")
            result["details"]["root"] = response.status_code == 200

            # Check health endpoint
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                result["details"]["health"] = health_data
                result["status"] = health_data.get("status", "unknown")
            else:
                result["status"] = "unhealthy"
                result["details"]["error"] = f"Health endpoint returned {response.status_code}"

    except httpx.ConnectError:
        result["status"] = "offline"
        result["details"]["error"] = "Cannot connect to backend"
    except Exception as e:
        result["status"] = "error"
        result["details"]["error"] = str(e)

    return result


async def check_frontend_health(base_url: str = "http://localhost:3000") -> dict:
    """Check frontend health."""
    result = {
        "service": "Frontend",
        "status": "unknown",
        "details": {},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(base_url)
            if response.status_code == 200:
                result["status"] = "healthy"
            else:
                result["status"] = "unhealthy"
                result["details"]["status_code"] = response.status_code

    except httpx.ConnectError:
        result["status"] = "offline"
        result["details"]["error"] = "Cannot connect to frontend"
    except Exception as e:
        result["status"] = "error"
        result["details"]["error"] = str(e)

    return result


async def check_redis_health(redis_url: str = "redis://localhost:6379") -> dict:
    """Check Redis health."""
    result = {
        "service": "Redis",
        "status": "unknown",
        "details": {},
    }

    try:
        import redis.asyncio as redis

        client = await redis.from_url(redis_url)
        pong = await client.ping()
        if pong:
            result["status"] = "healthy"
            info = await client.info("server")
            result["details"]["version"] = info.get("redis_version", "unknown")
        await client.close()

    except ImportError:
        result["status"] = "skipped"
        result["details"]["error"] = "redis package not installed"
    except Exception as e:
        result["status"] = "offline"
        result["details"]["error"] = str(e)

    return result


async def check_supabase_health() -> dict:
    """Check Supabase connection."""
    result = {
        "service": "Supabase",
        "status": "unknown",
        "details": {},
    }

    try:
        import os

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            result["status"] = "not_configured"
            result["details"]["error"] = "SUPABASE_URL or SUPABASE_ANON_KEY not set"
            return result

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{url}/rest/v1/",
                headers={"apikey": key},
            )
            if response.status_code in [200, 401]:  # 401 is expected without auth
                result["status"] = "healthy"
            else:
                result["status"] = "unhealthy"
                result["details"]["status_code"] = response.status_code

    except Exception as e:
        result["status"] = "error"
        result["details"]["error"] = str(e)

    return result


async def check_openai_health() -> dict:
    """Check OpenAI API connectivity."""
    result = {
        "service": "OpenAI API",
        "status": "unknown",
        "details": {},
    }

    try:
        import os

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            result["status"] = "not_configured"
            result["details"]["error"] = "OPENAI_API_KEY not set"
            return result

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if response.status_code == 200:
                result["status"] = "healthy"
                models = response.json().get("data", [])
                result["details"]["models_available"] = len(models)
            elif response.status_code == 401:
                result["status"] = "auth_error"
                result["details"]["error"] = "Invalid API key"
            else:
                result["status"] = "unhealthy"
                result["details"]["status_code"] = response.status_code

    except Exception as e:
        result["status"] = "error"
        result["details"]["error"] = str(e)

    return result


def print_result(result: dict, verbose: bool = False):
    """Print a health check result."""
    status_icons = {
        "healthy": "✅",
        "unhealthy": "❌",
        "offline": "⚫",
        "error": "⚠️",
        "not_configured": "⚪",
        "skipped": "⏭️",
        "unknown": "❓",
    }

    icon = status_icons.get(result["status"], "❓")
    print(f"{icon} {result['service']}: {result['status']}")

    if verbose and result.get("details"):
        for key, value in result["details"].items():
            print(f"   {key}: {value}")


async def run_health_checks(
    backend_url: str = "http://localhost:8000",
    frontend_url: str = "http://localhost:3000",
    redis_url: str = "redis://localhost:6379",
    verbose: bool = False,
) -> bool:
    """Run all health checks and return overall status."""
    print(f"\n🏥 Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Run all checks concurrently
    results = await asyncio.gather(
        check_backend_health(backend_url),
        check_frontend_health(frontend_url),
        check_redis_health(redis_url),
        check_supabase_health(),
        check_openai_health(),
    )

    # Print results
    all_healthy = True
    for result in results:
        print_result(result, verbose)
        if result["status"] not in ["healthy", "skipped", "not_configured"]:
            all_healthy = False

    print("=" * 50)

    if all_healthy:
        print("✅ All services are healthy!")
    else:
        print("⚠️ Some services need attention")

    return all_healthy


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Health check for Planning Intelligence Agent")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--frontend-url", default="http://localhost:3000", help="Frontend URL")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis URL")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Run health checks
    healthy = asyncio.run(run_health_checks(
        backend_url=args.backend_url,
        frontend_url=args.frontend_url,
        redis_url=args.redis_url,
        verbose=args.verbose,
    ))

    sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
