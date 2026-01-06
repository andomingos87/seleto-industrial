-- Migration: create_pending_operations_table
-- TECH-030: Fallback for CRM failures
-- Created: 2026-01-06
--
-- This table stores CRM operations that failed and need to be retried later.
-- When CRM is unavailable, operations are stored here for later synchronization.

CREATE TABLE IF NOT EXISTS pending_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Operation details
    operation_type VARCHAR(50) NOT NULL,  -- create_deal, create_person, create_company, create_note, update_deal
    entity_type VARCHAR(50) NOT NULL,     -- deal, person, company, note
    entity_id VARCHAR(100),               -- local entity ID (lead_id, orcamento_id, etc.)
    payload JSONB NOT NULL,               -- operation payload to be sent to CRM

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 10,
    last_error TEXT,
    last_attempt_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_operation_type CHECK (operation_type IN (
        'create_deal', 'create_person', 'create_company', 'create_note', 'update_deal'
    )),
    CONSTRAINT valid_entity_type CHECK (entity_type IN ('deal', 'person', 'company', 'note'))
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_pending_operations_status ON pending_operations(status);
CREATE INDEX IF NOT EXISTS idx_pending_operations_created_at ON pending_operations(created_at);
CREATE INDEX IF NOT EXISTS idx_pending_operations_status_created ON pending_operations(status, created_at);
CREATE INDEX IF NOT EXISTS idx_pending_operations_entity ON pending_operations(entity_type, entity_id);

-- Enable RLS
ALTER TABLE pending_operations ENABLE ROW LEVEL SECURITY;

-- Create policy for service role (full access)
CREATE POLICY "service_role_pending_operations"
ON pending_operations
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Add comment
COMMENT ON TABLE pending_operations IS 'Stores CRM operations that failed and need to be retried later (TECH-030)';


-- Migration: add_crm_sync_status_to_leads
-- Add field to track CRM synchronization status per lead

ALTER TABLE leads ADD COLUMN IF NOT EXISTS crm_sync_status VARCHAR(20) DEFAULT 'synced';

-- Constraint for valid values (use DO block since ADD CONSTRAINT doesn't support IF NOT EXISTS)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_crm_sync_status'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT valid_crm_sync_status
            CHECK (crm_sync_status IN ('synced', 'pending', 'failed'));
    END IF;
END $$;

-- Index for querying leads by sync status
CREATE INDEX IF NOT EXISTS idx_leads_crm_sync_status ON leads(crm_sync_status);

COMMENT ON COLUMN leads.crm_sync_status IS 'CRM synchronization status: synced, pending, failed (TECH-030)';
