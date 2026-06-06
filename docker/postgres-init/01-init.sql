-- OMNI Database Initialization

CREATE TABLE IF NOT EXISTS omni_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(100),
    priority VARCHAR(20) CHECK (priority IN ('critical', 'standard', 'complex')),
    status VARCHAR(50) CHECK (status IN ('extracted', 'planned', 'validated', 'approved', 'correction_required', 'failed')),
    plan JSONB,
    raw_input JSONB,
    cleaned_data JSONB,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omni_tasks_status ON omni_tasks(status);
CREATE INDEX IF NOT EXISTS idx_omni_tasks_priority ON omni_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_omni_tasks_created ON omni_tasks(created_at);

CREATE TABLE IF NOT EXISTS omni_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id VARCHAR(255),
    agent VARCHAR(100),
    task_id VARCHAR(255),
    event_type VARCHAR(100),
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omni_audit_trace ON omni_audit(trace_id);
CREATE INDEX IF NOT EXISTS idx_omni_audit_task ON omni_audit(task_id);
