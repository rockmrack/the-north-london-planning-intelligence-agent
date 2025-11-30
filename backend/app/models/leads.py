"""Lead capture related Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LeadSource(str, Enum):
    """Source of the lead."""

    CHAT_WIDGET = "chat_widget"
    LANDING_PAGE = "landing_page"
    REPORT_DOWNLOAD = "report_download"
    CONSULTATION_BOOKING = "consultation_booking"
    NEWSLETTER = "newsletter"


class LeadStatus(str, Enum):
    """Status of the lead."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class PropertyType(str, Enum):
    """Type of property."""

    TERRACED = "terraced"
    SEMI_DETACHED = "semi_detached"
    DETACHED = "detached"
    FLAT = "flat"
    MAISONETTE = "maisonette"
    OTHER = "other"


class ProjectType(str, Enum):
    """Type of project the lead is interested in."""

    EXTENSION = "extension"
    LOFT_CONVERSION = "loft_conversion"
    BASEMENT = "basement"
    RENOVATION = "renovation"
    NEW_BUILD = "new_build"
    CHANGE_OF_USE = "change_of_use"
    OTHER = "other"


class LeadCreate(BaseModel):
    """Request body for creating a lead."""

    email: EmailStr = Field(..., description="Lead's email address")
    name: Optional[str] = Field(None, max_length=100, description="Lead's name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    postcode: Optional[str] = Field(None, max_length=10, description="Property postcode")
    address: Optional[str] = Field(None, max_length=200, description="Property address")
    borough: Optional[str] = Field(None, description="Borough")
    property_type: Optional[PropertyType] = Field(None, description="Type of property")
    project_type: Optional[ProjectType] = Field(None, description="Type of project")
    project_description: Optional[str] = Field(
        None, max_length=1000, description="Description of the project"
    )
    budget_range: Optional[str] = Field(None, description="Budget range")
    timeline: Optional[str] = Field(None, description="Project timeline")
    source: LeadSource = Field(
        LeadSource.CHAT_WIDGET, description="Source of the lead"
    )
    session_id: Optional[str] = Field(None, description="Chat session ID")
    marketing_consent: bool = Field(
        False, description="Whether they consented to marketing"
    )
    utm_source: Optional[str] = Field(None, description="UTM source")
    utm_medium: Optional[str] = Field(None, description="UTM medium")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign")


class Lead(LeadCreate):
    """Full lead model with database fields."""

    id: str = Field(..., description="Unique lead ID")
    status: LeadStatus = Field(LeadStatus.NEW, description="Lead status")
    query_count: int = Field(0, description="Number of queries made")
    queries: List[str] = Field(
        default_factory=list, description="Questions asked in chat"
    )
    notes: Optional[str] = Field(None, description="Internal notes")
    assigned_to: Optional[str] = Field(None, description="Assigned team member")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the lead was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the lead was last updated",
    )
    last_activity: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity from the lead",
    )
    converted_at: Optional[datetime] = Field(
        None, description="When the lead was converted"
    )


class LeadResponse(BaseModel):
    """Response for lead operations."""

    success: bool = Field(..., description="Whether the operation succeeded")
    lead_id: Optional[str] = Field(None, description="Lead ID")
    message: str = Field(..., description="Response message")
    remaining_free_queries: Optional[int] = Field(
        None, description="Remaining free queries"
    )
