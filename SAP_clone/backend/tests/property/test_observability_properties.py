"""
Property-based tests for observability features.
**Feature: sap-erp-demo, Property 13: Structured Log Format**
**Validates: Requirements 6.2**
"""
import json
from hypothesis import given, strategies as st, settings

from backend.services.observability import (
    StructuredLogger, LogLevel, validate_log_entry,
    get_correlation_id, set_correlation_id,
)


# Strategies for generating test data
log_level_strategy = st.sampled_from(list(LogLevel))
message_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
service_name_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.isalnum())


@settings(max_examples=100)
@given(
    level=log_level_strategy,
    message=message_strategy
)
def test_log_entry_has_required_fields(level: LogLevel, message: str):
    """
    **Feature: sap-erp-demo, Property 13: Structured Log Format**
    **Validates: Requirements 6.2**
    
    Property: For any API request processed by the system, the generated log entry SHALL:
    - Be valid JSON
    - Contain correlation_id, timestamp, service, and log_level fields
    """
    logger = StructuredLogger(service_name="test-service")
    entry = logger._create_log_entry(level, message)
    
    # Verify it's valid JSON
    json_str = json.dumps(entry)
    parsed = json.loads(json_str)
    
    # Verify required fields
    assert "correlation_id" in parsed, "correlation_id missing"
    assert "timestamp" in parsed, "timestamp missing"
    assert "service" in parsed, "service missing"
    assert "log_level" in parsed, "log_level missing"
    assert "message" in parsed, "message missing"


@settings(max_examples=100)
@given(level=log_level_strategy)
def test_log_level_is_valid(level: LogLevel):
    """
    **Feature: sap-erp-demo, Property 13: Structured Log Format**
    **Validates: Requirements 6.2**
    
    Property: For any log entry, log_level SHALL be from {DEBUG, INFO, WARNING, ERROR}.
    """
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
    assert level.value in valid_levels, f"Invalid log level: {level.value}"


@settings(max_examples=100)
@given(
    level=log_level_strategy,
    message=message_strategy
)
def test_log_entry_validation(level: LogLevel, message: str):
    """
    **Feature: sap-erp-demo, Property 13: Structured Log Format**
    **Validates: Requirements 6.2**
    
    Property: For any valid log entry, validate_log_entry SHALL return True.
    """
    logger = StructuredLogger(service_name="test-service")
    entry = logger._create_log_entry(level, message)
    
    assert validate_log_entry(entry), "Valid log entry should pass validation"


@settings(max_examples=100)
@given(
    level=log_level_strategy,
    message=message_strategy,
    extra_key=st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.isalnum()),
    extra_value=st.text(max_size=100)
)
def test_log_entry_with_extra_fields(level: LogLevel, message: str, extra_key: str, extra_value: str):
    """
    **Feature: sap-erp-demo, Property 13: Structured Log Format**
    **Validates: Requirements 6.2**
    
    Property: For any log entry with extra fields, the entry SHALL still be valid JSON
    and contain all required fields.
    """
    logger = StructuredLogger(service_name="test-service")
    entry = logger._create_log_entry(level, message, {extra_key: extra_value})
    
    # Verify it's valid JSON
    json_str = json.dumps(entry)
    parsed = json.loads(json_str)
    
    # Verify required fields still present
    assert validate_log_entry(parsed), "Log entry with extra fields should be valid"
    
    # Verify extra field is present
    if extra_key and extra_value:
        assert "extra" in parsed, "extra field should be present"
        assert extra_key in parsed["extra"], f"extra.{extra_key} should be present"


@settings(max_examples=100)
@given(
    level=log_level_strategy,
    message=message_strategy
)
def test_log_entry_timestamp_format(level: LogLevel, message: str):
    """
    **Feature: sap-erp-demo, Property 13: Structured Log Format**
    **Validates: Requirements 6.2**
    
    Property: For any log entry, timestamp SHALL be in ISO 8601 format.
    """
    logger = StructuredLogger(service_name="test-service")
    entry = logger._create_log_entry(level, message)
    
    timestamp = entry["timestamp"]
    
    # Should end with Z (UTC)
    assert timestamp.endswith("Z"), "Timestamp should end with Z"
    
    # Should be parseable as ISO format
    from datetime import datetime
    try:
        datetime.fromisoformat(timestamp.rstrip("Z"))
    except ValueError:
        assert False, f"Timestamp '{timestamp}' is not valid ISO 8601"


@settings(max_examples=100)
@given(
    level=log_level_strategy,
    message=message_strategy
)
def test_log_entry_correlation_id_is_uuid(level: LogLevel, message: str):
    """
    **Feature: sap-erp-demo, Property 13: Structured Log Format**
    **Validates: Requirements 6.2, 6.3**
    
    Property: For any log entry, correlation_id SHALL be a valid UUID.
    """
    import uuid
    
    logger = StructuredLogger(service_name="test-service")
    entry = logger._create_log_entry(level, message)
    
    correlation_id = entry["correlation_id"]
    
    # Should be a valid UUID
    try:
        uuid.UUID(correlation_id)
    except ValueError:
        assert False, f"correlation_id '{correlation_id}' is not a valid UUID"
