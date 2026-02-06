"""
PM Workflow External System Integration Service
Requirements: 1.2, 2.1, 4.2, 6.7

This service provides integration interfaces for external SAP modules:
- SAP MM (Materials Management) for material master data and inventory
- SAP FI (Financial Accounting) for cost posting
- SAP HR (Human Resources) for technician data
- Notification System for breakdown notifications

In a production system, these would connect to real SAP modules via RFC, OData, or REST APIs.
For this demo, we provide mock implementations that can be replaced with real integrations.
"""
from typing import Optional, Dict, List, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class SAPMMIntegrationService:
    """Integration with SAP MM (Materials Management)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_material_master_data(
        self,
        material_number: str
    ) -> Optional[Dict]:
        """
        Get material master data from SAP MM.
        Requirement 1.2
        
        Returns material details including:
        - Description
        - Unit of measure
        - Standard price
        - Material group
        - Stock levels
        """
        # Mock implementation - in production, would call SAP MM API
        mock_materials = {
            "MAT-001": {
                "material_number": "MAT-001",
                "description": "Hydraulic Pump Assembly",
                "unit_of_measure": "EA",
                "standard_price": Decimal("450.00"),
                "material_group": "PUMPS",
                "available_stock": Decimal("15"),
                "reserved_stock": Decimal("3"),
                "on_order_stock": Decimal("10")
            },
            "MAT-002": {
                "material_number": "MAT-002",
                "description": "Industrial Bearing 6205",
                "unit_of_measure": "EA",
                "standard_price": Decimal("25.50"),
                "material_group": "BEARINGS",
                "available_stock": Decimal("150"),
                "reserved_stock": Decimal("20"),
                "on_order_stock": Decimal("0")
            },
            "MAT-003": {
                "material_number": "MAT-003",
                "description": "Hydraulic Oil SAE 10W",
                "unit_of_measure": "L",
                "standard_price": Decimal("12.00"),
                "material_group": "LUBRICANTS",
                "available_stock": Decimal("500"),
                "reserved_stock": Decimal("50"),
                "on_order_stock": Decimal("200")
            }
        }
        
        return mock_materials.get(material_number)
    
    async def check_material_availability(
        self,
        material_number: str,
        quantity_required: Decimal,
        plant: str = "1000"
    ) -> Tuple[bool, Decimal, str]:
        """
        Check if material is available in sufficient quantity.
        Requirement 3.2
        
        Returns:
            Tuple of (available, available_quantity, message)
        """
        material_data = await self.get_material_master_data(material_number)
        
        if not material_data:
            return False, Decimal("0"), f"Material {material_number} not found in master data"
        
        available_qty = material_data["available_stock"]
        
        if available_qty >= quantity_required:
            return True, available_qty, f"{available_qty} units available"
        else:
            shortage = quantity_required - available_qty
            on_order = material_data.get("on_order_stock", Decimal("0"))
            if on_order > 0:
                return False, available_qty, f"Short {shortage} units, but {on_order} on order"
            else:
                return False, available_qty, f"Short {shortage} units, procurement required"
    
    async def create_purchase_order_in_mm(
        self,
        vendor_id: str,
        material_number: str,
        quantity: Decimal,
        delivery_date: datetime,
        plant: str = "1000"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create purchase order in SAP MM.
        Requirement 2.1
        
        Returns:
            Tuple of (success, po_number, error_message)
        """
        # Mock implementation - in production, would call SAP MM BAPI or OData service
        # Example: BAPI_PO_CREATE1
        
        # Validate material exists
        material_data = await self.get_material_master_data(material_number)
        if not material_data:
            return False, None, f"Material {material_number} not found"
        
        # Generate mock PO number
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        po_number = f"MM-PO-{timestamp[-8:]}"
        
        # In production, would create actual PO in SAP MM
        # For now, just return success
        return True, po_number, None
    
    async def post_goods_receipt_to_mm(
        self,
        po_number: str,
        material_number: str,
        quantity: Decimal,
        storage_location: str,
        movement_type: str = "101"  # GR for PO
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post goods receipt to SAP MM inventory.
        Requirement 4.2
        
        Returns:
            Tuple of (success, material_document, error_message)
        """
        # Mock implementation - in production, would call SAP MM BAPI
        # Example: BAPI_GOODSMVT_CREATE with movement type 101
        
        # Generate mock material document
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        material_document = f"MM-GR-{timestamp[-8:]}"
        
        # In production, would:
        # 1. Update inventory quantities
        # 2. Create material document
        # 3. Update PO history
        # 4. Post to FI if price differences exist
        
        return True, material_document, None
    
    async def post_goods_issue_to_mm(
        self,
        material_number: str,
        quantity: Decimal,
        cost_center: str,
        order_number: str,
        movement_type: str = "261"  # GI for order
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post goods issue to SAP MM inventory.
        Requirement 5.1
        
        Returns:
            Tuple of (success, material_document, error_message)
        """
        # Mock implementation - in production, would call SAP MM BAPI
        # Example: BAPI_GOODSMVT_CREATE with movement type 261
        
        # Check availability
        material_data = await self.get_material_master_data(material_number)
        if not material_data:
            return False, None, f"Material {material_number} not found"
        
        available_qty = material_data["available_stock"]
        if available_qty < quantity:
            return False, None, f"Insufficient stock: {available_qty} available, {quantity} required"
        
        # Generate mock material document
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        material_document = f"MM-GI-{timestamp[-8:]}"
        
        # In production, would:
        # 1. Reduce inventory quantities
        # 2. Create material document
        # 3. Post consumption to cost center/order
        
        return True, material_document, None


class SAPFIIntegrationService:
    """Integration with SAP FI (Financial Accounting)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_cost_center(
        self,
        cost_center: str,
        company_code: str = "1000"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate cost center exists and is active.
        Requirement 6.7
        
        Returns:
            Tuple of (valid, error_message)
        """
        # Mock implementation - in production, would query SAP FI tables
        # Example: Read table CSKS (Cost Center Master)
        
        mock_cost_centers = {
            "CC-MAINT-001": "Maintenance Department",
            "CC-PROD-001": "Production Line 1",
            "CC-PROD-002": "Production Line 2",
            "CC-ADMIN-001": "Administration"
        }
        
        if cost_center in mock_cost_centers:
            return True, None
        else:
            return False, f"Cost center {cost_center} not found or inactive"
    
    async def post_cost_settlement_to_fi(
        self,
        order_number: str,
        cost_center: str,
        material_cost: Decimal,
        labor_cost: Decimal,
        external_cost: Decimal,
        total_cost: Decimal,
        posting_date: datetime,
        company_code: str = "1000"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Post cost settlement to SAP FI.
        Requirement 6.7
        
        Creates FI document to transfer costs from order to cost center.
        
        Returns:
            Tuple of (success, fi_document, error_message)
        """
        # Mock implementation - in production, would call SAP FI BAPI
        # Example: BAPI_ACC_DOCUMENT_POST
        
        # Validate cost center
        valid, error_msg = await self.validate_cost_center(cost_center)
        if not valid:
            return False, None, error_msg
        
        # Generate mock FI document
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        fi_document = f"FI-DOC-{timestamp[-8:]}"
        
        # In production, would create FI document with:
        # - Debit: Cost center (by cost element)
        # - Credit: Order settlement account
        # - Line items for material, labor, external costs
        
        return True, fi_document, None
    
    async def get_cost_element_master_data(
        self,
        cost_element: str
    ) -> Optional[Dict]:
        """
        Get cost element master data from SAP FI.
        
        Returns cost element details including description and category.
        """
        # Mock implementation
        mock_cost_elements = {
            "CE-MAT": {
                "cost_element": "CE-MAT",
                "description": "Material Costs",
                "category": "primary",
                "cost_element_group": "MATERIALS"
            },
            "CE-LABOR": {
                "cost_element": "CE-LABOR",
                "description": "Labor Costs",
                "category": "primary",
                "cost_element_group": "PERSONNEL"
            },
            "CE-EXTERNAL": {
                "cost_element": "CE-EXTERNAL",
                "description": "External Services",
                "category": "primary",
                "cost_element_group": "SERVICES"
            }
        }
        
        return mock_cost_elements.get(cost_element)


class SAPHRIntegrationService:
    """Integration with SAP HR (Human Resources)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_technician_master_data(
        self,
        technician_id: str
    ) -> Optional[Dict]:
        """
        Get technician master data from SAP HR.
        Requirement 3.3
        
        Returns technician details including:
        - Name
        - Skills/qualifications
        - Work center
        - Availability
        - Labor rate
        """
        # Mock implementation - in production, would query SAP HR tables
        # Example: Read table PA0001 (Organizational Assignment)
        
        mock_technicians = {
            "TECH-001": {
                "technician_id": "TECH-001",
                "name": "John Smith",
                "work_center": "MAINT-01",
                "skills": ["Hydraulics", "Electrical", "Mechanical"],
                "qualification_level": "Senior",
                "labor_rate": Decimal("50.00"),
                "available": True,
                "shift": "Day"
            },
            "TECH-002": {
                "technician_id": "TECH-002",
                "name": "Maria Garcia",
                "work_center": "MAINT-01",
                "skills": ["Electrical", "PLC Programming", "Instrumentation"],
                "qualification_level": "Expert",
                "labor_rate": Decimal("65.00"),
                "available": True,
                "shift": "Day"
            },
            "TECH-003": {
                "technician_id": "TECH-003",
                "name": "David Chen",
                "work_center": "MAINT-02",
                "skills": ["Mechanical", "Welding", "Fabrication"],
                "qualification_level": "Intermediate",
                "labor_rate": Decimal("45.00"),
                "available": False,
                "shift": "Night"
            }
        }
        
        return mock_technicians.get(technician_id)
    
    async def check_technician_availability(
        self,
        technician_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if technician is available for the specified period.
        Requirement 3.3
        
        Returns:
            Tuple of (available, reason)
        """
        technician_data = await self.get_technician_master_data(technician_id)
        
        if not technician_data:
            return False, f"Technician {technician_id} not found"
        
        if not technician_data["available"]:
            return False, f"Technician on leave or assigned to other work"
        
        # In production, would check:
        # - Leave calendar
        # - Other work assignments
        # - Training schedules
        # - Shift patterns
        
        return True, None
    
    async def get_labor_rate(
        self,
        technician_id: str
    ) -> Optional[Decimal]:
        """
        Get labor rate for technician.
        Used for cost calculation.
        """
        technician_data = await self.get_technician_master_data(technician_id)
        
        if technician_data:
            return technician_data["labor_rate"]
        
        return None


class NotificationSystemIntegrationService:
    """Integration with Notification System"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_breakdown_notification(
        self,
        notification_id: str
    ) -> Optional[Dict]:
        """
        Get breakdown notification details.
        Requirement 1.2
        
        Returns notification details including:
        - Equipment
        - Functional location
        - Description
        - Priority
        - Reporter
        """
        # Mock implementation - in production, would query notification system
        # Example: SAP PM notification tables (QMEL, QMFE)
        
        mock_notifications = {
            "NOTIF-001": {
                "notification_id": "NOTIF-001",
                "notification_type": "M1",  # Malfunction
                "equipment_id": "EQ-PUMP-001",
                "functional_location": "PLANT-A/AREA-1/LINE-1",
                "description": "Hydraulic pump making unusual noise and vibration",
                "priority": "urgent",
                "reporter": "Operator Smith",
                "reported_date": "2024-01-27T08:30:00",
                "status": "open"
            },
            "NOTIF-002": {
                "notification_id": "NOTIF-002",
                "notification_type": "M1",
                "equipment_id": "EQ-MOTOR-005",
                "functional_location": "PLANT-A/AREA-2/LINE-3",
                "description": "Motor overheating, temperature above 80°C",
                "priority": "urgent",
                "reporter": "Supervisor Jones",
                "reported_date": "2024-01-27T10:15:00",
                "status": "open"
            }
        }
        
        return mock_notifications.get(notification_id)
    
    async def send_notification(
        self,
        recipient: str,
        subject: str,
        message: str,
        notification_type: str = "email"
    ) -> Tuple[bool, Optional[str]]:
        """
        Send notification to user.
        Used for alerts and status updates.
        
        Returns:
            Tuple of (success, error_message)
        """
        # Mock implementation - in production, would integrate with:
        # - Email system (SMTP)
        # - SMS gateway
        # - Mobile push notifications
        # - SAP Business Notification
        
        # For demo, just log and return success
        print(f"[NOTIFICATION] To: {recipient}, Subject: {subject}, Type: {notification_type}")
        print(f"[NOTIFICATION] Message: {message}")
        
        return True, None
    
    async def update_notification_status(
        self,
        notification_id: str,
        status: str,
        order_number: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update notification status.
        Links notification to maintenance order.
        
        Returns:
            Tuple of (success, error_message)
        """
        # Mock implementation - in production, would update notification tables
        
        notification = await self.get_breakdown_notification(notification_id)
        if not notification:
            return False, f"Notification {notification_id} not found"
        
        # In production, would update notification status and link to order
        print(f"[NOTIFICATION] Updated {notification_id} status to {status}, linked to order {order_number}")
        
        return True, None


class PMWorkflowIntegrationService:
    """
    Unified integration service for PM Workflow.
    Provides single interface to all external systems.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mm = SAPMMIntegrationService(db)
        self.fi = SAPFIIntegrationService(db)
        self.hr = SAPHRIntegrationService(db)
        self.notifications = NotificationSystemIntegrationService(db)
    
    async def validate_order_prerequisites(
        self,
        order_data: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate order prerequisites across all systems.
        
        Checks:
        - Material availability (MM)
        - Technician availability (HR)
        - Cost center validity (FI)
        
        Returns:
            Tuple of (all_valid, blocking_reasons)
        """
        blocking_reasons = []
        
        # Check materials
        for component in order_data.get("components", []):
            material_number = component.get("material_number")
            quantity = component.get("quantity_required", Decimal("0"))
            
            if material_number:
                available, qty, msg = await self.mm.check_material_availability(
                    material_number, quantity
                )
                if not available:
                    blocking_reasons.append(f"Material {material_number}: {msg}")
        
        # Check technicians
        for operation in order_data.get("operations", []):
            technician_id = operation.get("technician_id")
            if technician_id:
                tech_data = await self.hr.get_technician_master_data(technician_id)
                if not tech_data:
                    blocking_reasons.append(f"Technician {technician_id} not found")
                elif not tech_data.get("available"):
                    blocking_reasons.append(f"Technician {technician_id} not available")
        
        return len(blocking_reasons) == 0, blocking_reasons
