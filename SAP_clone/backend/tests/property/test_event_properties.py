"""
Property-based tests for event emission with correlation.
**Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
**Validates: Requirements 2.4, 3.4, 4.5, 5.2, 6.3**
"""
import uuid
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

from backend.services.event_service import (
    Event, EventType, EventService,
    validate_event_type_prefix, get_event_module,
)


# Strategies for generating test data
event_type_strategy = st.sampled_from(list(EventType))
correlation_id_strategy = st.uuids().map(str)
payload_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    values=st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
    ),
    min_size=1,
    max_size=10,
)


@settings(max_examples=100)
@given(
    event_type=event_type_strategy,
    payload=payload_strategy,
    correlation_id=correlation_id_strategy
)
def test_event_has_unique_event_id(event_type: EventType, payload: dict, correlation_id: str):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 5.2**
    
    Property: For any event creation, the emitted event SHALL have a unique event_id.
    """
    event = Event(event_type=event_type, payload=payload, correlation_id=correlation_id)
    
    # Verify event_id is a valid UUID
    assert event.event_id is not None, "event_id should not be None"
    try:
        uuid.UUID(event.event_id)
    except ValueError:
        assert False, f"event_id '{event.event_id}' is not a valid UUID"


@settings(max_examples=100)
@given(
    event_type=event_type_strategy,
    payload=payload_strategy,
    correlation_id=correlation_id_strategy
)
def test_event_preserves_correlation_id(event_type: EventType, payload: dict, correlation_id: str):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 6.3**
    
    Property: For any event creation with a correlation_id, the event SHALL preserve
    that correlation_id in the emitted event.
    """
    event = Event(event_type=event_type, payload=payload, correlation_id=correlation_id)
    
    assert event.correlation_id == correlation_id, (
        f"correlation_id mismatch: expected {correlation_id}, got {event.correlation_id}"
    )


@settings(max_examples=100)
@given(
    event_type=event_type_strategy,
    payload=payload_strategy
)
def test_event_generates_correlation_id_if_missing(event_type: EventType, payload: dict):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 6.3**
    
    Property: For any event creation without a correlation_id, the system SHALL
    generate a valid correlation_id.
    """
    event = Event(event_type=event_type, payload=payload, correlation_id=None)
    
    assert event.correlation_id is not None, "correlation_id should be generated"
    try:
        uuid.UUID(event.correlation_id)
    except ValueError:
        assert False, f"Generated correlation_id '{event.correlation_id}' is not a valid UUID"


@settings(max_examples=100)
@given(event_type=event_type_strategy)
def test_event_type_has_valid_prefix(event_type: EventType):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 2.4, 3.4, 4.5**
    
    Property: For any event type, it SHALL have a valid module prefix (PM_, MM_, FI_).
    """
    assert validate_event_type_prefix(event_type), (
        f"Event type '{event_type.value}' does not have a valid prefix"
    )
    
    # Verify prefix matches one of the expected modules
    module = get_event_module(event_type)
    assert module in {"PM", "MM", "FI"}, f"Invalid module: {module}"


@settings(max_examples=100)
@given(
    event_type=event_type_strategy,
    payload=payload_strategy,
    correlation_id=correlation_id_strategy
)
def test_event_timestamp_is_recent(event_type: EventType, payload: dict, correlation_id: str):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 5.2**
    
    Property: For any event creation, the timestamp SHALL be within acceptable
    tolerance of the operation time.
    """
    before = datetime.utcnow()
    event = Event(event_type=event_type, payload=payload, correlation_id=correlation_id)
    after = datetime.utcnow()
    
    # Timestamp should be between before and after (with small tolerance)
    tolerance = timedelta(seconds=1)
    assert before - tolerance <= event.timestamp <= after + tolerance, (
        f"Timestamp {event.timestamp} not within expected range [{before}, {after}]"
    )


@settings(max_examples=100)
@given(
    event_type=event_type_strategy,
    payload=payload_strategy,
    correlation_id=correlation_id_strategy
)
def test_event_to_dict_roundtrip(event_type: EventType, payload: dict, correlation_id: str):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 5.2**
    
    Property: For any event, converting to dict and back SHALL preserve all fields.
    """
    original = Event(event_type=event_type, payload=payload, correlation_id=correlation_id)
    event_dict = original.to_dict()
    
    # Verify all required fields are present
    assert "event_id" in event_dict, "event_id missing from dict"
    assert "event_type" in event_dict, "event_type missing from dict"
    assert "correlation_id" in event_dict, "correlation_id missing from dict"
    assert "timestamp" in event_dict, "timestamp missing from dict"
    assert "payload" in event_dict, "payload missing from dict"
    
    # Verify values match
    assert event_dict["event_id"] == original.event_id
    assert event_dict["event_type"] == original.event_type.value
    assert event_dict["correlation_id"] == original.correlation_id
    assert event_dict["payload"] == original.payload


@settings(max_examples=100)
@given(event_type=event_type_strategy)
def test_event_type_prefix_matches_module(event_type: EventType):
    """
    **Feature: sap-erp-demo, Property 10: Event Emission with Correlation**
    **Validates: Requirements 2.4, 3.4, 4.5**
    
    Property: For any event type, the prefix SHALL correctly identify the source module.
    """
    module = get_event_module(event_type)
    
    # Verify the event type starts with the module prefix
    assert event_type.value.startswith(f"{module}_"), (
        f"Event type '{event_type.value}' should start with '{module}_'"
    )
