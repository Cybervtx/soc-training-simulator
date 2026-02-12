-- SOC Training Simulator - Database Schema
-- Supabase/PostgreSQL Database Setup
-- Execute this script in your Supabase SQL Editor

-- =====================================================
-- EXTENSIONS
-- =====================================================

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing (if needed)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- USERS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'analyst' NOT NULL CHECK (role IN ('analyst', 'instructor', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Index for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- =====================================================
-- ABUSEIPDB CACHE TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS abuseipdb_cache (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) UNIQUE NOT NULL,
    reputation_score INT,
    categories INTEGER[],
    country_code VARCHAR(2),
    country_name VARCHAR(100),
    domain VARCHAR(255),
    last_checked TIMESTAMP WITH TIME ZONE NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_whitelisted BOOLEAN DEFAULT FALSE,
    usage_type VARCHAR(50),
    isp VARCHAR(255),
    num_days INT,
    last_report TIMESTAMP WITH TIME ZONE,
    abuse_confidence_score INT,
    total_reports INT,
    num_users INT
);

-- Indexes for abuseipdb_cache
CREATE INDEX IF NOT EXISTS idx_abuseipdb_cache_ip ON abuseipdb_cache(ip);
CREATE INDEX IF NOT EXISTS idx_abuseipdb_cache_expires ON abuseipdb_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_abuseipdb_cache_score ON abuseipdb_cache(reputation_score);
CREATE INDEX IF NOT EXISTS idx_abuseipdb_cache_country ON abuseipdb_cache(country_code);

-- =====================================================
-- ABUSEIPDB API LOG TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS abuseipdb_api_log (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    request_params JSONB,
    response_status INT,
    rate_limit_remaining INT,
    rate_limit_limit INT,
    error_message TEXT,
    response_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ip_address VARCHAR(45),
    user_id UUID
);

-- Indexes for abuseipdb_api_log
CREATE INDEX IF NOT EXISTS idx_abuseipdb_api_log_endpoint ON abuseipdb_api_log(endpoint);
CREATE INDEX IF NOT EXISTS idx_abuseipdb_api_log_created ON abuseipdb_api_log(created_at);
CREATE INDEX IF NOT EXISTS idx_abuseipdb_api_log_user ON abuseipdb_api_log(user_id);

-- =====================================================
-- INCIDENTS TABLE (for Parte 2 - Workspace)
-- =====================================================

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' NOT NULL CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    evidence JSONB,
    tags TEXT[],
    scenario_id UUID
);

-- Indexes for incidents
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned ON incidents(assigned_to);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at);

-- =====================================================
-- EVIDENCE TABLE (for Parte 2 - Workspace)
-- =====================================================

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('log', 'pcap', 'screenshot', 'document', 'alert', 'other')),
    name VARCHAR(255) NOT NULL,
    content TEXT,
    file_path VARCHAR(500),
    metadata JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for evidence
CREATE INDEX IF NOT EXISTS idx_evidence_incident ON evidence(incident_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(type);
CREATE INDEX IF NOT EXISTS idx_evidence_created ON evidence(created_at);

-- =====================================================
-- SCENARIOS TABLE (for Parte 2 - Workspace)
-- =====================================================

CREATE TABLE IF NOT EXISTS scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) DEFAULT 'beginner' NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    estimated_duration INT, -- in minutes
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    learning_objectives TEXT[],
    prerequisites TEXT[]
);

-- Indexes for scenarios
CREATE INDEX IF NOT EXISTS idx_scenarios_difficulty ON scenarios(difficulty);
CREATE INDEX IF NOT EXISTS idx_scenarios_active ON scenarios(is_active);
CREATE INDEX IF NOT EXISTS idx_scenarios_created ON scenarios(created_at);

-- =====================================================
-- USER ACTIVITY LOG TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS user_activity_log (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id JSONB,
    UUID,
    details ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for user_activity_log
CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_action ON user_activity_log(action);
CREATE INDEX IF NOT EXISTS idx_user_activity_created ON user_activity_log(created_at);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scenarios_updated_at
    BEFORE UPDATE ON scenarios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM abuseipdb_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- =====================================================
-- VIEWS
-- =====================================================

-- View for active incidents summary
CREATE OR REPLACE VIEW active_incidents_summary AS
SELECT 
    status,
    severity,
    COUNT(*) as count,
    DATE_TRUNC('day', created_at) as date
FROM incidents
WHERE status IN ('open', 'in_progress')
GROUP BY status, severity, DATE_TRUNC('day', created_at)
ORDER BY date DESC, status, severity;

-- View for API usage statistics
CREATE OR REPLACE VIEW api_usage_stats AS
SELECT 
    endpoint,
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_time_ms,
    COUNTASE WHEN response_status(C >= 400 THEN 1 END) as error_count
FROM abuseipdb_api_log
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY endpoint, DATE_TRUNC('hour', created_at)
ORDER BY hour DESC, endpoint;

-- =====================================================
-- ROW LEVEL SECURITY (RLS) - Supabase
-- =====================================================

-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE abuseipdb_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE abuseipdb_api_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies (adjust as needed for your security requirements)

-- Users can view their own data and admins can view all
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    ));

-- Only admins can modify users
CREATE POLICY "Admins can modify users" ON users
    FOR ALL USING (EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    ));

-- Everyone can view abuseipdb_cache (read-only)
CREATE POLICY "Public can view cache" ON abuseipdb_cache
    FOR SELECT USING (true);

-- Only authenticated users can log API usage
CREATE POLICY "Users can insert API logs" ON abuseipdb_api_log
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Admins can view all API logs
CREATE POLICY "Admins can view API logs" ON abuseipdb_api_log
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    ));

-- =====================================================
-- SAMPLE DATA (for testing)
-- =====================================================

-- Insert a sample admin user (password: admin123)
-- NOTE: In production, use proper password hashing through the application
INSERT INTO users (email, nome, password_hash, role)
VALUES ('admin@soc-training.local', 'Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.dW8KIuJ3eHFfTi', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Insert sample IPs into cache (for demonstration)
INSERT INTO abuseipdb_cache (ip, reputation_score, categories, country_code, country_name, domain, last_checked, cached_at, expires_at, is_whitelisted, abuse_confidence_score, total_reports)
VALUES 
    ('1.2.3.4', 100, ARRAY[18, 22], 'CN', 'China', 'example.cn', NOW(), NOW(), NOW() + INTERVAL '24 hours', FALSE, 100, 50),
    ('5.6.7.8', 25, ARRAY[21], 'US', 'United States', 'example.us', NOW(), NOW(), NOW() + INTERVAL '24 hours', FALSE, 25, 5),
    ('9.10.11.12', 0, NULL, 'BR', 'Brazil', NULL, NOW(), NOW(), NOW() + INTERVAL '24 hours', TRUE, 0, 0)
ON CONFLICT (ip) DO NOTHING;
