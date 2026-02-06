-- MuleSoft Integration Database Initialization Script
-- PostgreSQL 16

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- API MANAGEMENT TABLES
-- =============================================================================

-- API Registry - Registered APIs
CREATE TABLE IF NOT EXISTS api_registry (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(255) NOT NULL,
    api_version VARCHAR(50) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    description TEXT,
    api_type VARCHAR(50) DEFAULT 'REST',
    authentication_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Active',
    owner VARCHAR(100),
    documentation_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(api_name, api_version)
);

-- API Endpoints
CREATE TABLE IF NOT EXISTS api_endpoints (
    id SERIAL PRIMARY KEY,
    api_id INTEGER REFERENCES api_registry(id) ON DELETE CASCADE,
    endpoint_path VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    description TEXT,
    request_schema JSONB,
    response_schema JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER,
    timeout_ms INTEGER DEFAULT 30000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INTEGRATION FLOWS
-- =============================================================================

-- Integration Flows Configuration
CREATE TABLE IF NOT EXISTS integration_flows (
    id SERIAL PRIMARY KEY,
    flow_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    source_system VARCHAR(100) NOT NULL,
    target_system VARCHAR(100) NOT NULL,
    flow_type VARCHAR(50) DEFAULT 'Sync',
    transformation_spec JSONB,
    error_handling_policy JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    schedule_cron VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flow Execution History
CREATE TABLE IF NOT EXISTS flow_executions (
    id SERIAL PRIMARY KEY,
    flow_id INTEGER REFERENCES integration_flows(id),
    execution_id UUID DEFAULT uuid_generate_v4(),
    status VARCHAR(50) DEFAULT 'Running',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    execution_log JSONB
);

-- =============================================================================
-- MESSAGE QUEUE & EVENTS
-- =============================================================================

-- Message Queue
CREATE TABLE IF NOT EXISTS message_queue (
    id SERIAL PRIMARY KEY,
    message_id UUID DEFAULT uuid_generate_v4() UNIQUE,
    queue_name VARCHAR(100) NOT NULL,
    message_type VARCHAR(100),
    payload JSONB NOT NULL,
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'Pending',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT,
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event Store
CREATE TABLE IF NOT EXISTS event_store (
    id SERIAL PRIMARY KEY,
    event_id UUID DEFAULT uuid_generate_v4() UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(100),
    aggregate_id VARCHAR(100),
    payload JSONB NOT NULL,
    metadata JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONNECTOR CONFIGURATIONS
-- =============================================================================

-- Connector Configurations
CREATE TABLE IF NOT EXISTS connectors (
    id SERIAL PRIMARY KEY,
    connector_name VARCHAR(255) NOT NULL UNIQUE,
    connector_type VARCHAR(50) NOT NULL,
    connection_config JSONB NOT NULL,
    credentials_ref VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Active',
    health_check_url VARCHAR(500),
    last_health_check TIMESTAMP,
    health_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Connector Mappings (Field Mappings between systems)
CREATE TABLE IF NOT EXISTS connector_mappings (
    id SERIAL PRIMARY KEY,
    connector_id INTEGER REFERENCES connectors(id) ON DELETE CASCADE,
    source_object VARCHAR(100) NOT NULL,
    target_object VARCHAR(100) NOT NULL,
    field_mappings JSONB NOT NULL,
    transformation_rules JSONB,
    is_bidirectional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SALESFORCE INTEGRATION
-- =============================================================================

-- Salesforce Sync Status
CREATE TABLE IF NOT EXISTS salesforce_sync_status (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(100) NOT NULL,
    salesforce_id VARCHAR(50),
    external_id VARCHAR(100),
    sync_direction VARCHAR(20) DEFAULT 'Outbound',
    sync_status VARCHAR(50) DEFAULT 'Pending',
    last_sync_at TIMESTAMP,
    sync_error TEXT,
    retry_count INTEGER DEFAULT 0,
    payload_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Salesforce Outbound Messages
CREATE TABLE IF NOT EXISTS salesforce_outbound_messages (
    id SERIAL PRIMARY KEY,
    message_id UUID DEFAULT uuid_generate_v4(),
    object_type VARCHAR(100) NOT NULL,
    object_id VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    processed_at TIMESTAMP,
    response JSONB,
    error_message TEXT,
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SAP INTEGRATION
-- =============================================================================

-- SAP Case Mappings
CREATE TABLE IF NOT EXISTS sap_case_mappings (
    id SERIAL PRIMARY KEY,
    crm_case_id INTEGER NOT NULL,
    crm_case_number VARCHAR(50) NOT NULL,
    sap_case_id VARCHAR(50),
    sap_case_number VARCHAR(50),
    sync_status VARCHAR(50) DEFAULT 'Pending',
    last_sync_at TIMESTAMP,
    sync_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SAP Integration Logs
CREATE TABLE IF NOT EXISTS sap_integration_logs (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(50) NOT NULL,
    crm_case_id INTEGER,
    sap_case_id VARCHAR(50),
    request_payload JSONB,
    response_payload JSONB,
    status VARCHAR(50),
    error_message TEXT,
    duration_ms INTEGER,
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SERVICENOW INTEGRATION
-- =============================================================================

-- ServiceNow Ticket Mappings
CREATE TABLE IF NOT EXISTS servicenow_ticket_mappings (
    id SERIAL PRIMARY KEY,
    crm_object_type VARCHAR(50) NOT NULL,
    crm_object_id INTEGER NOT NULL,
    servicenow_ticket_id VARCHAR(50),
    servicenow_ticket_number VARCHAR(50),
    ticket_type VARCHAR(50),
    sync_status VARCHAR(50) DEFAULT 'Pending',
    last_sync_at TIMESTAMP,
    sync_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ServiceNow Integration Logs
CREATE TABLE IF NOT EXISTS servicenow_integration_logs (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(50) NOT NULL,
    crm_object_type VARCHAR(50),
    crm_object_id INTEGER,
    servicenow_ticket_id VARCHAR(50),
    request_payload JSONB,
    response_payload JSONB,
    status VARCHAR(50),
    error_message TEXT,
    duration_ms INTEGER,
    correlation_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- API ANALYTICS
-- =============================================================================

-- API Call Logs
CREATE TABLE IF NOT EXISTS api_call_logs (
    id SERIAL PRIMARY KEY,
    api_id INTEGER REFERENCES api_registry(id),
    endpoint_id INTEGER REFERENCES api_endpoints(id),
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    request_headers JSONB,
    request_body JSONB,
    response_status INTEGER,
    response_body JSONB,
    duration_ms INTEGER,
    client_ip VARCHAR(50),
    user_agent TEXT,
    correlation_id UUID,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Metrics (Aggregated)
CREATE TABLE IF NOT EXISTS api_metrics (
    id SERIAL PRIMARY KEY,
    api_id INTEGER REFERENCES api_registry(id),
    metric_date DATE NOT NULL,
    metric_hour INTEGER,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(10, 2),
    p95_response_time_ms DECIMAL(10, 2),
    p99_response_time_ms DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(api_id, metric_date, metric_hour)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX idx_api_endpoints_api ON api_endpoints(api_id);
CREATE INDEX idx_flow_executions_flow ON flow_executions(flow_id);
CREATE INDEX idx_flow_executions_status ON flow_executions(status);
CREATE INDEX idx_message_queue_status ON message_queue(status);
CREATE INDEX idx_message_queue_queue ON message_queue(queue_name);
CREATE INDEX idx_message_queue_correlation ON message_queue(correlation_id);
CREATE INDEX idx_event_store_type ON event_store(event_type);
CREATE INDEX idx_event_store_aggregate ON event_store(aggregate_type, aggregate_id);
CREATE INDEX idx_salesforce_sync_status ON salesforce_sync_status(object_type, sync_status);
CREATE INDEX idx_sap_case_mappings_crm ON sap_case_mappings(crm_case_id);
CREATE INDEX idx_sap_case_mappings_sap ON sap_case_mappings(sap_case_id);
CREATE INDEX idx_servicenow_mappings_crm ON servicenow_ticket_mappings(crm_object_type, crm_object_id);
CREATE INDEX idx_api_call_logs_api ON api_call_logs(api_id);
CREATE INDEX idx_api_call_logs_created ON api_call_logs(created_at);
CREATE INDEX idx_api_metrics_api_date ON api_metrics(api_id, metric_date);

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Register default connectors
INSERT INTO connectors (connector_name, connector_type, connection_config, status)
VALUES
    ('Salesforce CRM', 'Salesforce', '{"instance_url": "http://salesforce-backend:8000", "api_version": "v1"}', 'Active'),
    ('SAP ERP', 'SAP', '{"system_id": "PRD", "client": "100", "base_url": "https://sap.example.com"}', 'Inactive'),
    ('ServiceNow ITSM', 'ServiceNow', '{"instance": "dev12345", "base_url": "https://dev12345.service-now.com"}', 'Inactive');

-- Register default APIs
INSERT INTO api_registry (api_name, api_version, base_url, description, api_type, authentication_type)
VALUES
    ('Salesforce CRM API', 'v1', 'http://salesforce-backend:8000/api', 'Main CRM API for Salesforce operations', 'REST', 'JWT'),
    ('MuleSoft Process API', 'v1', 'http://localhost:8081/api', 'Process API layer for integrations', 'REST', 'OAuth2'),
    ('MuleSoft Experience API', 'v1', 'http://localhost:8082/api', 'Experience API for frontend consumption', 'REST', 'OAuth2');

-- Register default integration flows
INSERT INTO integration_flows (flow_name, description, source_system, target_system, flow_type)
VALUES
    ('CRM-to-SAP-Case-Sync', 'Synchronize CRM cases to SAP Service Management', 'Salesforce', 'SAP', 'Sync'),
    ('CRM-to-ServiceNow-Ticket', 'Create ServiceNow tickets from CRM requests', 'Salesforce', 'ServiceNow', 'Async'),
    ('SAP-to-CRM-Update', 'Update CRM records from SAP changes', 'SAP', 'Salesforce', 'Sync');

COMMENT ON DATABASE mulesoft_integration IS 'MuleSoft Integration Platform - API Management and Integration Layer';
