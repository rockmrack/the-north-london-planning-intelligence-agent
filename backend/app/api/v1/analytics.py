"""
Analytics API endpoints.
Provides real-time and aggregated analytics from the database.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_required_token
from app.services.analytics import analytics_service

router = APIRouter()


@router.get(
    "/summary",
    dependencies=[Depends(get_required_token)],
)
async def get_analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get comprehensive analytics summary for the specified period.

    Requires authentication. Returns aggregated metrics about:
    - Query volume and patterns
    - User engagement
    - Lead conversion
    - Popular topics and boroughs

    **Query Parameters:**
    - `days`: Number of days to include (default: 30)
    """
    try:
        summary = await analytics_service.get_summary(days=days)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get(
    "/queries",
    dependencies=[Depends(get_required_token)],
)
async def get_query_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    borough: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
):
    """
    Get detailed query analytics.

    Requires authentication. Returns individual query records
    with filters for date range, borough, and topic.
    """
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    try:
        from app.services.supabase import supabase_service

        client = await supabase_service._get_client()

        query = client.table("query_analytics").select(
            "id, session_id, query_text, detected_borough, detected_topic, "
            "response_length, citations_count, processing_time_ms, "
            "user_feedback, created_at"
        ).gte(
            "created_at", start_date.isoformat()
        ).lte(
            "created_at", end_date.isoformat()
        ).order("created_at", desc=True)

        if borough:
            query = query.eq("detected_borough", borough)
        if topic:
            query = query.eq("detected_topic", topic)

        query = query.range(offset, offset + limit - 1)
        result = await query.execute()

        count_query = client.table("query_analytics").select(
            "id", count="exact"
        ).gte(
            "created_at", start_date.isoformat()
        ).lte(
            "created_at", end_date.isoformat()
        )

        if borough:
            count_query = count_query.eq("detected_borough", borough)
        if topic:
            count_query = count_query.eq("detected_topic", topic)

        count_result = await count_query.execute()

        return {
            "queries": result.data or [],
            "total": count_result.count or 0,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve query analytics: {str(e)}"
        )


@router.get("/trending")
async def get_trending_topics(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=5, ge=1, le=20),
):
    """
    Get trending planning topics.

    Returns the most popular query topics over the specified period.
    Public endpoint for display on the website.
    """
    try:
        topics = await analytics_service.get_trending_topics(days=days, limit=limit)

        return {
            "trending": [
                {"topic": t["topic"], "query_count": t["count"]}
                for t in topics
            ],
            "period": f"last_{days}_days",
        }
    except Exception:
        return {
            "trending": [],
            "period": f"last_{days}_days",
        }


@router.get(
    "/performance",
    dependencies=[Depends(get_required_token)],
)
async def get_performance_metrics(
    days: int = Query(default=7, ge=1, le=30),
):
    """
    Get system performance metrics.

    Requires authentication. Returns:
    - Average response times
    - Percentile response times (p50, p95, p99)
    - Total requests
    """
    try:
        metrics = await analytics_service.get_performance_metrics(days=days)
        return {**metrics, "period_days": days}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get(
    "/documents/usage",
    dependencies=[Depends(get_required_token)],
)
async def get_document_usage():
    """
    Get document usage statistics.

    Returns which documents are most frequently cited
    and statistics by borough.
    """
    try:
        usage = await analytics_service.get_document_usage()
        return usage
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document usage: {str(e)}"
        )


@router.get(
    "/conversion",
    dependencies=[Depends(get_required_token)],
)
async def get_conversion_metrics(
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get lead conversion metrics.

    Returns funnel metrics from chat session to lead capture.
    """
    try:
        metrics = await analytics_service.get_conversion_metrics(days=days)
        return {**metrics, "period_days": days}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversion metrics: {str(e)}"
        )


@router.get(
    "/daily",
    dependencies=[Depends(get_required_token)],
)
async def get_daily_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    borough: Optional[str] = None,
):
    """
    Get daily aggregated analytics.

    Returns pre-computed daily metrics for charts and reports.
    """
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    try:
        from app.services.supabase import supabase_service

        client = await supabase_service._get_client()

        query = client.table("analytics_daily").select("*").gte(
            "date", start_date.date().isoformat()
        ).lte(
            "date", end_date.date().isoformat()
        ).order("date")

        if borough:
            query = query.eq("borough", borough)

        result = await query.execute()

        return {
            "daily": result.data or [],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve daily analytics: {str(e)}"
        )


@router.post(
    "/aggregate",
    dependencies=[Depends(get_required_token)],
)
async def trigger_aggregation(
    date: Optional[datetime] = None,
):
    """
    Trigger daily analytics aggregation.

    Admin endpoint to manually run the daily aggregation.
    If no date is provided, aggregates for yesterday.
    """
    if not date:
        date = datetime.utcnow() - timedelta(days=1)

    try:
        from app.services.supabase import supabase_service

        client = await supabase_service._get_client()

        await client.rpc(
            "aggregate_daily_analytics",
            {"p_date": date.date().isoformat()}
        ).execute()

        return {
            "success": True,
            "message": f"Aggregation triggered for {date.date().isoformat()}",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger aggregation: {str(e)}"
        )
