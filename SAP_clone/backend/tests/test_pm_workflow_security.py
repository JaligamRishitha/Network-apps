"""
Tests for PM Workflow Security and Authorization
Requirements: 3.6, 9.3
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.pm_workflow_security_service import (
    PMWorkflowSecurityService,
    PMWorkflowRole,
    PMWorkflowPermission
)
from backend.models.pm_workflow_models import WorkflowOrderStatus


@pytest.mark.asyncio
async def test_get_user_roles(db: AsyncSession):
    """Test getting user roles"""
    security_service = PMWorkflowSecurityService(db)
    
    # Test planner role
    roles = security_service.get_user_roles("planner1")
    assert PMWorkflowRole.PLANNER in roles
    
    # Test admin role
    roles = security_service.get_user_roles("admin")
    assert PMWorkflowRole.ADMIN in roles
    
    # Test default role
    roles = security_service.get_user_roles("unknown_user")
    assert PMWorkflowRole.PLANNER in roles


@pytest.mark.asyncio
async def test_get_user_permissions(db: AsyncSession):
    """Test getting user permissions"""
    security_service = PMWorkflowSecurityService(db)
    
    # Test planner permissions
    perms = security_service.get_user_permissions("planner1")
    assert PMWorkflowPermission.CREATE_ORDER in perms
    assert PMWorkflowPermission.EDIT_ORDER in perms
    assert PMWorkflowPermission.RELEASE_ORDER not in perms
    
    # Test admin permissions (should have all)
    perms = security_service.get_user_permissions("admin")
    assert PMWorkflowPermission.CREATE_ORDER in perms
    assert PMWorkflowPermission.RELEASE_ORDER in perms
    assert PMWorkflowPermission.SETTLE_COSTS in perms


@pytest.mark.asyncio
async def test_has_permission(db: AsyncSession):
    """Test permission checking"""
    security_service = PMWorkflowSecurityService(db)
    
    # Planner can create orders
    assert security_service.has_permission("planner1", PMWorkflowPermission.CREATE_ORDER)
    
    # Planner cannot release orders
    assert not security_service.has_permission("planner1", PMWorkflowPermission.RELEASE_ORDER)
    
    # Supervisor can release orders
    assert security_service.has_permission("supervisor1", PMWorkflowPermission.RELEASE_ORDER)
    
    # Admin can do everything
    assert security_service.has_permission("admin", PMWorkflowPermission.CREATE_ORDER)
    assert security_service.has_permission("admin", PMWorkflowPermission.SETTLE_COSTS)


@pytest.mark.asyncio
async def test_check_permission(db: AsyncSession):
    """Test permission checking with error messages"""
    security_service = PMWorkflowSecurityService(db)
    
    # Authorized action
    authorized, error = security_service.check_permission("planner1", PMWorkflowPermission.CREATE_ORDER)
    assert authorized is True
    assert error is None
    
    # Unauthorized action
    authorized, error = security_service.check_permission("planner1", PMWorkflowPermission.RELEASE_ORDER)
    assert authorized is False
    assert "does not have permission" in error


@pytest.mark.asyncio
async def test_can_access_screen(db: AsyncSession):
    """Test screen access control"""
    security_service = PMWorkflowSecurityService(db)
    
    # Planner can access Screen 1 (planning)
    can_access, error = security_service.can_access_screen("planner1", 1)
    assert can_access is True
    assert error is None
    
    # Planner cannot access Screen 3 (release)
    can_access, error = security_service.can_access_screen("planner1", 3)
    assert can_access is False
    assert "does not have access" in error
    
    # Supervisor can access Screen 3
    can_access, error = security_service.can_access_screen("supervisor1", 3)
    assert can_access is True
    
    # Technician can access Screen 5 (execution)
    can_access, error = security_service.can_access_screen("tech1", 5)
    assert can_access is True
    
    # Admin can access all screens
    for screen_num in range(1, 7):
        can_access, error = security_service.can_access_screen("admin", screen_num)
        assert can_access is True


@pytest.mark.asyncio
async def test_can_perform_state_transition(db: AsyncSession):
    """Test state transition authorization"""
    security_service = PMWorkflowSecurityService(db)
    
    # Planner can transition Created -> Planned
    can_transition, error = security_service.can_perform_state_transition(
        "planner1",
        WorkflowOrderStatus.CREATED,
        WorkflowOrderStatus.PLANNED
    )
    assert can_transition is True
    
    # Planner cannot transition Planned -> Released
    can_transition, error = security_service.can_perform_state_transition(
        "planner1",
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED
    )
    assert can_transition is False
    
    # Supervisor can transition Planned -> Released
    can_transition, error = security_service.can_perform_state_transition(
        "supervisor1",
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED
    )
    assert can_transition is True
    
    # Technician can transition Released -> InProgress
    can_transition, error = security_service.can_perform_state_transition(
        "tech1",
        WorkflowOrderStatus.RELEASED,
        WorkflowOrderStatus.IN_PROGRESS
    )
    assert can_transition is True


@pytest.mark.asyncio
async def test_can_override_release_blocks(db: AsyncSession):
    """Test override authorization"""
    security_service = PMWorkflowSecurityService(db)
    
    # Planner cannot override blocks
    can_override, error = security_service.can_override_release_blocks("planner1")
    assert can_override is False
    
    # Supervisor can override blocks
    can_override, error = security_service.can_override_release_blocks("supervisor1")
    assert can_override is True
    
    # Admin can override blocks
    can_override, error = security_service.can_override_release_blocks("admin")
    assert can_override is True


@pytest.mark.asyncio
async def test_create_audit_log(db: AsyncSession):
    """Test audit log creation"""
    security_service = PMWorkflowSecurityService(db)
    
    # Should not raise exception
    await security_service.create_audit_log(
        order_number="PM-12345",
        user_id="planner1",
        action="create_order",
        details="Created new maintenance order",
        success=True
    )
    
    # Test failed action
    await security_service.create_audit_log(
        order_number="PM-12345",
        user_id="planner1",
        action="release_order",
        details="Unauthorized attempt",
        success=False
    )


@pytest.mark.asyncio
async def test_get_user_info(db: AsyncSession):
    """Test getting user information"""
    security_service = PMWorkflowSecurityService(db)
    
    # Test planner info
    user_info = security_service.get_user_info("planner1")
    assert user_info["user_id"] == "planner1"
    assert "planner" in user_info["roles"]
    assert "create_order" in user_info["permissions"]
    assert user_info["is_admin"] is False
    
    # Test admin info
    user_info = security_service.get_user_info("admin")
    assert user_info["is_admin"] is True
    assert len(user_info["permissions"]) > 5  # Admin has many permissions


@pytest.mark.asyncio
async def test_role_permission_mapping(db: AsyncSession):
    """Test that role-permission mapping is correct"""
    security_service = PMWorkflowSecurityService(db)
    
    # Warehouse role should have GR/GI permissions
    perms = security_service.get_user_permissions("warehouse1")
    assert PMWorkflowPermission.POST_GR in perms
    assert PMWorkflowPermission.POST_GI in perms
    assert PMWorkflowPermission.CREATE_ORDER not in perms
    
    # Controller role should have cost permissions
    perms = security_service.get_user_permissions("controller1")
    assert PMWorkflowPermission.VIEW_COSTS in perms
    assert PMWorkflowPermission.SETTLE_COSTS in perms
    assert PMWorkflowPermission.POST_GI not in perms
