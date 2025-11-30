# API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

Most endpoints are public. Admin endpoints require Bearer token authentication.

```
Authorization: Bearer <token>
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
      "relevance_score": 0.92
    }
  ],
  "suggested_questions": [
    {"question": "What is the maximum depth for a rear extension?"}
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

### GET /chat/boroughs

Get list of supported boroughs.

### GET /chat/topics

Get list of planning topics with examples.

---

## Document Endpoints

### POST /documents/ingest

Ingest a document (requires authentication).

**Request Body:**
```json
{
  "file_path": "/path/to/document.pdf",
  "document_name": "Camden Local Plan 2024",
  "borough": "Camden",
  "category": "local_plan"
}
```

### POST /documents/ingest/upload

Upload and ingest a document file.

**Multipart Form:**
- `file`: Document file
- `document_name`: Name (optional)
- `borough`: Borough enum
- `category`: Category enum

### GET /documents

List all ingested documents.

**Query Parameters:**
- `borough`: Filter by borough
- `category`: Filter by category
- `is_active`: Active status (default: true)

### GET /documents/{document_id}

Get document details.

### DELETE /documents/{document_id}

Delete a document (requires authentication).

### GET /documents/stats/summary

Get document statistics.

---

## Lead Endpoints

### POST /leads/capture

Capture a lead from chat.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Smith",
  "postcode": "NW3 1AB",
  "project_type": "extension",
  "session_id": "session_abc123",
  "marketing_consent": true
}
```

### POST /leads/check-email

Check if email exists.

**Query Parameters:**
- `email`: Email address

---

## Analytics Endpoints

### GET /analytics/summary

Get analytics summary (requires authentication).

**Query Parameters:**
- `days`: Number of days (default: 30)

### GET /analytics/trending

Get trending topics (public).

### GET /analytics/performance

Get performance metrics (requires authentication).

---

## Health Endpoints

### GET /health

Health check.

### GET /ready

Readiness check.

### GET /ping

Simple ping (returns "pong").

---

## Error Responses

```json
{
  "detail": "Error message",
  "error": "Error type"
}
```

**Status Codes:**
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Rate Limited
- `500`: Internal Server Error
