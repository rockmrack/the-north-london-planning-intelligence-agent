# Architecture Guide

## Overview

The North London Planning Intelligence Agent is a RAG (Retrieval-Augmented Generation) system that provides AI-powered planning permission guidance. This document details the system architecture and design decisions.

## System Components

### 1. Document Ingestion Pipeline

```
Raw Documents → Parser → Chunker → Embedder → Vector Store
     ↓            ↓         ↓          ↓           ↓
  PDF/DOCX    Extract    Split    Generate    Store in
   /HTML       Text     Chunks   Embeddings   Supabase
```

**Key Features:**
- Multi-format support (PDF, DOCX, HTML, TXT)
- OCR fallback for scanned documents
- Semantic chunking with overlap
- Metadata extraction (borough, category, page numbers)

### 2. RAG Engine

```
User Query → Query Refinement → Hybrid Retrieval → Reranking → Generation
     ↓              ↓                 ↓               ↓            ↓
  Natural      Extract         Vector +         Cross-      GPT-4o
  Language     Metadata         BM25            Encoder     Response
```

**Key Features:**
- Hybrid search (vector + keyword)
- Query metadata extraction
- Result reranking for relevance
- Citation generation

### 3. API Layer (FastAPI)

**Endpoints:**
- `/api/v1/chat/query` - Main chat endpoint
- `/api/v1/chat/query/stream` - Streaming responses
- `/api/v1/documents/*` - Document management
- `/api/v1/leads/*` - Lead capture
- `/api/v1/analytics/*` - Usage analytics

### 4. Frontend (Next.js)

**Components:**
- Chat widget (floating button + modal)
- Message display with citations
- Lead capture form
- Landing page

## Data Flow

### Query Processing

1. **User Input**: User types a planning question
2. **Session Management**: Get/create session, load history
3. **Query Refinement**: Extract borough, topic, location
4. **Retrieval**: Search vector DB with filters
5. **Reranking**: Reorder results by relevance
6. **Generation**: Generate response with GPT-4o
7. **Citation**: Extract and format citations
8. **Response**: Return with suggested follow-ups

### Document Ingestion

1. **Parse**: Extract text from document
2. **Chunk**: Split into semantic units (512 tokens, 50 overlap)
3. **Embed**: Generate vectors with text-embedding-3-large
4. **Store**: Save chunks with metadata to Supabase

## Database Schema

### Core Tables

- `documents`: Document metadata
- `document_chunks`: Chunked content with embeddings
- `chat_sessions`: Conversation history
- `leads`: Captured user information
- `query_analytics`: Usage tracking

### Vector Search

Uses pgvector extension with IVFFlat index for efficient similarity search.

## Caching Strategy

- **Query Cache**: Redis, 1 hour TTL
- **Embedding Cache**: Redis, 7 day TTL
- **Session Cache**: Redis, 24 hour TTL

## Security

- Rate limiting (100 req/hour by default)
- Input sanitization (prevent prompt injection)
- Row-level security in Supabase
- API key authentication for admin endpoints

## Deployment

### Docker Compose

- Backend: FastAPI on Uvicorn
- Frontend: Next.js standalone
- Redis: Caching layer
- Nginx: Reverse proxy (production)

### Environment

- Development: Debug mode, local services
- Production: Optimized builds, managed services

## Performance Considerations

- Batch embedding generation
- Connection pooling for database
- Gzip compression
- CDN for static assets
- Lazy loading for frontend
