# API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

Most endpoints are public. Admin endpoints require Bearer token authentication.

```
Authorization: Bearer <token>
```

## Rate Limiting

Rate limits are applied per IP address:
- Chat endpoints: 30 requests/hour
- General API: 100 requests/hour
- Document upload: 10 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699900000
Retry-After: 3600  (only on 429 responses)
```

---

## Chat Endpoints

### POST /chat/query

Submit a planning question and get an AI-generated response.

**Request Body:**
```json
{
  "message": "Can I add a rear extension in Hampstead?",
  "session_id": "optional-session-id",
  "borough": "Camden",
  "include_sources": true
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "message": "In Hampstead, rear extensions are subject to...",
  "citations": [
    {
      "document_name": "Camden Planning Guidance",
      "borough": "Camden",
      "section": "4.2 Extensions",
      "page_number": 42,
      "paragraph": "Relevant excerpt...",
      "relevance_score": 0.92,
      "chunk_id": "uuid"
    }
  ],
  "suggested_questions": [
    {"question": "What is the maximum depth for a rear extension?", "category": "extensions"}
  ],
  "detected_borough": "Camden",
  "detected_location": "Hampstead",
  "query_count": 1,
  "requires_email": false,
  "processing_time_ms": 1234.5
}
```

### POST /chat/query/stream

Same as above but returns Server-Sent Events for streaming response.

**Event Types:**
- `message`: Partial response text
- `citation`: Citation data
- `done`: Stream complete

### POST /chat/feedback

Submit feedback for a response.

**Request Body:**
```json
{
  "query_id": "uuid",
  "feedback": "positive",
  "comment": "Very helpful!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback recorded"
}
```

### GET /chat/boroughs

Get list of supported boroughs.

**Response:**
```json
{
  "boroughs": [
    {"name": "Camden", "description": "London Borough of Camden..."},
    {"name": "Barnet", "description": "London Borough of Barnet..."}
  ]
}
```

### GET /chat/topics

Get list of planning topics with examples.

**Response:**
```json
{
  "topics": [
    {
      "name": "extensions",
      "description": "House extensions including rear, side, and loft",
      "example_questions": [
        "Can I build a rear extension without planning permission?",
        "What is the maximum height for a single storey extension?"
      ]
    }
  ]
}
```

---

## Document Endpoints

### POST /documents/ingest

Ingest a document from a file path (requires authentication).

**Request Body:**
```json
{
  "file_path": "/path/to/document.pdf",
  "document_name": "Camden Local Plan 2024",
  "borough": "Camden",
  "category": "local_plan"
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "status": "processing",
  "message": "Document queued for ingestion"
}
```

### POST /documents/ingest/upload

Upload and ingest a document file (requires authentication).

**Multipart Form:**
- `file`: Document file (PDF, DOCX, etc.)
- `document_name`: Name (optional, defaults to filename)
- `borough`: Borough enum (Camden, Barnet, Westminster, Brent, Haringey)
- `category`: Category enum (local_plan, spd, design_guide, etc.)

### GET /documents

List all ingested documents.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| borough | string | Filter by borough |
| category | string | Filter by category |
| is_active | boolean | Active status (default: true) |
| limit | integer | Results per page (default: 50) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "camden-local-plan.pdf",
      "borough": "Camden",
      "document_type": "local_plan",
      "title": "Camden Local Plan 2024",
      "page_count": 250,
      "chunk_count": 1200,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 45,
  "limit": 50,
  "offset": 0
}
```

### GET /documents/{document_id}

Get document details.

### DELETE /documents/{document_id}

Delete a document and its chunks (requires authentication).

### GET /documents/stats/summary

Get document statistics.

**Response:**
```json
{
  "total_documents": 45,
  "total_chunks": 15000,
  "by_borough": {
    "Camden": 12,
    "Barnet": 10
  },
  "by_status": {
    "completed": 40,
    "processing": 3,
    "failed": 2
  }
}
```

---

## Lead Endpoints

### POST /leads/capture

Capture a lead from chat.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Smith",
  "phone": "+44 7123 456789",
  "postcode": "NW3 1AB",
  "project_type": "extension",
  "session_id": "session_abc123",
  "marketing_consent": true
}
```

**Response:**
```json
{
  "success": true,
  "lead_id": "uuid",
  "message": "Thank you for registering",
  "remaining_free_queries": 10
}
```

### POST /leads/check-email

Check if email exists and get query count.

**Query Parameters:**
- `email`: Email address to check

**Response:**
```json
{
  "exists": true,
  "query_count": 5,
  "remaining_free_queries": 5
}
```

### GET /leads (Admin)

List all leads (requires authentication).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (new, contacted, qualified, converted) |
| borough | string | Filter by borough |
| source | string | Filter by source |
| start_date | datetime | Filter by creation date |
| end_date | datetime | Filter by creation date |
| search | string | Search name/email |
| limit | integer | Results per page (default: 50) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "leads": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Smith",
      "phone": "+44 7123 456789",
      "postcode": "NW3 1AB",
      "borough": "Camden",
      "project_type": "extension",
      "status": "new",
      "query_count": 5,
      "source": "chat_widget",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### GET /leads/{lead_id} (Admin)

Get lead details.

### PATCH /leads/{lead_id} (Admin)

Update lead information.

**Request Body:**
```json
{
  "status": "contacted",
  "notes": "Called on Jan 15th"
}
```

### DELETE /leads/{lead_id} (Admin)

Delete a lead.

### GET /leads/stats (Admin)

Get lead statistics.

**Query Parameters:**
- `days`: Number of days to include (default: 30)

**Response:**
```json
{
  "total_leads": 150,
  "new_leads": 45,
  "by_status": {
    "new": 45,
    "contacted": 30,
    "qualified": 15,
    "converted": 10
  },
  "by_borough": {
    "Camden": 50,
    "Barnet": 40
  },
  "by_source": {
    "chat_widget": 120,
    "api": 30
  },
  "conversion_rate": 6.67
}
```

### GET /leads/export (Admin)

Export leads to CSV or JSON.

**Query Parameters:**
- `format`: Export format (csv or json, default: csv)
- `status`: Filter by status
- `borough`: Filter by borough
- `start_date`: Start date filter
- `end_date`: End date filter

---

## Analytics Endpoints

### GET /analytics/summary (Admin)

Get comprehensive analytics summary.

**Query Parameters:**
- `days`: Number of days (default: 30, max: 365)

**Response:**
```json
{
  "period_days": 30,
  "total_queries": 5000,
  "unique_sessions": 1200,
  "avg_queries_per_session": 4.2,
  "total_leads": 150,
  "leads_with_email": 120,
  "conversion_rate": 10.0,
  "avg_response_time_ms": 1500,
  "top_boroughs": [
    {"borough": "Camden", "count": 1500},
    {"borough": "Barnet", "count": 1200}
  ],
  "top_topics": [
    {"topic": "extensions", "count": 2000},
    {"topic": "permitted_development", "count": 1500}
  ],
  "feedback_summary": {
    "positive": 400,
    "negative": 50,
    "satisfaction_rate": 88.9
  }
}
```

### GET /analytics/queries (Admin)

Get detailed query analytics.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | datetime | Start of date range |
| end_date | datetime | End of date range |
| borough | string | Filter by detected borough |
| topic | string | Filter by detected topic |
| limit | integer | Results per page (default: 100) |
| offset | integer | Pagination offset |

### GET /analytics/trending

Get trending planning topics (public endpoint).

**Query Parameters:**
- `days`: Number of days (default: 7, max: 30)
- `limit`: Number of topics (default: 5, max: 20)

**Response:**
```json
{
  "trending": [
    {"topic": "extensions", "query_count": 250},
    {"topic": "loft_conversions", "query_count": 180}
  ],
  "period": "last_7_days"
}
```

### GET /analytics/performance (Admin)

Get system performance metrics.

**Query Parameters:**
- `days`: Number of days (default: 7, max: 30)

**Response:**
```json
{
  "period_days": 7,
  "total_requests": 5000,
  "avg_response_time_ms": 1500,
  "p50_response_time_ms": 1200,
  "p95_response_time_ms": 2800,
  "p99_response_time_ms": 4500,
  "error_rate": 0.5
}
```

### GET /analytics/documents/usage (Admin)

Get document usage statistics.

**Response:**
```json
{
  "most_cited_documents": [
    {"document_id": "uuid", "title": "Camden Local Plan", "citation_count": 500}
  ],
  "citations_by_borough": {
    "Camden": 2000,
    "Barnet": 1500
  },
  "total_citations": 10000
}
```

### GET /analytics/conversion (Admin)

Get lead conversion metrics.

**Query Parameters:**
- `days`: Number of days (default: 30, max: 365)

**Response:**
```json
{
  "period_days": 30,
  "total_sessions": 1200,
  "sessions_with_multiple_queries": 800,
  "sessions_with_lead_capture": 150,
  "session_to_lead_rate": 12.5,
  "avg_queries_before_capture": 3.2
}
```

### GET /analytics/daily (Admin)

Get daily aggregated analytics.

**Query Parameters:**
- `start_date`: Start date
- `end_date`: End date
- `borough`: Filter by borough

**Response:**
```json
{
  "daily": [
    {
      "date": "2024-01-15",
      "borough": "Camden",
      "total_queries": 150,
      "unique_sessions": 45,
      "new_leads": 5,
      "avg_response_time": 1400
    }
  ],
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T00:00:00"
}
```

### POST /analytics/aggregate (Admin)

Trigger daily analytics aggregation manually.

**Query Parameters:**
- `date`: Date to aggregate (default: yesterday)

---

## Health Endpoints

### GET /health

Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /health/detailed

Detailed health check with dependency status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "database": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "openai": {"status": "healthy"}
  }
}
```

### GET /ready

Kubernetes readiness probe.

### GET /ping

Simple ping (returns "pong").

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "context": {
    "field": "additional context"
  }
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Input validation failed |
| 429 | Rate Limited - Too many requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `RATE_LIMITED` | Rate limit exceeded |
| `AUTHENTICATION_REQUIRED` | Auth token missing |
| `INVALID_TOKEN` | Auth token invalid or expired |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `PROCESSING_ERROR` | Error processing request |

---

## SDK Examples

### Python

```python
import httpx

API_BASE = "http://localhost:8000/api/v1"

async def ask_planning_question(question: str, session_id: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/chat/query",
            json={
                "message": question,
                "session_id": session_id,
                "include_sources": True
            }
        )
        return response.json()
```

### JavaScript/TypeScript

```typescript
const API_BASE = "http://localhost:8000/api/v1";

async function askPlanningQuestion(question: string, sessionId?: string) {
  const response = await fetch(`${API_BASE}/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: question,
      session_id: sessionId,
      include_sources: true,
    }),
  });
  return response.json();
}
```

### cURL

```bash
# Ask a question
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Can I build a loft conversion?", "borough": "Camden"}'

# Get analytics (authenticated)
curl http://localhost:8000/api/v1/analytics/summary \
  -H "Authorization: Bearer your-token"
```
