#!/usr/bin/env python3
"""
DBBasic State Machine & Workflow Engine
Configuration-driven state transitions and business process automation
"""

import yaml
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

class TransitionResult(Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    ERROR = "error"
    PERMISSION_DENIED = "permission_denied"

@dataclass
class StateTransition:
    from_state: str
    to_state: str
    conditions: List[str]
    actions: List[str]
    permissions: List[str]
    metadata: Dict[str, Any]

@dataclass
class WorkflowEvent:
    entity_id: str
    entity_type: str
    from_state: str
    to_state: str
    user_id: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime

class StateMachine:
    """Configuration-driven state machine for business workflows"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.states = config.get('states', {})
        self.initial_state = config.get('initial_state', 'pending')
        self.final_states = set(config.get('final_states', []))
        self.transitions = self._build_transition_map()
        self.global_conditions = config.get('global_conditions', {})

    def _build_transition_map(self) -> Dict[str, List[StateTransition]]:
        """Build transition map from configuration"""
        transitions = {}

        for state_name, state_config in self.states.items():
            state_transitions = []

            for target_state in state_config.get('transitions', []):
                transition = StateTransition(
                    from_state=state_name,
                    to_state=target_state,
                    conditions=state_config.get('conditions', []),
                    actions=state_config.get('actions', []),
                    permissions=state_config.get('permissions', []),
                    metadata=state_config.get('metadata', {})
                )
                state_transitions.append(transition)

            transitions[state_name] = state_transitions

        return transitions

    def get_valid_transitions(self, current_state: str) -> List[str]:
        """Get list of valid next states from current state"""
        if current_state not in self.transitions:
            return []
        return [t.to_state for t in self.transitions[current_state]]

    def can_transition(self, from_state: str, to_state: str,
                      context: Dict[str, Any] = None) -> bool:
        """Check if transition is valid and conditions are met"""
        if from_state not in self.transitions:
            return False

        valid_transitions = [t for t in self.transitions[from_state]
                           if t.to_state == to_state]
        if not valid_transitions:
            return False

        transition = valid_transitions[0]
        context = context or {}

        # Check conditions
        for condition in transition.conditions:
            if not self._evaluate_condition(condition, context):
                return False

        return True

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context"""
        # Simple condition evaluation - can be expanded with more complex logic
        if condition.startswith('field_'):
            field_name = condition[6:]  # Remove 'field_' prefix
            return context.get(field_name) is not None

        if condition.startswith('user_role_'):
            required_role = condition[10:]  # Remove 'user_role_' prefix
            user_roles = context.get('user_roles', [])
            return required_role in user_roles

        if condition.startswith('value_'):
            # Format: value_field_name_operator_value (e.g., value_amount_gt_1000)
            parts = condition.split('_')
            if len(parts) >= 4:
                field_name = parts[1]
                operator = parts[2]
                expected_value = '_'.join(parts[3:])

                field_value = context.get(field_name)
                if field_value is None:
                    return False

                if operator == 'eq':
                    return str(field_value) == expected_value
                elif operator == 'gt':
                    return float(field_value) > float(expected_value)
                elif operator == 'lt':
                    return float(field_value) < float(expected_value)

        return True  # Default to allow if condition not recognized

class WorkflowEngine:
    """Manages multiple state machines and workflow execution"""

    def __init__(self):
        self.state_machines: Dict[str, StateMachine] = {}
        self.event_handlers = []
        self.workflow_history: List[WorkflowEvent] = []

    def register_state_machine(self, name: str, config: Dict[str, Any]):
        """Register a state machine from configuration"""
        self.state_machines[name] = StateMachine(config)
        logger.info(f"📋 Registered state machine: {name}")

    def load_from_config(self, config_path: str):
        """Load workflow configurations from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for workflow_name, workflow_config in config.get('workflows', {}).items():
            self.register_state_machine(workflow_name, workflow_config)

    async def transition(self, entity_type: str, entity_id: str,
                        from_state: str, to_state: str,
                        context: Dict[str, Any] = None,
                        user_id: str = None) -> TransitionResult:
        """Execute a state transition with all validations and actions"""

        if entity_type not in self.state_machines:
            logger.error(f"No state machine found for entity type: {entity_type}")
            return TransitionResult.ERROR

        state_machine = self.state_machines[entity_type]
        context = context or {}

        # Validate transition
        if not state_machine.can_transition(from_state, to_state, context):
            logger.warning(f"Transition blocked: {entity_type}#{entity_id} {from_state} -> {to_state}")
            return TransitionResult.BLOCKED

        # Get transition config
        transition = None
        for t in state_machine.transitions.get(from_state, []):
            if t.to_state == to_state:
                transition = t
                break

        if not transition:
            return TransitionResult.ERROR

        # Check permissions
        if transition.permissions and user_id:
            user_roles = context.get('user_roles', [])
            if not any(role in transition.permissions for role in user_roles):
                logger.warning(f"Permission denied: {user_id} cannot transition {entity_type}#{entity_id}")
                return TransitionResult.PERMISSION_DENIED

        # Execute pre-transition actions
        try:
            await self._execute_actions(transition.actions, 'before', context)

            # Record the transition event
            event = WorkflowEvent(
                entity_id=entity_id,
                entity_type=entity_type,
                from_state=from_state,
                to_state=to_state,
                user_id=user_id,
                metadata=context,
                timestamp=datetime.now()
            )
            self.workflow_history.append(event)

            # Execute post-transition actions
            await self._execute_actions(transition.actions, 'after', context)

            # Notify event handlers
            for handler in self.event_handlers:
                await handler(event)

            logger.info(f"✅ Transition successful: {entity_type}#{entity_id} {from_state} -> {to_state}")
            return TransitionResult.SUCCESS

        except Exception as e:
            logger.error(f"Transition failed: {e}")
            return TransitionResult.ERROR

    async def _execute_actions(self, actions: List[str], phase: str,
                             context: Dict[str, Any]):
        """Execute workflow actions (hooks to AI Service Builder)"""
        for action in actions:
            if action.startswith(f'{phase}_'):
                action_name = action[len(f'{phase}_'):]
                await self._call_ai_service(action_name, context)

    async def _call_ai_service(self, action_name: str, context: Dict[str, Any]):
        """Call AI Service Builder to execute business logic"""
        try:
            # This would integrate with the AI Service Builder
            logger.info(f"🤖 Executing AI action: {action_name}")
            # Placeholder for AI service integration
            pass
        except Exception as e:
            logger.error(f"AI action failed: {action_name} - {e}")

    def get_workflow_history(self, entity_type: str = None,
                           entity_id: str = None) -> List[WorkflowEvent]:
        """Get workflow history with optional filtering"""
        history = self.workflow_history

        if entity_type:
            history = [e for e in history if e.entity_type == entity_type]
        if entity_id:
            history = [e for e in history if e.entity_id == entity_id]

        return sorted(history, key=lambda x: x.timestamp, reverse=True)

    def get_entity_state_info(self, entity_type: str, current_state: str) -> Dict[str, Any]:
        """Get information about current state and possible transitions"""
        if entity_type not in self.state_machines:
            return {}

        state_machine = self.state_machines[entity_type]
        valid_transitions = state_machine.get_valid_transitions(current_state)

        state_config = state_machine.states.get(current_state, {})

        return {
            'current_state': current_state,
            'valid_transitions': valid_transitions,
            'is_final_state': current_state in state_machine.final_states,
            'state_metadata': state_config.get('metadata', {}),
            'required_permissions': state_config.get('permissions', []),
            'actions': state_config.get('actions', [])
        }

# Global workflow engine instance
workflow_engine = WorkflowEngine()

def get_workflow_engine() -> WorkflowEngine:
    """Get global workflow engine instance"""
    return workflow_engine

# Example configuration for e-commerce order workflow
ECOMMERCE_WORKFLOW_CONFIG = {
    'workflows': {
        'orders': {
            'initial_state': 'pending',
            'final_states': ['delivered', 'cancelled', 'refunded'],
            'states': {
                'pending': {
                    'transitions': ['confirmed', 'cancelled'],
                    'permissions': ['customer', 'sales_rep', 'admin'],
                    'actions': ['before_validate_order', 'after_send_confirmation'],
                    'metadata': {'description': 'Order awaiting confirmation'}
                },
                'confirmed': {
                    'transitions': ['processing', 'cancelled'],
                    'permissions': ['sales_rep', 'admin'],
                    'conditions': ['field_payment_authorized'],
                    'actions': ['before_authorize_payment', 'after_reserve_inventory'],
                    'metadata': {'description': 'Order confirmed and payment authorized'}
                },
                'processing': {
                    'transitions': ['shipped', 'cancelled'],
                    'permissions': ['fulfillment_team', 'admin'],
                    'conditions': ['field_inventory_reserved'],
                    'actions': ['before_pick_items', 'after_generate_shipping_label'],
                    'metadata': {'description': 'Order being processed for shipment'}
                },
                'shipped': {
                    'transitions': ['delivered'],
                    'permissions': ['carrier_webhook', 'admin'],
                    'actions': ['before_update_tracking', 'after_send_tracking_info'],
                    'metadata': {'description': 'Order shipped to customer'}
                },
                'delivered': {
                    'transitions': ['refunded'],
                    'permissions': ['carrier_webhook', 'customer_confirmation', 'admin'],
                    'actions': ['after_request_review', 'after_update_analytics'],
                    'metadata': {'description': 'Order successfully delivered'}
                },
                'cancelled': {
                    'transitions': [],
                    'permissions': ['customer_if_early', 'admin'],
                    'actions': ['after_process_refund', 'after_restore_inventory'],
                    'metadata': {'description': 'Order cancelled'}
                },
                'refunded': {
                    'transitions': [],
                    'permissions': ['admin'],
                    'actions': ['after_process_refund_payment'],
                    'metadata': {'description': 'Order refunded'}
                }
            }
        },
        'leads': {
            'initial_state': 'new',
            'final_states': ['won', 'lost'],
            'states': {
                'new': {
                    'transitions': ['contacted', 'lost'],
                    'permissions': ['sales_rep', 'admin'],
                    'actions': ['after_assign_lead_automatically']
                },
                'contacted': {
                    'transitions': ['qualified', 'lost'],
                    'permissions': ['sales_rep', 'admin'],
                    'actions': ['before_log_contact_attempt']
                },
                'qualified': {
                    'transitions': ['proposal', 'lost'],
                    'permissions': ['sales_rep', 'admin'],
                    'conditions': ['field_budget_confirmed', 'field_decision_maker_identified']
                },
                'proposal': {
                    'transitions': ['negotiation', 'lost'],
                    'permissions': ['sales_rep', 'admin'],
                    'actions': ['before_generate_proposal', 'after_schedule_follow_up']
                },
                'negotiation': {
                    'transitions': ['won', 'lost'],
                    'permissions': ['sales_rep', 'admin'],
                    'conditions': ['value_probability_gt_50']
                },
                'won': {
                    'transitions': [],
                    'permissions': ['sales_rep', 'admin'],
                    'actions': ['after_create_customer_record', 'after_update_sales_metrics']
                },
                'lost': {
                    'transitions': [],
                    'permissions': ['sales_rep', 'admin'],
                    'actions': ['after_analyze_loss_reason', 'after_update_pipeline_metrics']
                }
            }
        }
    }
}

if __name__ == "__main__":
    # Example usage
    import tempfile
    import os

    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(ECOMMERCE_WORKFLOW_CONFIG, f)
        config_path = f.name

    try:
        # Initialize workflow engine
        engine = get_workflow_engine()
        engine.load_from_config(config_path)

        # Example workflow execution
        async def test_workflow():
            # Test order workflow
            context = {
                'payment_authorized': True,
                'inventory_reserved': True,
                'user_roles': ['sales_rep']
            }

            # Transition from pending to confirmed
            result = await engine.transition(
                entity_type='orders',
                entity_id='ORD-001',
                from_state='pending',
                to_state='confirmed',
                context=context,
                user_id='user123'
            )

            print(f"Transition result: {result}")

            # Get state info
            info = engine.get_entity_state_info('orders', 'confirmed')
            print(f"State info: {json.dumps(info, indent=2)}")

            # Get history
            history = engine.get_workflow_history('orders', 'ORD-001')
            print(f"Workflow history: {len(history)} events")

        asyncio.run(test_workflow())

    finally:
        os.unlink(config_path)