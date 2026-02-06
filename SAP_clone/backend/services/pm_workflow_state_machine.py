"""
State Machine Engine for PM Workflow
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""
from typing import Dict, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass
from backend.models.pm_workflow_models import WorkflowOrderStatus


@dataclass
class StateTransition:
    """Represents a state transition with prerequisites"""
    from_state: WorkflowOrderStatus
    to_state: WorkflowOrderStatus
    prerequisites: List[Callable]
    actions: List[Callable]


class WorkflowStateMachine:
    """
    State machine for PM workflow orders.
    Requirement 10.1 - Define discrete states
    Requirement 10.2 - Validate prerequisites for transitions
    Requirement 10.3 - Prevent invalid transitions
    Requirement 10.4 - Execute business logic on transitions
    Requirement 10.5 - Enable/disable actions based on state
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS: Dict[WorkflowOrderStatus, Set[WorkflowOrderStatus]] = {
        WorkflowOrderStatus.CREATED: {WorkflowOrderStatus.PLANNED},
        WorkflowOrderStatus.PLANNED: {WorkflowOrderStatus.RELEASED},
        WorkflowOrderStatus.RELEASED: {WorkflowOrderStatus.IN_PROGRESS},
        WorkflowOrderStatus.IN_PROGRESS: {WorkflowOrderStatus.CONFIRMED},
        WorkflowOrderStatus.CONFIRMED: {WorkflowOrderStatus.TECO},
        WorkflowOrderStatus.TECO: set(),  # Terminal state
    }
    
    def __init__(self):
        """Initialize the state machine"""
        self.transition_prerequisites: Dict[tuple, List[Callable]] = {}
        self.transition_actions: Dict[tuple, List[Callable]] = {}
        self._setup_default_prerequisites()
    
    def _setup_default_prerequisites(self):
        """Set up default prerequisites for state transitions"""
        # Created → Planned: Must have operations and components
        self.add_prerequisite(
            WorkflowOrderStatus.CREATED,
            WorkflowOrderStatus.PLANNED,
            self._check_has_operations
        )
        self.add_prerequisite(
            WorkflowOrderStatus.CREATED,
            WorkflowOrderStatus.PLANNED,
            self._check_has_cost_estimate
        )
        
        # Planned → Released: Must have permits and materials
        self.add_prerequisite(
            WorkflowOrderStatus.PLANNED,
            WorkflowOrderStatus.RELEASED,
            self._check_permits_approved
        )
        self.add_prerequisite(
            WorkflowOrderStatus.PLANNED,
            WorkflowOrderStatus.RELEASED,
            self._check_materials_available
        )
        self.add_prerequisite(
            WorkflowOrderStatus.PLANNED,
            WorkflowOrderStatus.RELEASED,
            self._check_technician_assigned
        )
        
        # Released → In Progress: First confirmation posted
        self.add_prerequisite(
            WorkflowOrderStatus.RELEASED,
            WorkflowOrderStatus.IN_PROGRESS,
            self._check_has_confirmation
        )
        
        # In Progress → Confirmed: All operations confirmed
        self.add_prerequisite(
            WorkflowOrderStatus.IN_PROGRESS,
            WorkflowOrderStatus.CONFIRMED,
            self._check_all_operations_confirmed
        )
        
        # Confirmed → TECO: All operations confirmed and all goods issued
        self.add_prerequisite(
            WorkflowOrderStatus.CONFIRMED,
            WorkflowOrderStatus.TECO,
            self._check_all_operations_confirmed
        )
        self.add_prerequisite(
            WorkflowOrderStatus.CONFIRMED,
            WorkflowOrderStatus.TECO,
            self._check_all_goods_issued
        )
    
    def can_transition(
        self,
        from_state: WorkflowOrderStatus,
        to_state: WorkflowOrderStatus,
        order_data: Dict
    ) -> tuple[bool, List[str]]:
        """
        Check if a state transition is valid.
        
        Requirement 10.2 - Validate all prerequisites for transition
        Requirement 10.3 - Prevent transition if prerequisites not met
        
        Args:
            from_state: Current state
            to_state: Target state
            order_data: Order data for prerequisite checking
            
        Returns:
            Tuple of (can_transition, blocking_reasons)
        """
        # Check if transition is structurally valid
        if to_state not in self.VALID_TRANSITIONS.get(from_state, set()):
            return False, [f"Invalid transition from {from_state.value} to {to_state.value}"]
        
        # Check all prerequisites
        blocking_reasons = []
        prerequisites = self.transition_prerequisites.get((from_state, to_state), [])
        
        for prerequisite in prerequisites:
            is_met, reason = prerequisite(order_data)
            if not is_met:
                blocking_reasons.append(reason)
        
        return len(blocking_reasons) == 0, blocking_reasons
    
    def transition(
        self,
        from_state: WorkflowOrderStatus,
        to_state: WorkflowOrderStatus,
        order_data: Dict
    ) -> tuple[bool, Optional[str]]:
        """
        Execute a state transition.
        
        Requirement 10.4 - Execute associated business logic
        
        Args:
            from_state: Current state
            to_state: Target state
            order_data: Order data
            
        Returns:
            Tuple of (success, error_message)
        """
        # Validate transition
        can_transition, blocking_reasons = self.can_transition(from_state, to_state, order_data)
        
        if not can_transition:
            return False, "; ".join(blocking_reasons)
        
        # Execute transition actions
        actions = self.transition_actions.get((from_state, to_state), [])
        for action in actions:
            try:
                action(order_data)
            except Exception as e:
                return False, f"Action failed: {str(e)}"
        
        return True, None
    
    def get_valid_next_states(
        self,
        current_state: WorkflowOrderStatus
    ) -> Set[WorkflowOrderStatus]:
        """
        Get valid next states from current state.
        
        Requirement 10.5 - Enable only valid actions for state
        
        Args:
            current_state: Current state
            
        Returns:
            Set of valid next states
        """
        return self.VALID_TRANSITIONS.get(current_state, set())
    
    def get_enabled_actions(
        self,
        current_state: WorkflowOrderStatus
    ) -> List[str]:
        """
        Get enabled actions for current state.
        
        Requirement 10.5 - Enable only valid actions for state
        
        Args:
            current_state: Current state
            
        Returns:
            List of enabled action names
        """
        action_map = {
            WorkflowOrderStatus.CREATED: [
                "add_operation",
                "add_component",
                "estimate_costs",
                "request_permit",
                "transition_to_planned"
            ],
            WorkflowOrderStatus.PLANNED: [
                "create_purchase_order",
                "view_procurement_status",
                "transition_to_released"
            ],
            WorkflowOrderStatus.RELEASED: [
                "record_goods_receipt",
                "record_service_entry",
                "issue_goods",
                "confirm_work",
                "report_malfunction"
            ],
            WorkflowOrderStatus.IN_PROGRESS: [
                "issue_goods",
                "confirm_work",
                "report_malfunction"
            ],
            WorkflowOrderStatus.CONFIRMED: [
                "view_costs",
                "view_document_flow",
                "technical_complete"
            ],
            WorkflowOrderStatus.TECO: [
                "view_costs",
                "view_document_flow",
                "generate_report"
            ]
        }
        return action_map.get(current_state, [])
    
    def add_prerequisite(
        self,
        from_state: WorkflowOrderStatus,
        to_state: WorkflowOrderStatus,
        prerequisite: Callable
    ):
        """Add a prerequisite check for a transition"""
        key = (from_state, to_state)
        if key not in self.transition_prerequisites:
            self.transition_prerequisites[key] = []
        self.transition_prerequisites[key].append(prerequisite)
    
    def add_action(
        self,
        from_state: WorkflowOrderStatus,
        to_state: WorkflowOrderStatus,
        action: Callable
    ):
        """Add an action to execute on transition"""
        key = (from_state, to_state)
        if key not in self.transition_actions:
            self.transition_actions[key] = []
        self.transition_actions[key].append(action)
    
    # Prerequisite check functions
    
    @staticmethod
    def _check_has_operations(order_data: Dict) -> tuple[bool, str]:
        """Check if order has at least one operation"""
        operations = order_data.get("operations", [])
        if len(operations) == 0:
            return False, "Order must have at least one operation"
        return True, ""
    
    @staticmethod
    def _check_has_cost_estimate(order_data: Dict) -> tuple[bool, str]:
        """Check if order has cost estimate"""
        cost_summary = order_data.get("cost_summary")
        if not cost_summary or cost_summary.get("estimated_total_cost", 0) == 0:
            return False, "Order must have cost estimate"
        return True, ""
    
    @staticmethod
    def _check_permits_approved(order_data: Dict) -> tuple[bool, str]:
        """Check if all required permits are approved"""
        # For breakdown orders, reduced validation
        if order_data.get("order_type") == "breakdown":
            return True, ""
        
        permits = order_data.get("permits", [])
        required_permits = [p for p in permits if p.get("required", False)]
        
        if not required_permits:
            return True, ""
        
        unapproved = [p for p in required_permits if not p.get("approved", False)]
        if unapproved:
            return False, f"{len(unapproved)} required permit(s) not approved"
        return True, ""
    
    @staticmethod
    def _check_materials_available(order_data: Dict) -> tuple[bool, str]:
        """Check if critical materials are available"""
        # For breakdown orders, reduced validation
        if order_data.get("order_type") == "breakdown":
            return True, ""
        
        components = order_data.get("components", [])
        critical_components = [c for c in components if c.get("critical", False)]
        
        if not critical_components:
            return True, ""
        
        unavailable = [
            c for c in critical_components
            if not c.get("available", False) and not c.get("on_order", False)
        ]
        
        if unavailable:
            return False, f"{len(unavailable)} critical material(s) not available"
        return True, ""
    
    @staticmethod
    def _check_technician_assigned(order_data: Dict) -> tuple[bool, str]:
        """Check if at least one technician is assigned"""
        operations = order_data.get("operations", [])
        assigned = any(op.get("technician_id") for op in operations)
        if not assigned:
            return False, "At least one operation must have a technician assigned"
        return True, ""
    
    @staticmethod
    def _check_has_confirmation(order_data: Dict) -> tuple[bool, str]:
        """Check if order has at least one confirmation"""
        confirmations = order_data.get("confirmations", [])
        if len(confirmations) == 0:
            return False, "Order must have at least one confirmation to be in progress"
        return True, ""
    
    @staticmethod
    def _check_all_operations_confirmed(order_data: Dict) -> tuple[bool, str]:
        """Check if all operations are confirmed"""
        operations = order_data.get("operations", [])
        if not operations:
            return False, "Order must have operations"
        
        unconfirmed = [op for op in operations if op.get("status") != "confirmed"]
        if unconfirmed:
            return False, f"{len(unconfirmed)} operation(s) not confirmed"
        return True, ""
    
    @staticmethod
    def _check_all_goods_issued(order_data: Dict) -> tuple[bool, str]:
        """Check if all required goods are issued"""
        components = order_data.get("components", [])
        if not components:
            return True, ""
        
        not_issued = [
            c for c in components
            if c.get("quantity_required", 0) > c.get("quantity_issued", 0)
        ]
        
        if not_issued:
            return False, f"{len(not_issued)} component(s) not fully issued"
        return True, ""


# Singleton instance
_state_machine = None


def get_state_machine() -> WorkflowStateMachine:
    """Get the singleton state machine instance"""
    global _state_machine
    if _state_machine is None:
        _state_machine = WorkflowStateMachine()
    return _state_machine
