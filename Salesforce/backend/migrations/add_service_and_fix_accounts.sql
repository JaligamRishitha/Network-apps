-- ============================================
-- PostgreSQL Migration for Scenario 2 & 3
-- Plus fix accounts table
-- ============================================

-- Fix accounts table - add missing columns
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(255);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS integration_status VARCHAR(50);

-- Create index on correlation_id
CREATE INDEX IF NOT EXISTS idx_accounts_correlation_id ON accounts(correlation_id);

-- ============================================
-- SCENARIO 2: Service Appointments & Scheduling
-- ============================================

CREATE TABLE IF NOT EXISTS service_appointments (
    id SERIAL PRIMARY KEY,
    appointment_number VARCHAR(50) UNIQUE,
    account_id INTEGER REFERENCES accounts(id),
    case_id INTEGER REFERENCES cases(id),
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    appointment_type VARCHAR(50) DEFAULT 'Field Service',
    scheduled_start TIMESTAMP WITH TIME ZONE,
    scheduled_end TIMESTAMP WITH TIME ZONE,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'Scheduled',
    priority VARCHAR(20) DEFAULT 'Normal',
    assigned_technician_id INTEGER,
    technician_name VARCHAR(100),
    location VARCHAR(255),
    required_skills VARCHAR(255),
    required_parts TEXT,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_service_appointments_number ON service_appointments(appointment_number);
CREATE INDEX IF NOT EXISTS idx_service_appointments_account ON service_appointments(account_id);
CREATE INDEX IF NOT EXISTS idx_service_appointments_status ON service_appointments(status);

CREATE TABLE IF NOT EXISTS scheduling_requests (
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER REFERENCES service_appointments(id),
    appointment_number VARCHAR(50),
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    integration_status VARCHAR(50),
    assigned_technician_id INTEGER,
    technician_name VARCHAR(100),
    parts_available BOOLEAN DEFAULT TRUE,
    parts_status TEXT,
    mulesoft_transaction_id VARCHAR(255),
    correlation_id VARCHAR(255),
    sap_hr_response TEXT,
    sap_inventory_response TEXT,
    requested_by_id INTEGER REFERENCES users(id),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_scheduling_requests_appointment ON scheduling_requests(appointment_id);
CREATE INDEX IF NOT EXISTS idx_scheduling_requests_status ON scheduling_requests(status);
CREATE INDEX IF NOT EXISTS idx_scheduling_requests_correlation ON scheduling_requests(correlation_id);

-- ============================================
-- SCENARIO 3: Work Orders
-- ============================================

CREATE TABLE IF NOT EXISTS work_orders (
    id SERIAL PRIMARY KEY,
    work_order_number VARCHAR(50) UNIQUE,
    account_id INTEGER REFERENCES accounts(id),
    case_id INTEGER REFERENCES cases(id),
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'Medium',
    service_type VARCHAR(50) DEFAULT 'Warranty',
    product VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    integration_status VARCHAR(50),
    entitlement_verified BOOLEAN DEFAULT FALSE,
    entitlement_type VARCHAR(50),
    entitlement_end_date TIMESTAMP WITH TIME ZONE,
    sap_order_id VARCHAR(100),
    sap_notification_id VARCHAR(100),
    mulesoft_transaction_id VARCHAR(255),
    correlation_id VARCHAR(255),
    requested_by_id INTEGER REFERENCES users(id),
    error_message TEXT,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_work_orders_number ON work_orders(work_order_number);
CREATE INDEX IF NOT EXISTS idx_work_orders_account ON work_orders(account_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_correlation ON work_orders(correlation_id);
