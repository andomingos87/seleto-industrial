-- TECH-028: Create audit_logs table for tracking sensitive operations
-- Apply this migration manually to Supabase using the SQL Editor

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'API_CALL')),
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255),
    user_id VARCHAR(100) DEFAULT 'system',
    changes JSONB,
    metadata JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_id ON audit_logs(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type_id ON audit_logs(entity_type, entity_id);

-- Composite index for common query pattern (entity lookup with time range)
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_timestamp
    ON audit_logs(entity_type, entity_id, timestamp DESC);

-- Add comments for documentation
COMMENT ON TABLE audit_logs IS 'Audit trail for sensitive operations (TECH-028). Stores CRUD operations on leads, orcamentos, empresas and API calls to external services.';
COMMENT ON COLUMN audit_logs.action IS 'Type of operation: CREATE, UPDATE, DELETE, or API_CALL';
COMMENT ON COLUMN audit_logs.entity_type IS 'Type of entity: lead, orcamento, empresa, api_call';
COMMENT ON COLUMN audit_logs.entity_id IS 'ID of the affected entity (UUID or external ID)';
COMMENT ON COLUMN audit_logs.user_id IS 'User or system that performed the action';
COMMENT ON COLUMN audit_logs.changes IS 'JSON with before/after values for UPDATE operations';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional context (masked sensitive data, request info)';
COMMENT ON COLUMN audit_logs.ip_address IS 'Client IP address if available';
