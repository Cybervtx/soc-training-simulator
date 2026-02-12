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
    details JSONB,
    ip_address VARCHAR(45),
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
    COUNT(CASE WHEN response_status >= 400 THEN 1 END) as error_count
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

-- =====================================================
-- SCENARIO ARTIFACTS TABLE (Parte 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS scenario_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('ip', 'domain', 'url', 'file_hash', 'email', 'registry_key', 'mutex')),
    value VARCHAR(500) NOT NULL,
    is_malicious BOOLEAN DEFAULT FALSE,
    is_critical BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    points INT DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scenario_artifacts_scenario ON scenario_artifacts(scenario_id);
CREATE INDEX IF NOT EXISTS idx_scenario_artifacts_type ON scenario_artifacts(type);
CREATE INDEX IF NOT EXISTS idx_scenario_artifacts_value ON scenario_artifacts(value);

-- =====================================================
-- SCENARIO TIMELINE TABLE (Parte 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS scenario_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(100) NOT NULL CHECK (event_type IN ('connection_attempt', 'authentication_failure', 'authentication_success', 'data_exfiltration', 'malware_detection', 'network_scan', 'c2_beacon', 'phishing_email', 'privilege_escalation', 'persistence', 'lateral_movement', 'command_execution', 'file_download', 'registry_modification', 'service_installation', 'other')),
    description TEXT,
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    source_port INT,
    destination_port INT,
    artifact_ids JSONB DEFAULT '[]',
    priority INT DEFAULT 1 CHECK (priority IN (1, 2, 3)),
    raw_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scenario_timeline_scenario ON scenario_timeline(scenario_id);
CREATE INDEX IF NOT EXISTS idx_scenario_timeline_timestamp ON scenario_timeline(scenario_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_scenario_timeline_event_type ON scenario_timeline(event_type);

-- =====================================================
-- SCENARIO TEMPLATES TABLE (Parte 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS scenario_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    incident_type VARCHAR(50) NOT NULL CHECK (incident_type IN ('port_scanning', 'brute_force', 'c2_communication', 'malware_distribution', 'phishing_campaign', 'data_exfiltration', 'apt_activity')),
    description TEXT,
    base_timeline JSONB NOT NULL,
    base_artifacts JSONB DEFAULT '[]',
    default_difficulty VARCHAR(20) DEFAULT 'beginner' CHECK (default_difficulty IN ('beginner', 'intermediate', 'advanced')),
    estimated_duration INT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_scenario_templates_type ON scenario_templates(incident_type);
CREATE INDEX IF NOT EXISTS idx_scenario_templates_active ON scenario_templates(is_active);

-- =====================================================
-- ENRICHED DATA CACHE TABLE (Parte 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS enriched_data_cache (
    id SERIAL PRIMARY KEY,
    query_type VARCHAR(50) NOT NULL CHECK (query_type IN ('whois', 'geolocation', 'pdns', 'reverse_dns', 'shodan', 'virus_total', 'abuseipdb_extended')),
    query_value VARCHAR(500) NOT NULL,
    result_data JSONB NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(100),
    UNIQUE(query_type, query_value)
);

CREATE INDEX IF NOT EXISTS idx_enriched_data_cache_query ON enriched_data_cache(query_type, query_value);
CREATE INDEX IF NOT EXISTS idx_enriched_data_cache_expires ON enriched_data_cache(expires_at);

-- =====================================================
-- INVESTIGATION NOTES TABLE (Parte 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS investigation_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    artifact_id UUID REFERENCES scenario_artifacts(id),
    content TEXT NOT NULL,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_investigation_notes_scenario ON investigation_notes(scenario_id);
CREATE INDEX IF NOT EXISTS idx_investigation_notes_user ON investigation_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_investigation_notes_artifact ON investigation_notes(artifact_id);

-- =====================================================
-- USER INVESTIGATION PROGRESS TABLE (Parte 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS user_investigation_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'in_progress' NOT NULL CHECK (status IN ('not_started', 'in_progress', 'completed', 'submitted')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    time_spent_seconds INT DEFAULT 0,
    artifacts_reviewed INT DEFAULT 0,
    conclusions TEXT,
    recommendations TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(scenario_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_investigation_scenario ON user_investigation_progress(scenario_id);
CREATE INDEX IF NOT EXISTS idx_user_investigation_user ON user_investigation_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_investigation_status ON user_investigation_progress(status);

-- =====================================================
-- ADDITIONAL TRIGGERS FOR PARTE 2
-- =====================================================

CREATE TRIGGER update_scenario_artifacts_updated_at
    BEFORE UPDATE ON scenario_artifacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scenario_timeline_updated_at
    BEFORE UPDATE ON scenario_timeline
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scenario_templates_updated_at
    BEFORE UPDATE ON scenario_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_investigation_notes_updated_at
    BEFORE UPDATE ON investigation_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_investigation_updated_at
    BEFORE UPDATE ON user_investigation_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE SCENARIO TEMPLATES (Parte 2)
-- =====================================================

INSERT INTO scenario_templates (name, incident_type, description, base_timeline, base_artifacts, default_difficulty, estimated_duration)
VALUES 
    (
        'Port Scanning Detection',
        'port_scanning',
        'Detected reconnaissance activity via port scanning',
        '[
            {"timestamp": "2025-02-11T10:00:00Z", "event_type": "network_scan", "description": "Initial SYN packet detected", "priority": 2},
            {"timestamp": "2025-02-11T10:00:05Z", "event_type": "connection_attempt", "description": "Connection attempt to port 22", "priority": 2},
            {"timestamp": "2025-02-11T10:00:10Z", "event_type": "connection_attempt", "description": "Connection attempt to port 80", "priority": 2},
            {"timestamp": "2025-02-11T10:00:15Z", "event_type": "connection_attempt", "description": "Connection attempt to port 443", "priority": 2},
            {"timestamp": "2025-02-11T10:00:20Z", "event_type": "network_scan", "description": "Rapid connection attempts detected", "priority": 3}
        ]',
        '[
            {"type": "ip", "value": "185.220.101.42", "is_malicious": true, "is_critical": true, "points": 20},
            {"type": "domain", "value": "scanner.badssl.com", "is_malicious": false, "is_critical": false, "points": 10}
        ]',
        'beginner',
        30
    ),
    (
        'SSH Brute Force Attack',
        'brute_force',
        'Brute force attack targeting SSH service',
        '[
            {"timestamp": "2025-02-11T10:25:00Z", "event_type": "connection_attempt", "description": "SSH connection from unknown IP", "priority": 2},
            {"timestamp": "2025-02-11T10:25:01Z", "event_type": "authentication_failure", "description": "Failed password attempt for user root", "priority": 2},
            {"timestamp": "2025-02-11T10:25:03Z", "event_type": "authentication_failure", "description": "Failed password attempt for user admin", "priority": 2},
            {"timestamp": "2025-02-11T10:25:05Z", "event_type": "authentication_failure", "description": "Failed password attempt for user ubuntu", "priority": 2},
            {"timestamp": "2025-02-11T10:25:07Z", "event_type": "authentication_failure", "description": "Failed password attempt for user administrator", "priority": 2},
            {"timestamp": "2025-02-11T10:26:00Z", "event_type": "authentication_success", "description": "Successful SSH login for user root", "priority": 3}
        ]',
        '[
            {"type": "ip", "value": "185.220.101.42", "is_malicious": true, "is_critical": true, "points": 25},
            {"type": "domain", "value": "brute-force.badssl.com", "is_malicious": true, "is_critical": false, "points": 15}
        ]',
        'intermediate',
        45
    )
ON CONFLICT DO NOTHING;

-- =====================================================
-- ENABLE RLS FOR NEW TABLES (Parte 2)
-- =====================================================

ALTER TABLE scenario_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenario_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenario_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE enriched_data_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigation_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_investigation_progress ENABLE ROW LEVEL SECURITY;

-- RLS Policies for scenario tables
CREATE POLICY "Users can view scenarios" ON scenarios
    FOR SELECT USING (true);

CREATE POLICY "Instructors can create scenarios" ON scenarios
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' AND EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('instructor', 'admin')
    ));

CREATE POLICY "Scenario creators can update" ON scenarios
    FOR UPDATE USING (auth.uid() = created_by OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    ));

CREATE POLICY "Authenticated users can view artifacts" ON scenario_artifacts
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can view timeline" ON scenario_timeline
    FOR SELECT USING (true);

CREATE POLICY "Instructors can manage templates" ON scenario_templates
    FOR ALL USING (EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('instructor', 'admin')
    ));

CREATE POLICY "Users can view enriched data cache" ON enriched_data_cache
    FOR SELECT USING (true);

CREATE POLICY "Users can manage own notes" ON investigation_notes
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own investigation progress" ON user_investigation_progress
    FOR ALL USING (auth.uid() = user_id);
