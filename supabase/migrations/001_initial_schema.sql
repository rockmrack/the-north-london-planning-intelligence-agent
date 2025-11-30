-- ============================================
-- The North London Planning Intelligence Agent
-- Initial Database Schema
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search

-- ============================================
-- Documents Table
-- Stores metadata about ingested documents
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_name TEXT NOT NULL,
    borough TEXT NOT NULL CHECK (borough IN ('Camden', 'Barnet', 'Westminster', 'Brent', 'Haringey')),
    category TEXT NOT NULL CHECK (category IN (
        'local_plan', 'conservation_area', 'design_guide',
        'supplementary_planning_document', 'basement', 'extensions',
        'roof', 'windows', 'heritage', 'sustainability', 'other'
    )),
    source_url TEXT,
    file_path TEXT,
    file_type TEXT,
    total_pages INTEGER,
    total_chunks INTEGER,
    publication_date TIMESTAMPTZ,
    version TEXT DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    extra_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for documents
CREATE INDEX idx_documents_borough ON documents(borough);
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_active ON documents(is_active);
CREATE INDEX idx_documents_name ON documents USING gin(document_name gin_trgm_ops);

-- ============================================
-- Document Chunks Table
-- Stores chunked content with embeddings
-- ============================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    embedding vector(3072),  -- text-embedding-3-large dimensions
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for document_chunks
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_page ON document_chunks(page_number);
CREATE INDEX idx_chunks_section ON document_chunks(section_title);
CREATE INDEX idx_chunks_content ON document_chunks USING gin(content gin_trgm_ops);

-- Vector similarity index (IVFFlat for faster search)
CREATE INDEX idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- Chat Sessions Table
-- Stores conversation history
-- ============================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    messages JSONB DEFAULT '[]'::jsonb,
    query_count INTEGER DEFAULT 0,
    detected_borough TEXT,
    detected_topics TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for chat_sessions
CREATE INDEX idx_sessions_lead ON chat_sessions(lead_id);
CREATE INDEX idx_sessions_created ON chat_sessions(created_at);
CREATE INDEX idx_sessions_activity ON chat_sessions(last_activity);

-- ============================================
-- Leads Table
-- Stores captured leads
-- ============================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    postcode TEXT,
    address TEXT,
    borough TEXT,
    property_type TEXT,
    project_type TEXT,
    project_description TEXT,
    budget_range TEXT,
    timeline TEXT,
    source TEXT DEFAULT 'chat_widget',
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'lost')),
    query_count INTEGER DEFAULT 0,
    queries TEXT[],
    notes TEXT,
    assigned_to TEXT,
    marketing_consent BOOLEAN DEFAULT FALSE,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ
);

-- Indexes for leads
CREATE UNIQUE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_borough ON leads(borough);
CREATE INDEX idx_leads_created ON leads(created_at);
CREATE INDEX idx_leads_source ON leads(source);

-- ============================================
-- Query Analytics Table
-- Stores analytics for each query
-- ============================================
CREATE TABLE IF NOT EXISTS query_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT REFERENCES chat_sessions(id),
    query_text TEXT NOT NULL,
    detected_borough TEXT,
    detected_location TEXT,
    detected_topic TEXT,
    response_length INTEGER,
    citations_count INTEGER DEFAULT 0,
    documents_retrieved INTEGER DEFAULT 0,
    processing_time_ms FLOAT,
    user_feedback TEXT CHECK (user_feedback IN ('positive', 'negative', NULL)),
    feedback_comment TEXT,
    is_follow_up BOOLEAN DEFAULT FALSE,
    lead_captured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for query_analytics
CREATE INDEX idx_analytics_session ON query_analytics(session_id);
CREATE INDEX idx_analytics_borough ON query_analytics(detected_borough);
CREATE INDEX idx_analytics_topic ON query_analytics(detected_topic);
CREATE INDEX idx_analytics_created ON query_analytics(created_at);
CREATE INDEX idx_analytics_feedback ON query_analytics(user_feedback);

-- ============================================
-- Vector Search Function
-- Performs similarity search with filters
-- ============================================
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(3072),
    match_threshold float DEFAULT 0.75,
    match_count int DEFAULT 10,
    filter_borough text DEFAULT NULL,
    filter_category text DEFAULT NULL
)
RETURNS TABLE (
    id text,
    document_id uuid,
    document_name text,
    borough text,
    content text,
    page_number int,
    section_title text,
    similarity float,
    metadata jsonb
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        d.document_name,
        d.borough,
        dc.content,
        dc.page_number,
        dc.section_title,
        1 - (dc.embedding <=> query_embedding) AS similarity,
        dc.metadata
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE
        d.is_active = TRUE
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
        AND (filter_borough IS NULL OR d.borough = filter_borough)
        AND (filter_category IS NULL OR d.category = filter_category)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================
-- Hybrid Search Function
-- Combines vector and text search
-- ============================================
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text text,
    query_embedding vector(3072),
    match_count int DEFAULT 20,
    vector_weight float DEFAULT 0.7,
    text_weight float DEFAULT 0.3,
    filter_borough text DEFAULT NULL
)
RETURNS TABLE (
    id text,
    document_id uuid,
    document_name text,
    borough text,
    content text,
    page_number int,
    section_title text,
    vector_score float,
    text_score float,
    combined_score float,
    metadata jsonb
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            dc.id,
            dc.document_id,
            d.document_name,
            d.borough,
            dc.content,
            dc.page_number,
            dc.section_title,
            1 - (dc.embedding <=> query_embedding) AS vscore,
            dc.metadata
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE
            d.is_active = TRUE
            AND (filter_borough IS NULL OR d.borough = filter_borough)
        ORDER BY dc.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    text_results AS (
        SELECT
            dc.id,
            similarity(dc.content, query_text) AS tscore
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE
            d.is_active = TRUE
            AND dc.content % query_text
            AND (filter_borough IS NULL OR d.borough = filter_borough)
        LIMIT match_count * 2
    )
    SELECT
        vr.id,
        vr.document_id,
        vr.document_name,
        vr.borough,
        vr.content,
        vr.page_number,
        vr.section_title,
        vr.vscore AS vector_score,
        COALESCE(tr.tscore, 0) AS text_score,
        (vr.vscore * vector_weight + COALESCE(tr.tscore, 0) * text_weight) AS combined_score,
        vr.metadata
    FROM vector_results vr
    LEFT JOIN text_results tr ON vr.id = tr.id
    ORDER BY (vr.vscore * vector_weight + COALESCE(tr.tscore, 0) * text_weight) DESC
    LIMIT match_count;
END;
$$;

-- ============================================
-- Row Level Security (RLS) Policies
-- ============================================

-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_analytics ENABLE ROW LEVEL SECURITY;

-- Public read access to documents (for the API)
CREATE POLICY "Public read access to documents" ON documents
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "Public read access to chunks" ON document_chunks
    FOR SELECT USING (TRUE);

-- Service role has full access
CREATE POLICY "Service role full access to documents" ON documents
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to chunks" ON document_chunks
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to sessions" ON chat_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to leads" ON leads
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to analytics" ON query_analytics
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================
-- Triggers for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
