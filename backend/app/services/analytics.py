"""
Analytics service for the Planning Intelligence Agent.
Provides real-time and aggregated analytics from the database.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import structlog

from app.core.config import settings
from app.services.supabase import supabase_service

logger = structlog.get_logger()


class AnalyticsService:
    """
    Service for computing and retrieving analytics data.

    Provides methods for:
    - Query volume and patterns
    - User engagement metrics
    - Lead conversion tracking
    - Document usage statistics
    - Performance metrics
    """

    async def get_summary(
        self,
        days: int = 30,
    ) -> Dict:
        """
        Get comprehensive analytics summary for the specified period.
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        try:
            # Get query analytics
            query_stats = await self._get_query_stats(period_start, period_end)

            # Get session stats
            session_stats = await self._get_session_stats(period_start, period_end)

            # Get lead stats
            lead_stats = await self._get_lead_stats(period_start, period_end)

            # Get borough breakdown
            borough_stats = await self._get_borough_stats(period_start, period_end)

            # Get topic breakdown
            topic_stats = await self._get_topic_stats(period_start, period_end)

            # Get time series
            time_series = await self._get_queries_over_time(period_start, period_end)

            # Get top queries
            top_queries = await self._get_top_queries(period_start, period_end, limit=10)

            # Get most cited documents
            most_cited = await self._get_most_cited_documents(period_start, period_end, limit=10)

            # Calculate rates
            total_queries = query_stats.get("total", 0)
            unique_sessions = session_stats.get("unique", 0)
            leads_captured = lead_stats.get("total", 0)

            positive_feedback = query_stats.get("positive_feedback", 0)
            negative_feedback = query_stats.get("negative_feedback", 0)
            total_feedback = positive_feedback + negative_feedback

            return {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "total_queries": total_queries,
                "unique_sessions": unique_sessions,
                "avg_queries_per_session": (
                    total_queries / unique_sessions if unique_sessions > 0 else 0
                ),
                "avg_processing_time_ms": query_stats.get("avg_processing_time", 0),
                "positive_feedback_rate": (
                    positive_feedback / total_feedback if total_feedback > 0 else 0
                ),
                "negative_feedback_rate": (
                    negative_feedback / total_feedback if total_feedback > 0 else 0
                ),
                "no_feedback_rate": (
                    (total_queries - total_feedback) / total_queries
                    if total_queries > 0 else 1.0
                ),
                "leads_captured": leads_captured,
                "lead_conversion_rate": (
                    leads_captured / unique_sessions if unique_sessions > 0 else 0
                ),
                "queries_by_borough": borough_stats,
                "queries_by_topic": topic_stats,
                "queries_over_time": time_series,
                "top_queries": top_queries,
                "most_cited_documents": most_cited,
            }

        except Exception as e:
            logger.error("Failed to get analytics summary", error=str(e))
            raise

    async def _get_query_stats(
        self,
        start: datetime,
        end: datetime,
    ) -> Dict:
        """Get basic query statistics."""
        try:
            client = await supabase_service._get_client()

            # Get total queries and avg processing time
            result = await client.rpc(
                "get_query_stats",
                {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                }
            ).execute()

            if result.data:
                return result.data[0] if isinstance(result.data, list) else result.data

            # Fallback: direct query
            result = await client.table("query_analytics").select(
                "id",
                count="exact"
            ).gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).execute()

            return {
                "total": result.count or 0,
                "avg_processing_time": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
            }

        except Exception as e:
            logger.warning("Failed to get query stats", error=str(e))
            return {
                "total": 0,
                "avg_processing_time": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
            }

    async def _get_session_stats(
        self,
        start: datetime,
        end: datetime,
    ) -> Dict:
        """Get session statistics."""
        try:
            client = await supabase_service._get_client()

            result = await client.table("chat_sessions").select(
                "id",
                count="exact"
            ).gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).execute()

            return {
                "unique": result.count or 0,
            }

        except Exception as e:
            logger.warning("Failed to get session stats", error=str(e))
            return {"unique": 0}

    async def _get_lead_stats(
        self,
        start: datetime,
        end: datetime,
    ) -> Dict:
        """Get lead capture statistics."""
        try:
            client = await supabase_service._get_client()

            result = await client.table("leads").select(
                "id, status",
                count="exact"
            ).gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).execute()

            # Count by status
            status_counts = {}
            for lead in (result.data or []):
                status = lead.get("status", "new")
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                "total": result.count or 0,
                "by_status": status_counts,
            }

        except Exception as e:
            logger.warning("Failed to get lead stats", error=str(e))
            return {"total": 0, "by_status": {}}

    async def _get_borough_stats(
        self,
        start: datetime,
        end: datetime,
    ) -> List[Dict]:
        """Get query breakdown by borough."""
        try:
            client = await supabase_service._get_client()

            result = await client.table("query_analytics").select(
                "detected_borough"
            ).gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).not_.is_("detected_borough", "null").execute()

            # Count by borough
            borough_counts = {}
            total = 0
            for row in (result.data or []):
                borough = row.get("detected_borough")
                if borough:
                    borough_counts[borough] = borough_counts.get(borough, 0) + 1
                    total += 1

            # Convert to list with percentages
            return [
                {
                    "borough": borough,
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0,
                }
                for borough, count in sorted(
                    borough_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

        except Exception as e:
            logger.warning("Failed to get borough stats", error=str(e))
            return []

    async def _get_topic_stats(
        self,
        start: datetime,
        end: datetime,
    ) -> List[Dict]:
        """Get query breakdown by topic."""
        try:
            client = await supabase_service._get_client()

            result = await client.table("query_analytics").select(
                "detected_topic"
            ).gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).not_.is_("detected_topic", "null").execute()

            # Count by topic
            topic_counts = {}
            total = 0
            for row in (result.data or []):
                topic = row.get("detected_topic")
                if topic:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    total += 1

            # Convert to list with percentages
            return [
                {
                    "topic": topic,
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0,
                }
                for topic, count in sorted(
                    topic_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

        except Exception as e:
            logger.warning("Failed to get topic stats", error=str(e))
            return []

    async def _get_queries_over_time(
        self,
        start: datetime,
        end: datetime,
    ) -> List[Dict]:
        """Get queries aggregated by day."""
        try:
            client = await supabase_service._get_client()

            # Use the pre-aggregated analytics_daily table if available
            result = await client.table("analytics_daily").select(
                "date, total_queries"
            ).gte(
                "date", start.date().isoformat()
            ).lte(
                "date", end.date().isoformat()
            ).order("date").execute()

            if result.data:
                return [
                    {"date": row["date"], "count": row["total_queries"]}
                    for row in result.data
                ]

            return []

        except Exception as e:
            logger.warning("Failed to get queries over time", error=str(e))
            return []

    async def _get_top_queries(
        self,
        start: datetime,
        end: datetime,
        limit: int = 10,
    ) -> List[Dict]:
        """Get most common query patterns."""
        try:
            client = await supabase_service._get_client()

            result = await client.table("query_analytics").select(
                "query_text, detected_topic, detected_borough"
            ).gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).limit(500).execute()

            # Simple word frequency analysis
            query_counts = {}
            for row in (result.data or []):
                query = row.get("query_text", "")[:100]  # Truncate
                query_counts[query] = query_counts.get(query, 0) + 1

            # Get top queries
            top = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

            return [
                {"query": query, "count": count}
                for query, count in top
            ]

        except Exception as e:
            logger.warning("Failed to get top queries", error=str(e))
            return []

    async def _get_most_cited_documents(
        self,
        start: datetime,
        end: datetime,
        limit: int = 10,
    ) -> List[Dict]:
        """Get most frequently cited documents."""
        try:
            client = await supabase_service._get_client()

            # Get document stats from materialized view
            result = await client.table("document_stats").select(
                "borough, category, document_count, total_chunks"
            ).execute()

            return [
                {
                    "borough": row["borough"],
                    "category": row["category"],
                    "document_count": row["document_count"],
                    "chunk_count": row["total_chunks"],
                }
                for row in (result.data or [])[:limit]
            ]

        except Exception as e:
            logger.warning("Failed to get most cited documents", error=str(e))
            return []

    async def get_trending_topics(
        self,
        days: int = 7,
        limit: int = 5,
    ) -> List[Dict]:
        """Get trending topics over the specified period."""
        period_start = datetime.utcnow() - timedelta(days=days)

        try:
            topic_stats = await self._get_topic_stats(period_start, datetime.utcnow())
            return topic_stats[:limit]
        except Exception as e:
            logger.warning("Failed to get trending topics", error=str(e))
            return []

    async def get_performance_metrics(
        self,
        days: int = 7,
    ) -> Dict:
        """Get system performance metrics."""
        period_start = datetime.utcnow() - timedelta(days=days)

        try:
            client = await supabase_service._get_client()

            result = await client.table("query_analytics").select(
                "processing_time_ms"
            ).gte(
                "created_at", period_start.isoformat()
            ).not_.is_("processing_time_ms", "null").execute()

            times = [r["processing_time_ms"] for r in (result.data or []) if r.get("processing_time_ms")]

            if not times:
                return {
                    "avg_response_time_ms": 0,
                    "p50_response_time_ms": 0,
                    "p95_response_time_ms": 0,
                    "p99_response_time_ms": 0,
                    "total_requests": 0,
                }

            times.sort()
            total = len(times)

            return {
                "avg_response_time_ms": sum(times) / total,
                "p50_response_time_ms": times[int(total * 0.5)],
                "p95_response_time_ms": times[int(total * 0.95)] if total >= 20 else times[-1],
                "p99_response_time_ms": times[int(total * 0.99)] if total >= 100 else times[-1],
                "total_requests": total,
            }

        except Exception as e:
            logger.warning("Failed to get performance metrics", error=str(e))
            return {
                "avg_response_time_ms": 0,
                "p50_response_time_ms": 0,
                "p95_response_time_ms": 0,
                "p99_response_time_ms": 0,
                "total_requests": 0,
            }

    async def get_conversion_metrics(
        self,
        days: int = 30,
    ) -> Dict:
        """Get lead conversion funnel metrics."""
        period_start = datetime.utcnow() - timedelta(days=days)

        try:
            session_stats = await self._get_session_stats(period_start, datetime.utcnow())
            lead_stats = await self._get_lead_stats(period_start, datetime.utcnow())
            query_stats = await self._get_query_stats(period_start, datetime.utcnow())

            total_sessions = session_stats.get("unique", 0)
            leads_captured = lead_stats.get("total", 0)
            total_queries = query_stats.get("total", 0)

            return {
                "total_sessions": total_sessions,
                "sessions_with_queries": total_sessions,  # Approximate
                "total_queries": total_queries,
                "leads_captured": leads_captured,
                "conversion_rate": (
                    leads_captured / total_sessions if total_sessions > 0 else 0
                ),
                "avg_queries_per_lead": (
                    total_queries / leads_captured if leads_captured > 0 else 0
                ),
            }

        except Exception as e:
            logger.warning("Failed to get conversion metrics", error=str(e))
            return {
                "total_sessions": 0,
                "sessions_with_queries": 0,
                "total_queries": 0,
                "leads_captured": 0,
                "conversion_rate": 0,
                "avg_queries_per_lead": 0,
            }

    async def get_document_usage(self) -> Dict:
        """Get document usage statistics."""
        try:
            client = await supabase_service._get_client()

            # Get document stats
            result = await client.table("document_stats").select("*").execute()

            stats = result.data or []

            # Sort by usage
            most_cited = sorted(stats, key=lambda x: x.get("total_chunks", 0), reverse=True)

            return {
                "most_cited": most_cited[:10],
                "by_borough": {
                    row["borough"]: row["document_count"]
                    for row in stats
                },
                "total_documents": sum(row.get("document_count", 0) for row in stats),
                "total_chunks": sum(row.get("total_chunks", 0) for row in stats),
            }

        except Exception as e:
            logger.warning("Failed to get document usage", error=str(e))
            return {
                "most_cited": [],
                "by_borough": {},
                "total_documents": 0,
                "total_chunks": 0,
            }


# Global instance
analytics_service = AnalyticsService()
