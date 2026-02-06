-- ServiceNow ITSM Integration Database Initialization Script
-- PostgreSQL 16

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- INCIDENT MANAGEMENT
-- =============================================================================

-- Incidents Table
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_number VARCHAR(50) UNIQUE NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    priority INTEGER DEFAULT 3,
    urgency INTEGER DEFAULT 3,
    impact INTEGER DEFAULT 3,
    state VARCHAR(50) DEFAULT 'New',
    assignment_group VARCHAR(100),
    assigned_to VARCHAR(100),
    caller_id VARCHAR(100),
    opened_by VARCHAR(100),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    closed_at TIMESTAMP,
    closed_by VARCHAR(100),
    resolution_code VARCHAR(50),
    resolution_notes TEXT,
    work_notes TEXT,
    additional_comments TEXT,
    configuration_item VARCHAR(100),
    business_service VARCHAR(100),
    sla_breached BOOLEAN DEFAULT FALSE,
    escalated BOOLEAN DEFAULT FALSE,
    external_reference VARCHAR(100),
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incident SLA
CREATE TABLE IF NOT EXISTS incident_sla (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    sla_definition_id INTEGER,
    sla_name VARCHAR(255),
    stage VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    actual_elapsed_ms BIGINT,
    breach_time TIMESTAMP,
    has_breached BOOLEAN DEFAULT FALSE,
    percentage_complete DECIMAL(5, 2),
    status VARCHAR(50) DEFAULT 'In Progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CHANGE MANAGEMENT
-- =============================================================================

-- Change Requests
CREATE TABLE IF NOT EXISTS change_requests (
    id SERIAL PRIMARY KEY,
    change_number VARCHAR(50) UNIQUE NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(50) DEFAULT 'Normal',
    category VARCHAR(100),
    priority INTEGER DEFAULT 3,
    risk VARCHAR(50) DEFAULT 'Moderate',
    impact VARCHAR(50) DEFAULT 'Medium',
    state VARCHAR(50) DEFAULT 'New',
    phase VARCHAR(50) DEFAULT 'Requested',
    requested_by VARCHAR(100),
    assignment_group VARCHAR(100),
    assigned_to VARCHAR(100),
    planned_start TIMESTAMP,
    planned_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    implementation_plan TEXT,
    backout_plan TEXT,
    test_plan TEXT,
    review_status VARCHAR(50),
    approval_status VARCHAR(50) DEFAULT 'Not Yet Requested',
    cab_required BOOLEAN DEFAULT FALSE,
    cab_date TIMESTAMP,
    configuration_item VARCHAR(100),
    business_service VARCHAR(100),
    external_reference VARCHAR(100),
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Change Approvals
CREATE TABLE IF NOT EXISTS change_approvals (
    id SERIAL PRIMARY KEY,
    change_id INTEGER REFERENCES change_requests(id) ON DELETE CASCADE,
    approver VARCHAR(100) NOT NULL,
    approver_group VARCHAR(100),
    approval_status VARCHAR(50) DEFAULT 'Requested',
    comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SERVICE REQUEST MANAGEMENT
-- =============================================================================

-- Service Requests
CREATE TABLE IF NOT EXISTS service_requests (
    id SERIAL PRIMARY KEY,
    request_number VARCHAR(50) UNIQUE NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    description TEXT,
    catalog_item VARCHAR(255),
    category VARCHAR(100),
    priority INTEGER DEFAULT 3,
    state VARCHAR(50) DEFAULT 'Open',
    requested_by VARCHAR(100),
    requested_for VARCHAR(100),
    assignment_group VARCHAR(100),
    assigned_to VARCHAR(100),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    fulfilled_at TIMESTAMP,
    fulfilled_by VARCHAR(100),
    closed_at TIMESTAMP,
    approval_status VARCHAR(50) DEFAULT 'Not Yet Requested',
    price DECIMAL(10, 2),
    quantity INTEGER DEFAULT 1,
    delivery_address TEXT,
    special_instructions TEXT,
    external_reference VARCHAR(100),
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Request Items (RITM)
CREATE TABLE IF NOT EXISTS request_items (
    id SERIAL PRIMARY KEY,
    ritm_number VARCHAR(50) UNIQUE NOT NULL,
    request_id INTEGER REFERENCES service_requests(id) ON DELETE CASCADE,
    catalog_item VARCHAR(255),
    short_description VARCHAR(500),
    quantity INTEGER DEFAULT 1,
    price DECIMAL(10, 2),
    state VARCHAR(50) DEFAULT 'Open',
    assignment_group VARCHAR(100),
    assigned_to VARCHAR(100),
    stage VARCHAR(50) DEFAULT 'Waiting for Approval',
    due_date TIMESTAMP,
    variables JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PROBLEM MANAGEMENT
-- =============================================================================

-- Problems
CREATE TABLE IF NOT EXISTS problems (
    id SERIAL PRIMARY KEY,
    problem_number VARCHAR(50) UNIQUE NOT NULL,
    short_description VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    priority INTEGER DEFAULT 3,
    urgency INTEGER DEFAULT 3,
    impact INTEGER DEFAULT 3,
    state VARCHAR(50) DEFAULT 'New',
    known_error BOOLEAN DEFAULT FALSE,
    assignment_group VARCHAR(100),
    assigned_to VARCHAR(100),
    opened_by VARCHAR(100),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    closed_at TIMESTAMP,
    root_cause TEXT,
    workaround TEXT,
    fix TEXT,
    configuration_item VARCHAR(100),
    business_service VARCHAR(100),
    external_reference VARCHAR(100),
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Problem-Incident Relationship
CREATE TABLE IF NOT EXISTS problem_incidents (
    id SERIAL PRIMARY KEY,
    problem_id INTEGER REFERENCES problems(id) ON DELETE CASCADE,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(problem_id, incident_id)
);

-- =============================================================================
-- KNOWLEDGE MANAGEMENT
-- =============================================================================

-- Knowledge Articles
CREATE TABLE IF NOT EXISTS knowledge_articles (
    id SERIAL PRIMARY KEY,
    article_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    short_description VARCHAR(1000),
    text TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    article_type VARCHAR(50),
    workflow_state VARCHAR(50) DEFAULT 'Draft',
    author VARCHAR(100),
    published_at TIMESTAMP,
    retired_at TIMESTAMP,
    valid_to DATE,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    rating DECIMAL(3, 2),
    keywords TEXT,
    related_incidents TEXT,
    external_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONFIGURATION MANAGEMENT (CMDB)
-- =============================================================================

-- Configuration Items
CREATE TABLE IF NOT EXISTS configuration_items (
    id SERIAL PRIMARY KEY,
    ci_name VARCHAR(255) NOT NULL,
    ci_class VARCHAR(100) NOT NULL,
    sys_class_name VARCHAR(100),
    asset_tag VARCHAR(100),
    serial_number VARCHAR(100),
    model_id VARCHAR(100),
    manufacturer VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Installed',
    operational_status VARCHAR(50) DEFAULT 'Operational',
    environment VARCHAR(50),
    location VARCHAR(255),
    department VARCHAR(100),
    assigned_to VARCHAR(100),
    supported_by VARCHAR(100),
    managed_by VARCHAR(100),
    owned_by VARCHAR(100),
    ip_address VARCHAR(50),
    mac_address VARCHAR(50),
    dns_domain VARCHAR(255),
    discovery_source VARCHAR(100),
    first_discovered TIMESTAMP,
    last_discovered TIMESTAMP,
    attributes JSONB,
    external_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CI Relationships
CREATE TABLE IF NOT EXISTS ci_relationships (
    id SERIAL PRIMARY KEY,
    parent_ci_id INTEGER REFERENCES configuration_items(id) ON DELETE CASCADE,
    child_ci_id INTEGER REFERENCES configuration_items(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_ci_id, child_ci_id, relationship_type)
);

-- =============================================================================
-- EXTERNAL INTEGRATION (CRM)
-- =============================================================================

-- CRM Account Approval Tickets
CREATE TABLE IF NOT EXISTS crm_account_approvals (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    crm_request_id INTEGER NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_industry VARCHAR(100),
    requested_by VARCHAR(100),
    requestor_role VARCHAR(50),
    approval_status VARCHAR(50) DEFAULT 'Pending',
    approved_by VARCHAR(100),
    approval_date TIMESTAMP,
    rejection_reason TEXT,
    notes TEXT,
    mulesoft_correlation_id UUID,
    external_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CRM Case Sync
CREATE TABLE IF NOT EXISTS crm_case_sync (
    id SERIAL PRIMARY KEY,
    crm_case_id INTEGER NOT NULL,
    crm_case_number VARCHAR(50) NOT NULL,
    servicenow_incident_id INTEGER REFERENCES incidents(id),
    servicenow_incident_number VARCHAR(50),
    sync_status VARCHAR(50) DEFAULT 'Pending',
    sync_direction VARCHAR(20) DEFAULT 'Inbound',
    last_sync_at TIMESTAMP,
    sync_error TEXT,
    payload_hash VARCHAR(64),
    mulesoft_correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- WORKFLOW & AUTOMATION
-- =============================================================================

-- Workflows
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    table_name VARCHAR(100),
    trigger_condition VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    run_as VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Executions
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id),
    record_table VARCHAR(100),
    record_id INTEGER,
    status VARCHAR(50) DEFAULT 'Running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    execution_log JSONB
);

-- Scheduled Jobs
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    script TEXT,
    schedule_type VARCHAR(50),
    schedule_cron VARCHAR(100),
    next_run_time TIMESTAMP,
    last_run_time TIMESTAMP,
    last_run_status VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    run_as VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- AUDIT & HISTORY
-- =============================================================================

-- System Audit Log
CREATE TABLE IF NOT EXISTS sys_audit (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    user_id VARCHAR(100),
    user_name VARCHAR(100),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- History Log
CREATE TABLE IF NOT EXISTS sys_history (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    set_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX idx_incidents_state ON incidents(state);
CREATE INDEX idx_incidents_priority ON incidents(priority);
CREATE INDEX idx_incidents_assigned ON incidents(assigned_to);
CREATE INDEX idx_incidents_correlation ON incidents(correlation_id);
CREATE INDEX idx_incidents_external ON incidents(external_reference);
CREATE INDEX idx_incident_sla_incident ON incident_sla(incident_id);
CREATE INDEX idx_change_requests_state ON change_requests(state);
CREATE INDEX idx_change_requests_phase ON change_requests(phase);
CREATE INDEX idx_service_requests_state ON service_requests(state);
CREATE INDEX idx_problems_state ON problems(state);
CREATE INDEX idx_knowledge_articles_workflow ON knowledge_articles(workflow_state);
CREATE INDEX idx_configuration_items_class ON configuration_items(ci_class);
CREATE INDEX idx_configuration_items_status ON configuration_items(status);
CREATE INDEX idx_crm_account_approvals_status ON crm_account_approvals(approval_status);
CREATE INDEX idx_crm_case_sync_crm ON crm_case_sync(crm_case_id);
CREATE INDEX idx_crm_case_sync_sn ON crm_case_sync(servicenow_incident_id);
CREATE INDEX idx_sys_audit_table_record ON sys_audit(table_name, record_id);
CREATE INDEX idx_sys_history_table_record ON sys_history(table_name, record_id);

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Default Assignment Groups
INSERT INTO incidents (incident_number, short_description, state, category, priority)
SELECT 'INC0000000', 'Template - Do Not Use', 'Closed', 'System', 5
WHERE NOT EXISTS (SELECT 1 FROM incidents WHERE incident_number = 'INC0000000');

-- Default Knowledge Categories
INSERT INTO knowledge_articles (article_number, title, short_description, workflow_state, category)
VALUES
    ('KB0000001', 'Welcome to ServiceNow Knowledge Base', 'Getting started with the knowledge base', 'Published', 'General'),
    ('KB0000002', 'How to Create an Incident', 'Step-by-step guide to creating incidents', 'Published', 'How-To'),
    ('KB0000003', 'CRM Integration Overview', 'Documentation for CRM-ServiceNow integration', 'Published', 'Integration');

-- Default Workflows
INSERT INTO workflows (workflow_name, description, table_name, trigger_condition, is_active)
VALUES
    ('Incident Auto-Assignment', 'Automatically assign incidents based on category', 'incidents', 'state = New', TRUE),
    ('CRM Account Approval', 'Approval workflow for CRM account creation requests', 'crm_account_approvals', 'approval_status = Pending', TRUE),
    ('Change Approval', 'CAB approval workflow for change requests', 'change_requests', 'cab_required = TRUE', TRUE);

-- Default Scheduled Jobs
INSERT INTO scheduled_jobs (job_name, description, schedule_type, schedule_cron, is_active)
VALUES
    ('SLA Breach Monitor', 'Monitor and flag SLA breaches', 'Recurring', '0 */15 * * * *', TRUE),
    ('CRM Sync Job', 'Sync data with CRM system', 'Recurring', '0 */5 * * * *', TRUE),
    ('Audit Log Cleanup', 'Archive old audit records', 'Recurring', '0 0 1 * * *', TRUE);

COMMENT ON DATABASE servicenow_itsm IS 'ServiceNow ITSM Clone - IT Service Management Database';
