"""
Property-based tests for authentication and authorization.
**Feature: sap-erp-demo, Property 11: JWT Token Structure**
**Feature: sap-erp-demo, Property 12: Role-Based Access Control**
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**
"""
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

from backend.services.auth_service import (
    AuthService, Role, Module, TokenPayload,
    ROLE_MODULE_ACCESS, get_accessible_modules, is_admin,
)


# Strategies for generating test data
role_strategy = st.sampled_from(list(Role))
roles_strategy = st.lists(role_strategy, min_size=1, max_size=4, unique=True)
module_strategy = st.sampled_from(list(Module))
user_id_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    roles=roles_strategy
)
def test_jwt_contains_user_id(user_id: str, roles: list):
    """
    **Feature: sap-erp-demo, Property 11: JWT Token Structure**
    **Validates: Requirements 7.1**
    
    Property: For any successful authentication, the issued JWT token SHALL contain
    a valid user_id claim.
    """
    auth_service = AuthService(secret_key="test-secret-key")
    token = auth_service.create_token(user_id=user_id, roles=roles)
    
    # Decode and verify
    decoded = auth_service.decode_token_without_validation(token)
    
    assert "user_id" in decoded, "user_id claim missing from token"
    assert decoded["user_id"] == user_id, f"user_id mismatch: expected {user_id}, got {decoded['user_id']}"


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    roles=roles_strategy
)
def test_jwt_contains_roles(user_id: str, roles: list):
    """
    **Feature: sap-erp-demo, Property 11: JWT Token Structure**
    **Validates: Requirements 7.1**
    
    Property: For any successful authentication, the issued JWT token SHALL contain
    a roles claim with at least one valid role.
    """
    auth_service = AuthService(secret_key="test-secret-key")
    token = auth_service.create_token(user_id=user_id, roles=roles)
    
    # Decode and verify
    decoded = auth_service.decode_token_without_validation(token)
    
    assert "roles" in decoded, "roles claim missing from token"
    assert len(decoded["roles"]) >= 1, "roles claim should have at least one role"
    
    # Verify all roles are valid
    valid_role_values = {r.value for r in Role}
    for role in decoded["roles"]:
        assert role in valid_role_values, f"Invalid role in token: {role}"


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    roles=roles_strategy
)
def test_jwt_contains_future_expiration(user_id: str, roles: list):
    """
    **Feature: sap-erp-demo, Property 11: JWT Token Structure**
    **Validates: Requirements 7.1**
    
    Property: For any successful authentication, the issued JWT token SHALL contain
    an exp claim set to a future timestamp.
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    before = datetime.utcnow()
    token = auth_service.create_token(user_id=user_id, roles=roles)
    
    # Decode and verify
    decoded = auth_service.decode_token_without_validation(token)
    
    assert "exp" in decoded, "exp claim missing from token"
    
    exp_timestamp = decoded["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    
    # Expiration should be in the future
    assert exp_datetime > before, f"exp {exp_datetime} should be after {before}"


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    roles=roles_strategy
)
def test_jwt_roundtrip(user_id: str, roles: list):
    """
    **Feature: sap-erp-demo, Property 11: JWT Token Structure**
    **Validates: Requirements 7.1**
    
    Property: For any JWT token, decoding and re-encoding the token payload
    SHALL produce equivalent claims.
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    token = auth_service.create_token(user_id=user_id, roles=roles)
    
    # Decode without validation (to avoid expiration issues in tests)
    decoded = auth_service.decode_token_without_validation(token)
    payload = TokenPayload.from_dict(decoded)
    
    # Verify payload matches input
    assert payload.user_id == user_id, "user_id mismatch after roundtrip"
    assert set(payload.roles) == set(roles), "roles mismatch after roundtrip"



# Property 12: Role-Based Access Control


@settings(max_examples=100)
@given(role=role_strategy)
def test_role_has_defined_module_access(role: Role):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.3, 7.4, 7.5, 7.6**
    
    Property: For any role, there SHALL be a defined set of accessible modules.
    """
    assert role in ROLE_MODULE_ACCESS, f"Role {role} has no defined module access"
    
    modules = ROLE_MODULE_ACCESS[role]
    assert isinstance(modules, set), "Module access should be a set"


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    role=role_strategy,
    module=module_strategy
)
def test_rbac_access_control(user_id: str, role: Role, module: Module):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.2, 7.3, 7.4, 7.5, 7.6**
    
    Property: For any user with a specific role and any module, access SHALL be:
    - Granted if the role is authorized for that module
    - Denied if the role is not authorized
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    token = auth_service.create_token(user_id=user_id, roles=[role])
    
    # Check access (skip expiration for testing)
    has_access = auth_service.check_module_access(token, module, skip_expiration=True)
    
    # Verify against expected access
    expected_access = module in ROLE_MODULE_ACCESS.get(role, set())
    
    assert has_access == expected_access, (
        f"Access mismatch for role {role.value} to module {module.value}: "
        f"expected {expected_access}, got {has_access}"
    )


@settings(max_examples=100)
@given(user_id=user_id_strategy)
def test_maintenance_engineer_access(user_id: str):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.3**
    
    Property: When a user has role Maintenance_Engineer, the system SHALL grant
    access to PM_Module read and write operations.
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    token = auth_service.create_token(user_id=user_id, roles=[Role.MAINTENANCE_ENGINEER])
    
    # Should have PM access
    assert auth_service.check_module_access(token, Module.PM, skip_expiration=True), (
        "Maintenance_Engineer should have PM access"
    )
    
    # Should NOT have MM or FI access
    assert not auth_service.check_module_access(token, Module.MM, skip_expiration=True), (
        "Maintenance_Engineer should NOT have MM access"
    )
    assert not auth_service.check_module_access(token, Module.FI, skip_expiration=True), (
        "Maintenance_Engineer should NOT have FI access"
    )


@settings(max_examples=100)
@given(user_id=user_id_strategy)
def test_store_manager_access(user_id: str):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.4**
    
    Property: When a user has role Store_Manager, the system SHALL grant
    access to MM_Module read and write operations.
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    token = auth_service.create_token(user_id=user_id, roles=[Role.STORE_MANAGER])
    
    # Should have MM access
    assert auth_service.check_module_access(token, Module.MM, skip_expiration=True), (
        "Store_Manager should have MM access"
    )
    
    # Should NOT have PM or FI access
    assert not auth_service.check_module_access(token, Module.PM, skip_expiration=True), (
        "Store_Manager should NOT have PM access"
    )
    assert not auth_service.check_module_access(token, Module.FI, skip_expiration=True), (
        "Store_Manager should NOT have FI access"
    )


@settings(max_examples=100)
@given(user_id=user_id_strategy)
def test_finance_officer_access(user_id: str):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.5**
    
    Property: When a user has role Finance_Officer, the system SHALL grant
    access to FI_Module read and write operations.
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    token = auth_service.create_token(user_id=user_id, roles=[Role.FINANCE_OFFICER])
    
    # Should have FI access
    assert auth_service.check_module_access(token, Module.FI, skip_expiration=True), (
        "Finance_Officer should have FI access"
    )
    
    # Should NOT have PM or MM access
    assert not auth_service.check_module_access(token, Module.PM, skip_expiration=True), (
        "Finance_Officer should NOT have PM access"
    )
    assert not auth_service.check_module_access(token, Module.MM, skip_expiration=True), (
        "Finance_Officer should NOT have MM access"
    )


@settings(max_examples=100)
@given(
    user_id=user_id_strategy,
    module=module_strategy
)
def test_admin_has_all_access(user_id: str, module: Module):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.6**
    
    Property: When a user has role Admin, the system SHALL grant access
    to all modules and system configuration.
    """
    auth_service = AuthService(secret_key="test-secret-key", expiration_minutes=60)
    token = auth_service.create_token(user_id=user_id, roles=[Role.ADMIN])
    
    # Admin should have access to all modules
    assert auth_service.check_module_access(token, module, skip_expiration=True), (
        f"Admin should have access to {module.value}"
    )


@settings(max_examples=100)
@given(roles=roles_strategy)
def test_multiple_roles_combine_access(roles: list):
    """
    **Feature: sap-erp-demo, Property 12: Role-Based Access Control**
    **Validates: Requirements 7.3, 7.4, 7.5, 7.6**
    
    Property: For any user with multiple roles, accessible modules SHALL be
    the union of all role permissions.
    """
    # Calculate expected accessible modules
    expected_modules = get_accessible_modules(roles)
    
    # Verify each role contributes its modules
    for role in roles:
        role_modules = ROLE_MODULE_ACCESS.get(role, set())
        for module in role_modules:
            assert module in expected_modules, (
                f"Module {module} from role {role} should be in accessible modules"
            )
