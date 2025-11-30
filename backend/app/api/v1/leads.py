"""
Lead capture API endpoints.
For capturing and managing leads from the chat interface.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_required_token
from app.core.config import settings
from app.models.leads import Lead, LeadCreate, LeadResponse
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
    status: Optional[str] = None,
    borough: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List all leads (admin only).

    Requires authentication.
    """
    # This would typically query the database with filters
    # For now, return a placeholder
    return {
        "leads": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{lead_id}",
    dependencies=[Depends(get_required_token)],
)
async def get_lead(
    lead_id: str,
):
    """
    Get a specific lead (admin only).

    Requires authentication.
    """
    # This would query the database
    return {"message": "Not implemented"}


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
    update_data = {}
    if status:
        update_data["status"] = status
    if notes:
        update_data["notes"] = notes
    if assigned_to:
        update_data["assigned_to"] = assigned_to

    if update_data:
        await supabase_service.update_lead(lead_id, update_data)

    return {"message": "Lead updated successfully"}


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
