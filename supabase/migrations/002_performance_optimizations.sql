-- ============================================
-- Performance Optimizations Migration
-- Version: 002
-- ============================================

-- ============================================
-- HNSW Index for Faster Vector Search
-- HNSW (Hierarchical Navigable Small World) provides
-- better query performance for large datasets
-- ============================================

-- Drop old IVFFlat index if exists
DROP INDEX IF EXISTS idx_chunks_embedding;

-- Create HNSW index (better for production workloads)
CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================
-- API Keys Table
-- Store hashed API keys for authentication
-- ============================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,  -- First 8 chars for identification
    name TEXT NOT NULL,
    description TEXT,
    scopes TEXT[] DEFAULT ARRAY['read'],
    rate_limit_override INTEGER,  -- Custom rate limit if needed
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);

-- ============================================
-- Query Cache Table
-- Cache frequently asked questions
-- ============================================
CREATE TABLE IF NOT EXISTS query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash TEXT NOT NULL UNIQUE,
    query_text TEXT NOT NULL,
    normalized_query TEXT,
    borough TEXT,
    response JSONB NOT NULL,
    sources JSONB,
    hit_count INTEGER DEFAULT 1,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',
    last_hit_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX idx_query_cache_valid ON query_cache(is_valid, expires_at);
CREATE INDEX idx_query_cache_borough ON query_cache(borough);

-- Function to get or create cache entry
CREATE OR REPLACE FUNCTION get_cached_response(
    p_query_hash TEXT,
    p_borough TEXT DEFAULT NULL
)
RETURNS TABLE (
    response JSONB,
    sources JSONB,
    hit_count INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update hit count and last_hit_at
    UPDATE query_cache
    SET
        hit_count = query_cache.hit_count + 1,
        last_hit_at = NOW()
    WHERE
        query_hash = p_query_hash
        AND is_valid = TRUE
        AND expires_at > NOW()
        AND (p_borough IS NULL OR borough = p_borough);

    RETURN QUERY
    SELECT
        qc.response,
        qc.sources,
        qc.hit_count
    FROM query_cache qc
    WHERE
        qc.query_hash = p_query_hash
        AND qc.is_valid = TRUE
        AND qc.expires_at > NOW()
        AND (p_borough IS NULL OR qc.borough = p_borough);
END;
$$;

-- ============================================
-- Document Stats Materialized View
-- Pre-computed statistics for dashboard
-- ============================================
CREATE MATERIALIZED VIEW IF NOT EXISTS document_stats AS
SELECT
    d.borough,
    d.category,
    COUNT(DISTINCT d.id) as document_count,
    SUM(d.total_chunks) as total_chunks,
    SUM(d.total_pages) as total_pages,
    MAX(d.updated_at) as last_updated
FROM documents d
WHERE d.is_active = TRUE
GROUP BY d.borough, d.category
WITH DATA;

CREATE UNIQUE INDEX idx_document_stats_borough_category
ON document_stats(borough, category);

-- Function to refresh document stats
CREATE OR REPLACE FUNCTION refresh_document_stats()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY document_stats;
END;
$$;

-- ============================================
-- Analytics Aggregation Table
-- Pre-computed daily analytics
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_daily (
    date DATE NOT NULL,
    borough TEXT,
    total_queries INTEGER DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,
    leads_captured INTEGER DEFAULT 0,
    top_topics TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, borough)
);

CREATE INDEX idx_analytics_daily_date ON analytics_daily(date);
CREATE INDEX idx_analytics_daily_borough ON analytics_daily(borough);

-- Function to aggregate daily analytics
CREATE OR REPLACE FUNCTION aggregate_daily_analytics(p_date DATE)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO analytics_daily (
        date,
        borough,
        total_queries,
        unique_sessions,
        avg_response_time_ms,
        positive_feedback,
        negative_feedback,
        leads_captured,
        top_topics
    )
    SELECT
        p_date,
        detected_borough,
        COUNT(*),
        COUNT(DISTINCT session_id),
        AVG(processing_time_ms),
        COUNT(*) FILTER (WHERE user_feedback = 'positive'),
        COUNT(*) FILTER (WHERE user_feedback = 'negative'),
        COUNT(*) FILTER (WHERE lead_captured = TRUE),
        (
            SELECT ARRAY_AGG(detected_topic ORDER BY topic_count DESC)
            FROM (
                SELECT detected_topic, COUNT(*) as topic_count
                FROM query_analytics qa2
                WHERE
                    qa2.detected_borough = qa.detected_borough
                    AND DATE(qa2.created_at) = p_date
                    AND qa2.detected_topic IS NOT NULL
                GROUP BY detected_topic
                LIMIT 5
            ) sub
        )
    FROM query_analytics qa
    WHERE DATE(created_at) = p_date
    GROUP BY detected_borough
    ON CONFLICT (date, borough) DO UPDATE SET
        total_queries = EXCLUDED.total_queries,
        unique_sessions = EXCLUDED.unique_sessions,
        avg_response_time_ms = EXCLUDED.avg_response_time_ms,
        positive_feedback = EXCLUDED.positive_feedback,
        negative_feedback = EXCLUDED.negative_feedback,
        leads_captured = EXCLUDED.leads_captured,
        top_topics = EXCLUDED.top_topics;
END;
$$;

-- ============================================
-- Session Cleanup Function
-- Remove old sessions to save space
-- ============================================
CREATE OR REPLACE FUNCTION cleanup_old_sessions(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chat_sessions
    WHERE
        last_activity < NOW() - (days_to_keep || ' days')::INTERVAL
        AND lead_id IS NULL;  -- Keep sessions linked to leads

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- ============================================
-- Cache Cleanup Function
-- Remove expired cache entries
-- ============================================
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM query_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- ============================================
-- Optimized Hybrid Search with Caching
-- ============================================
CREATE OR REPLACE FUNCTION hybrid_search_v2(
    query_text TEXT,
    query_embedding vector(3072),
    query_hash TEXT DEFAULT NULL,
    match_count INTEGER DEFAULT 20,
    vector_weight FLOAT DEFAULT 0.7,
    text_weight FLOAT DEFAULT 0.3,
    filter_borough TEXT DEFAULT NULL,
    use_cache BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    id TEXT,
    document_id UUID,
    document_name TEXT,
    borough TEXT,
    content TEXT,
    page_number INTEGER,
    section_title TEXT,
    vector_score FLOAT,
    text_score FLOAT,
    combined_score FLOAT,
    metadata JSONB,
    from_cache BOOLEAN
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    cached_result RECORD;
BEGIN
    -- Check cache first if enabled
    IF use_cache AND query_hash IS NOT NULL THEN
        SELECT * INTO cached_result
        FROM get_cached_response(query_hash, filter_borough);

        IF FOUND THEN
            -- Return cached results with from_cache flag
            RETURN QUERY
            SELECT
                (r->>'id')::TEXT,
                (r->>'document_id')::UUID,
                (r->>'document_name')::TEXT,
                (r->>'borough')::TEXT,
                (r->>'content')::TEXT,
                (r->>'page_number')::INTEGER,
                (r->>'section_title')::TEXT,
                (r->>'vector_score')::FLOAT,
                (r->>'text_score')::FLOAT,
                (r->>'combined_score')::FLOAT,
                (r->'metadata')::JSONB,
                TRUE
            FROM jsonb_array_elements(cached_result.sources) r;
            RETURN;
        END IF;
    END IF;

    -- Execute hybrid search
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
        vr.metadata,
        FALSE AS from_cache
    FROM vector_results vr
    LEFT JOIN text_results tr ON vr.id = tr.id
    ORDER BY (vr.vscore * vector_weight + COALESCE(tr.tscore, 0) * text_weight) DESC
    LIMIT match_count;
END;
$$;

-- ============================================
-- RLS for New Tables
-- ============================================
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_daily ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access to api_keys" ON api_keys
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to query_cache" ON query_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to analytics_daily" ON analytics_daily
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================
-- Trigger to Update API Key Last Used
-- ============================================
CREATE OR REPLACE FUNCTION update_api_key_last_used()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_used_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Grant Permissions
-- ============================================
GRANT SELECT ON document_stats TO anon, authenticated;
GRANT SELECT ON analytics_daily TO authenticated;
