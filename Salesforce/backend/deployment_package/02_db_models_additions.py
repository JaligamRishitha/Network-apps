# ============================================
# Add these classes to the END of db_models.py
# ============================================

class ServiceAppointment(Base):
    """
    Service Appointments for field service scheduling (Scenario 2)
    """
    __tablename__ = "service_appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)

    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    appointment_type = Column(String(50), default="Field Service")  # Field Service, Phone, Remote

    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(50), default="Scheduled")  # Scheduled, Dispatched, In Progress, Completed, Cancelled
    priority = Column(String(20), default="Normal")  # Low, Normal, High, Critical

    assigned_technician_id = Column(Integer, nullable=True)
    technician_name = Column(String(100), nullable=True)

    location = Column(String(255), nullable=True)
    required_skills = Column(String(255), nullable=True)
    required_parts = Column(Text, nullable=True)  # JSON list of parts

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account", backref="service_appointments")
    case = relationship("Case", backref="service_appointments")
    owner = relationship("User", backref="owned_appointments")


class SchedulingRequest(Base):
    """
    Track MuleSoft scheduling requests for service appointments (Scenario 2)
    """
    __tablename__ = "scheduling_requests"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("service_appointments.id"), nullable=True, index=True)
    appointment_number = Column(String(50), nullable=True)

    request_type = Column(String(50), nullable=False)  # schedule, reschedule, cancel
    status = Column(String(50), default="PENDING")  # PENDING, SUCCESS, PARTS_UNAVAILABLE, TECHNICIAN_UNAVAILABLE, FAILED
    integration_status = Column(String(50), nullable=True)  # PENDING_MULESOFT, CHECKING_SAP_HR, CHECKING_SAP_INVENTORY, COMPLETED

    # Assignment results
    assigned_technician_id = Column(Integer, nullable=True)
    technician_name = Column(String(100), nullable=True)
    parts_available = Column(Boolean, default=True)
    parts_status = Column(Text, nullable=True)  # JSON with parts availability details

    # MuleSoft tracking
    mulesoft_transaction_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)

    # SAP tracking
    sap_hr_response = Column(Text, nullable=True)
    sap_inventory_response = Column(Text, nullable=True)

    # Request details
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    appointment = relationship("ServiceAppointment", backref="scheduling_requests")
    requested_by = relationship("User")


class WorkOrder(Base):
    """
    Work Orders for service requests (Scenario 3)
    """
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    work_order_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)

    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    service_type = Column(String(50), default="Warranty")  # Warranty, Paid, Contract
    product = Column(String(255), nullable=True)

    status = Column(String(50), default="PENDING")  # PENDING, SUCCESS, ENTITLEMENT_FAILED, COMPLETED, FAILED
    integration_status = Column(String(50), nullable=True)  # PENDING_MULESOFT, CHECKING_ENTITLEMENT, COMPLETED

    # Entitlement tracking
    entitlement_verified = Column(Boolean, default=False)
    entitlement_type = Column(String(50), nullable=True)  # Warranty, Contract, etc.
    entitlement_end_date = Column(DateTime(timezone=True), nullable=True)

    # SAP Integration
    sap_order_id = Column(String(100), nullable=True)
    sap_notification_id = Column(String(100), nullable=True)

    # MuleSoft tracking
    mulesoft_transaction_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)

    # Request details
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error_message = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account", backref="work_orders")
    case = relationship("Case", backref="work_orders")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_work_orders")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
