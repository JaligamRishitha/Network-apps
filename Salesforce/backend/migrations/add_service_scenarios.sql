-- ============================================
-- SQL Migration for Scenario 2 & 3 (SQLite)
-- ============================================

-- SCENARIO 2: Service Appointments & Scheduling
CREATE TABLE IF NOT EXISTS service_appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_number VARCHAR(50) UNIQUE,
    account_id INTEGER,
    case_id INTEGER,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    appointment_type VARCHAR(50) DEFAULT 'Field Service',
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Scheduled',
    priority VARCHAR(20) DEFAULT 'Normal',
    assigned_technician_id INTEGER,
    technician_name VARCHAR(100),
    location VARCHAR(255),
    required_skills VARCHAR(255),
    required_parts TEXT,
    owner_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_service_appointments_number ON service_appointments(appointment_number);

CREATE TABLE IF NOT EXISTS scheduling_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER,
    appointment_number VARCHAR(50),
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    integration_status VARCHAR(50),
    assigned_technician_id INTEGER,
    technician_name VARCHAR(100),
    parts_available BOOLEAN DEFAULT 1,
    parts_status TEXT,
    mulesoft_transaction_id VARCHAR(255),
    correlation_id VARCHAR(255),
    sap_hr_response TEXT,
    sap_inventory_response TEXT,
    requested_by_id INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES service_appointments(id),
    FOREIGN KEY (requested_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_scheduling_requests_appointment ON scheduling_requests(appointment_id);

-- SCENARIO 3: Work Orders
CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_number VARCHAR(50) UNIQUE,
    account_id INTEGER,
    case_id INTEGER,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'Medium',
    service_type VARCHAR(50) DEFAULT 'Warranty',
    product VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    integration_status VARCHAR(50),
    entitlement_verified BOOLEAN DEFAULT 0,
    entitlement_type VARCHAR(50),
    entitlement_end_date TIMESTAMP,
    sap_order_id VARCHAR(100),
    sap_notification_id VARCHAR(100),
    mulesoft_transaction_id VARCHAR(255),
    correlation_id VARCHAR(255),
    requested_by_id INTEGER,
    error_message TEXT,
    owner_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (requested_by_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_work_orders_number ON work_orders(work_order_number);
