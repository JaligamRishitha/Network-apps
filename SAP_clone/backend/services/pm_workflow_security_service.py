"""
PM Workflow Security and Authorization Service
Requirements: 3.6, 9.3

Provides role-based access control (RBAC) and authorization checks for PM Workflow.
"""
from typing import Optional, List, Tuple
from enum import Enum
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder,
    WorkflowOrderStatus,
    WorkflowOrderType
)


class PMWorkflowRole(str, Enum):
    """User roles for PM Workflow"""
    PLANNER = "planner"  # Can create and plan orders
    SUPERVISOR = "supervisor"  # Can release orders
    TECHNICIAN = "technician"  # Can execute work and confirm
    WAREHOUSE = "warehouse"  # Can post GR/GI
    CONTROLLER = "controller"  # Can view costs and settle
    ADMIN = "admin"  # Full access


class PMWorkflowPermission(str, Enum):
    """Permissions for PM Workflow actions"""
    CREATE_ORDER = "create_order"
    EDIT_ORDER = "edit_order"
    DELETE_ORDER = "delete_order"
    RELEASE_ORDER = "release_order"
    OVERRIDE_BLOCKS = "override_blocks"
    CREATE_PO = "create_po"
    POST_GR = "post_gr"
    POST_GI = "post_gi"
    POST_CONFIRMATION = "post_confirmation"
    TECO_ORDER = "teco_order"
    VIEW_COSTS = "view_costs"
    SETTLE_COSTS = "settle_costs"
    CREATE_MALFUNCTION_REPORT = "create_malfunction_report"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    PMWorkflowRole.PLANNER: [
        PMWorkflowPermission.CREATE_ORDER,
        PMWorkflowPermission.EDIT_ORDER,
        PMWorkflowPermission.CREATE_PO,
        PMWorkflowPermission.VIEW_COSTS,
    ],
    PMWorkflowRole.SUPERVISOR: [
        PMWorkflowPermission.CREATE_ORDER,
        PMWorkflowPermission.EDIT_ORDER,
        PMWorkflowPermission.RELEASE_ORDER,
        PMWorkflowPermission.OVERRIDE_BLOCKS,
        PMWorkflowPermission.VIEW_COSTS,
        PMWorkflowPermission.TECO_ORDER,
    ],
    PMWorkflowRole.TECHNICIAN: [
        PMWorkflowPermission.POST_GI,
        PMWorkflowPermission.POST_CONFIRMATION,
        PMWorkflowPermission.CREATE_MALFUNCTION_REPORT,
    ],
    PMWorkflowRole.WAREHOUSE: [
        PMWorkflowPermission.POST_GR,
        PMWorkflowPermission.POST_GI,
    ],
    PMWorkflowRole.CONTROLLER: [
        PMWorkflowPermission.VIEW_COSTS,
        PMWorkflowPermission.SETTLE_COSTS,
        PMWorkflowPermission.TECO_ORDER,
    ],
    PMWorkflowRole.ADMIN: [
        # Admin has all permissions
        PMWorkflowPermission.CREATE_ORDER,
        PMWorkflowPermission.EDIT_ORDER,
        PMWorkflowPermission.DELETE_ORDER,
        PMWorkflowPermission.RELEASE_ORDER,
        PMWorkflowPermission.OVERRIDE_BLOCKS,
        PMWorkflowPermission.CREATE_PO,
        PMWorkflowPermission.POST_GR,
        PMWorkflowPermission.POST_GI,
        PMWorkflowPermission.POST_CONFIRMATION,
        PMWorkflowPermission.TECO_ORDER,
        PMWorkflowPermission.VIEW_COSTS,
        PMWorkflowPermission.SETTLE_COSTS,
        PMWorkflowPermission.CREATE_MALFUNCTION_REPORT,
    ],
}


class PMWorkflowSecurityService:
    """Service for security and authorization"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def get_user_roles(self, user_id: str) -> List[PMWorkflowRole]:
        """
        Get roles for a user.
        In production, would query user-role mapping from database.
        """
        # Mock implementation - in production, query from database
        mock_user_roles = {
            "planner1": [PMWorkflowRole.PLANNER],
            "supervisor1": [PMWorkflowRole.SUPERVISOR],
            "tech1": [PMWorkflowRole.TECHNICIAN],
            "warehouse1": [PMWorkflowRole.WAREHOUSE],
            "controller1": [PMWorkflowRole.CONTROLLER],
            "admin": [PMWorkflowRole.ADMIN],
            # Default user has planner role
            "default": [PMWorkflowRole.PLANNER],
        }
        
        return mock_user_roles.get(user_id, [PMWorkflowRole.PLANNER])
    
    def get_user_permissions(self, user_id: str) -> List[PMWorkflowPermission]:
        """Get all permissions for a user based on their roles"""
        roles = self.get_user_roles(user_id)
        permissions = set()
        
        for role in roles:
            role_perms = ROLE_PERMISSIONS.get(role, [])
            permissions.update(role_perms)
        
        return list(permissions)
    
    def has_permission(
        self,
        user_id: str,
        permission: PMWorkflowPermission
    ) -> bool:
        """Check if user has a specific permission"""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
    
    def check_permission(
        self,
        user_id: str,
        permission: PMWorkflowPermission
    ) -> Tuple[bool, Optional[str]]:
        """
        Check permission and return result with error message.
        
        Returns:
            Tuple of (authorized, error_message)
        """
        if self.has_permission(user_id, permission):
            return True, None
        else:
            return False, f"User {user_id} does not have permission: {permission.value}"
    
    def can_access_screen(
        self,
        user_id: str,
        screen_number: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can access a specific screen.
        Requirement: 3.6
        """
        screen_permissions = {
            1: [PMWorkflowPermission.CREATE_ORDER, PMWorkflowPermission.EDIT_ORDER],
            2: [PMWorkflowPermission.CREATE_PO],
            3: [PMWorkflowPermission.RELEASE_ORDER],
            4: [PMWorkflowPermission.POST_GR],
            5: [PMWorkflowPermission.POST_GI, PMWorkflowPermission.POST_CONFIRMATION],
            6: [PMWorkflowPermission.VIEW_COSTS, PMWorkflowPermission.TECO_ORDER],
        }
        
        required_perms = screen_permissions.get(screen_number, [])
        user_perms = self.get_user_permissions(user_id)
        
        # User needs at least one of the required permissions
        has_access = any(perm in user_perms for perm in required_perms)
        
        if has_access:
            return True, None
        else:
            return False, f"User does not have access to Screen {screen_number}"
    
    def can_perform_state_transition(
        self,
        user_id: str,
        from_status: WorkflowOrderStatus,
        to_status: WorkflowOrderStatus
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user is authorized to perform a state transition.
        Requirement: 3.6
        """
        # Define which transitions require which permissions
        transition_permissions = {
            (WorkflowOrderStatus.CREATED, WorkflowOrderStatus.PLANNED): PMWorkflowPermission.EDIT_ORDER,
            (WorkflowOrderStatus.PLANNED, WorkflowOrderStatus.RELEASED): PMWorkflowPermission.RELEASE_ORDER,
            (WorkflowOrderStatus.RELEASED, WorkflowOrderStatus.IN_PROGRESS): PMWorkflowPermission.POST_CONFIRMATION,
            (WorkflowOrderStatus.IN_PROGRESS, WorkflowOrderStatus.CONFIRMED): PMWorkflowPermission.POST_CONFIRMATION,
            (WorkflowOrderStatus.CONFIRMED, WorkflowOrderStatus.TECO): PMWorkflowPermission.TECO_ORDER,
        }
        
        required_permission = transition_permissions.get((from_status, to_status))
        
        if not required_permission:
            return False, f"Invalid state transition: {from_status.value} -> {to_status.value}"
        
        return self.check_permission(user_id, required_permission)
    
    def can_override_release_blocks(
        self,
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can override release blocks.
        Requirement: 3.6
        """
        return self.check_permission(user_id, PMWorkflowPermission.OVERRIDE_BLOCKS)
    
    async def create_audit_log(
        self,
        order_number: str,
        user_id: str,
        action: str,
        details: Optional[str] = None,
        success: bool = True
    ) -> None:
        """
        Create audit log entry for transaction.
        Requirement: 9.3
        
        In production, would write to audit log table.
        """
        # Mock implementation - in production, write to database
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "order_number": order_number,
            "user_id": user_id,
            "action": action,
            "details": details,
            "success": success
        }
        
        # In production, would insert into audit_log table
        print(f"[AUDIT] {log_entry}")
    
    def get_user_info(self, user_id: str) -> dict:
        """Get user information for display"""
        roles = self.get_user_roles(user_id)
        permissions = self.get_user_permissions(user_id)
        
        return {
            "user_id": user_id,
            "roles": [role.value for role in roles],
            "permissions": [perm.value for perm in permissions],
            "is_admin": PMWorkflowRole.ADMIN in roles
        }


# Dependency for FastAPI routes
def get_security_service(db: AsyncSession) -> PMWorkflowSecurityService:
    """Get security service instance"""
    return PMWorkflowSecurityService(db)
