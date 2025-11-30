"""
Lead capture API endpoints.
For capturing and managing leads from the chat interface.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_required_token
from app.core.config import settings
from app.models.leads import LeadCreate, LeadResponse
from app.services.cache import cache_service
from app.services.supabase import supabase_service

router = APIRouter()


@router.post(
    "/capture",
    response_model=LeadResponse,
)
async def capture_lead(
    lead: LeadCreate,
) -> LeadResponse:
    """
    Capture a lead from the chat interface.

    Called when a user provides their email to continue the conversation
    or to receive a detailed report.

    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "name": "John Smith",
        "postcode": "NW3 1AB",
        "project_type": "extension",
        "session_id": "session_abc123"
    }
    ```
    """
    try:
        # Check if lead already exists
        existing = await supabase_service.get_lead_by_email(lead.email)

        if existing:
            # Update existing lead
            update_data = {
                "last_activity": datetime.utcnow().isoformat(),
                "query_count": existing.get("query_count", 0) + 1,
            }

            # Add new session queries if provided
            if lead.session_id:
                session = await supabase_service.get_session(lead.session_id)
                if session:
                    queries = existing.get("queries", [])
                    for msg in session.get("messages", []):
                        if msg.get("role") == "user":
                            queries.append(msg.get("content"))
                    update_data["queries"] = queries[-20:]  # Keep last 20

            await supabase_service.update_lead(existing["id"], update_data)

            # Link session to lead
            if lead.session_id:
                await supabase_service.update_session(
                    lead.session_id,
                    {"lead_id": existing["id"]},
                )
                await cache_service.set_session(
                    lead.session_id,
                    {"lead_id": existing["id"]},
                )

            remaining = max(0, settings.free_queries_limit - update_data["query_count"])

            # Send notification for returning user
            await _notify_lead_activity(existing["id"], "returning_user")

            return LeadResponse(
                success=True,
                lead_id=existing["id"],
                message="Welcome back! You can continue your planning queries.",
                remaining_free_queries=remaining,
            )

        # Create new lead
        lead_id = str(uuid.uuid4())
        lead_data = {
            "id": lead_id,
            "email": lead.email,
            "name": lead.name,
            "phone": lead.phone,
            "postcode": lead.postcode,
            "address": lead.address,
            "borough": lead.borough,
            "property_type": lead.property_type.value if lead.property_type else None,
            "project_type": lead.project_type.value if lead.project_type else None,
            "project_description": lead.project_description,
            "budget_range": lead.budget_range,
            "timeline": lead.timeline,
            "source": lead.source.value if lead.source else "chat_widget",
            "status": "new",
            "query_count": 0,
            "queries": [],
            "marketing_consent": lead.marketing_consent,
            "utm_source": lead.utm_source,
            "utm_medium": lead.utm_medium,
            "utm_campaign": lead.utm_campaign,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }

        # Get queries from session
        if lead.session_id:
            session = await supabase_service.get_session(lead.session_id)
            if session:
                queries = []
                for msg in session.get("messages", []):
                    if msg.get("role") == "user":
                        queries.append(msg.get("content"))
                lead_data["queries"] = queries
                lead_data["query_count"] = len(queries)

        await supabase_service.create_lead(lead_data)

        # Link session to lead
        if lead.session_id:
            await supabase_service.update_session(
                lead.session_id,
                {"lead_id": lead_id},
            )

        # Send notification for new lead
        await _notify_lead_activity(lead_id, "new_lead", lead_data)

        return LeadResponse(
            success=True,
            lead_id=lead_id,
            message="Thank you! You can now continue your planning queries.",
            remaining_free_queries=settings.free_queries_limit,
        )

    except Exception as e:
        return LeadResponse(
            success=False,
            lead_id=None,
            message="Failed to save your information. Please try again.",
        )


@router.get(
    "/",
    dependencies=[Depends(get_required_token)],
)
async def list_leads(
    status_filter: Optional[str] = Query(None, alias="status"),
    borough: Optional[str] = None,
    source: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """
    List all leads (admin only).

    Requires authentication. Supports filtering by status, borough, source, date range.
    """
    try:
        client = await supabase_service._get_client()

        query = client.table("leads").select(
            "id, email, name, phone, postcode, borough, project_type, "
            "status, query_count, source, created_at, last_activity"
        ).order("created_at", desc=True)

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)
        if borough:
            query = query.eq("borough", borough)
        if source:
            query = query.eq("source", source)
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        if search:
            query = query.or_(f"email.ilike.%{search}%,name.ilike.%{search}%")

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        result = await query.execute()

        # Get total count
        count_query = client.table("leads").select("id", count="exact")
        if status_filter:
            count_query = count_query.eq("status", status_filter)
        if borough:
            count_query = count_query.eq("borough", borough)
        if source:
            count_query = count_query.eq("source", source)

        count_result = await count_query.execute()

        return {
            "leads": result.data or [],
            "total": count_result.count or 0,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve leads: {str(e)}"
        )


@router.get(
    "/stats",
    dependencies=[Depends(get_required_token)],
)
async def get_lead_stats():
    """
    Get lead statistics summary (admin only).

    Returns counts by status, borough, and source.
    """
    try:
        client = await supabase_service._get_client()

        # Get all leads for aggregation
        result = await client.table("leads").select(
            "status, borough, source"
        ).execute()

        leads = result.data or []

        # Aggregate by status
        by_status = {}
        for lead in leads:
            status = lead.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        # Aggregate by borough
        by_borough = {}
        for lead in leads:
            borough = lead.get("borough") or "Unknown"
            by_borough[borough] = by_borough.get(borough, 0) + 1

        # Aggregate by source
        by_source = {}
        for lead in leads:
            source = lead.get("source") or "unknown"
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total": len(leads),
            "by_status": by_status,
            "by_borough": by_borough,
            "by_source": by_source,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve lead stats: {str(e)}"
        )


@router.get(
    "/{lead_id}",
    dependencies=[Depends(get_required_token)],
)
async def get_lead(
    lead_id: str,
):
    """
    Get a specific lead with full details (admin only).

    Requires authentication.
    """
    try:
        client = await supabase_service._get_client()

        result = await client.table("leads").select("*").eq("id", lead_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        # Get associated sessions
        sessions_result = await client.table("chat_sessions").select(
            "id, query_count, created_at, last_activity"
        ).eq("lead_id", lead_id).execute()

        lead_data = result.data
        lead_data["sessions"] = sessions_result.data or []

        return lead_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve lead: {str(e)}"
        )


@router.patch(
    "/{lead_id}",
    dependencies=[Depends(get_required_token)],
)
async def update_lead(
    lead_id: str,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    assigned_to: Optional[str] = None,
):
    """
    Update a lead (admin only).

    Requires authentication.
    """
    try:
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if status:
            valid_statuses = ["new", "contacted", "qualified", "converted", "lost"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            update_data["status"] = status

            if status == "converted":
                update_data["converted_at"] = datetime.utcnow().isoformat()

        if notes is not None:
            update_data["notes"] = notes
        if assigned_to is not None:
            update_data["assigned_to"] = assigned_to

        await supabase_service.update_lead(lead_id, update_data)

        return {"success": True, "message": "Lead updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update lead: {str(e)}"
        )


@router.delete(
    "/{lead_id}",
    dependencies=[Depends(get_required_token)],
)
async def delete_lead(
    lead_id: str,
):
    """
    Delete a lead (admin only).

    Requires authentication. This is a soft delete - the lead is marked as deleted
    but not removed from the database.
    """
    try:
        client = await supabase_service._get_client()

        # Soft delete by updating status
        await client.table("leads").update({
            "status": "deleted",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", lead_id).execute()

        return {"success": True, "message": "Lead deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete lead: {str(e)}"
        )


@router.post(
    "/check-email",
)
async def check_email(
    email: str,
):
    """
    Check if an email is already registered as a lead.

    Returns the query count and remaining free queries.
    """
    existing = await supabase_service.get_lead_by_email(email)

    if existing:
        query_count = existing.get("query_count", 0)
        remaining = max(0, settings.free_queries_limit - query_count)
        return {
            "exists": True,
            "query_count": query_count,
            "remaining_free_queries": remaining,
        }

    return {
        "exists": False,
        "query_count": 0,
        "remaining_free_queries": settings.free_queries_limit,
    }


@router.post(
    "/{lead_id}/export",
    dependencies=[Depends(get_required_token)],
)
async def export_lead(
    lead_id: str,
    format: str = Query(default="json", enum=["json", "csv"]),
):
    """
    Export a lead's data (admin only).

    Requires authentication. Returns lead data in specified format.
    """
    try:
        client = await supabase_service._get_client()

        result = await client.table("leads").select("*").eq("id", lead_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        if format == "csv":
            # Convert to CSV format
            lead = result.data
            headers = list(lead.keys())
            values = [str(lead.get(h, "")) for h in headers]

            csv_content = ",".join(headers) + "\n" + ",".join(values)
            return {"format": "csv", "content": csv_content}

        return {"format": "json", "content": result.data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export lead: {str(e)}"
        )


async def _notify_lead_activity(
    lead_id: str,
    activity_type: str,
    lead_data: dict = None,
):
    """Send notifications for lead activity."""
    try:
        from app.services.notifications import notification_service

        if activity_type == "new_lead":
            await notification_service.send_new_lead_notification(lead_id, lead_data)
        elif activity_type == "returning_user":
            await notification_service.send_returning_user_notification(lead_id)

    except Exception as e:
        # Don't fail the main operation if notification fails
        import structlog
        logger = structlog.get_logger()
        logger.warning("Failed to send lead notification", error=str(e), lead_id=lead_id)
