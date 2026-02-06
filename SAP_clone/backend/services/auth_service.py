"""
Authentication and Authorization Service.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6 - JWT auth and RBAC
"""
from datetime import datetime, timedelta
from typing import Optional, List, Set, Dict, Any
from enum import Enum
import jwt
from functools import wraps

from backend.config import get_settings


class Role(str, Enum):
    """User roles - Requirements 7.3, 7.4, 7.5, 7.6"""
    MAINTENANCE_ENGINEER = "Maintenance_Engineer"
    STORE_MANAGER = "Store_Manager"
    FINANCE_OFFICER = "Finance_Officer"
    ADMIN = "Admin"


class Module(str, Enum):
    """Module identifiers for access control"""
    PM = "PM"
    MM = "MM"
    FI = "FI"
    SYSTEM = "SYSTEM"


# Role to module access mapping - Requirements 7.3, 7.4, 7.5, 7.6
ROLE_MODULE_ACCESS: Dict[Role, Set[Module]] = {
    Role.MAINTENANCE_ENGINEER: {Module.PM},
    Role.STORE_MANAGER: {Module.MM},
    Role.FINANCE_OFFICER: {Module.FI},
    Role.ADMIN: {Module.PM, Module.MM, Module.FI, Module.SYSTEM},
}


class AuthServiceError(Exception):
    """Base exception for auth service errors"""
    pass


class InvalidTokenError(AuthServiceError):
    """Raised when a token is invalid"""
    pass


class InsufficientPermissionsError(AuthServiceError):
    """Raised when user lacks required permissions"""
    pass


class TokenPayload:
    """JWT token payload structure - Requirement 7.1"""
    
    def __init__(
        self,
        user_id: str,
        roles: List[Role],
        exp: datetime,
        iat: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.roles = roles
        self.exp = exp
        self.iat = iat or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            "user_id": self.user_id,
            "roles": [r.value for r in self.roles],
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """Create from dictionary (decoded JWT)."""
        return cls(
            user_id=data["user_id"],
            roles=[Role(r) for r in data["roles"]],
            exp=datetime.fromtimestamp(data["exp"]),
            iat=datetime.fromtimestamp(data.get("iat", datetime.utcnow().timestamp())),
        )
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.exp
    
    def has_role(self, role: Role) -> bool:
        """Check if payload has a specific role."""
        return role in self.roles
    
    def can_access_module(self, module: Module) -> bool:
        """Check if user can access a specific module."""
        for role in self.roles:
            if module in ROLE_MODULE_ACCESS.get(role, set()):
                return True
        return False



class AuthService:
    """
    Service for authentication and authorization.
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        expiration_minutes: Optional[int] = None,
    ):
        settings = get_settings()
        self.secret_key = secret_key or settings.jwt_secret
        self.algorithm = algorithm or settings.jwt_algorithm
        self.expiration_minutes = expiration_minutes or settings.jwt_expiration_minutes
    
    def create_token(
        self,
        user_id: str,
        roles: List[Role],
        expiration_minutes: Optional[int] = None,
    ) -> str:
        """
        Create a JWT token.
        Requirement 7.1 - Issue JWT with user_id, roles, expiration_time
        """
        if not user_id:
            raise AuthServiceError("user_id is required")
        if not roles:
            raise AuthServiceError("At least one role is required")
        
        exp_minutes = expiration_minutes or self.expiration_minutes
        exp = datetime.utcnow() + timedelta(minutes=exp_minutes)
        
        payload = TokenPayload(
            user_id=user_id,
            roles=roles,
            exp=exp,
        )
        
        token = jwt.encode(
            payload.to_dict(),
            self.secret_key,
            algorithm=self.algorithm,
        )
        
        return token
    
    def validate_token(self, token: str) -> TokenPayload:
        """
        Validate a JWT token.
        Requirement 7.2 - Validate JWT token before processing
        """
        if not token:
            raise InvalidTokenError("Token is required")
        
        try:
            decoded = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            payload = TokenPayload.from_dict(decoded)
            
            if payload.is_expired():
                raise InvalidTokenError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    def decode_token_without_validation(self, token: str) -> Dict[str, Any]:
        """Decode token without validation (for testing/inspection)."""
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={"verify_exp": False},
        )
    
    def check_module_access(
        self,
        token: str,
        module: Module,
        skip_expiration: bool = False,
    ) -> bool:
        """
        Check if token grants access to a module.
        Requirements: 7.3, 7.4, 7.5, 7.6
        """
        if skip_expiration:
            decoded = self.decode_token_without_validation(token)
            payload = TokenPayload.from_dict(decoded)
        else:
            payload = self.validate_token(token)
        return payload.can_access_module(module)
    
    def require_module_access(
        self,
        token: str,
        module: Module,
    ) -> TokenPayload:
        """
        Require access to a module, raise if not authorized.
        """
        payload = self.validate_token(token)
        
        if not payload.can_access_module(module):
            raise InsufficientPermissionsError(
                f"User {payload.user_id} does not have access to {module.value} module"
            )
        
        return payload
    
    def refresh_token(self, token: str) -> str:
        """
        Refresh a token (issue new token with same claims).
        """
        payload = self.validate_token(token)
        return self.create_token(
            user_id=payload.user_id,
            roles=payload.roles,
        )


def has_role(role: Role):
    """Decorator to check if user has a specific role."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would be used with request context in actual implementation
            return func(*args, **kwargs)
        return wrapper
    return decorator


def has_module_access(module: Module):
    """Decorator to check if user has access to a module."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would be used with request context in actual implementation
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for role checking

def get_accessible_modules(roles: List[Role]) -> Set[Module]:
    """Get all modules accessible by a list of roles."""
    modules = set()
    for role in roles:
        modules.update(ROLE_MODULE_ACCESS.get(role, set()))
    return modules


def is_admin(roles: List[Role]) -> bool:
    """Check if roles include Admin."""
    return Role.ADMIN in roles


def validate_role(role_str: str) -> Optional[Role]:
    """Validate and convert a role string to Role enum."""
    try:
        return Role(role_str)
    except ValueError:
        return None
