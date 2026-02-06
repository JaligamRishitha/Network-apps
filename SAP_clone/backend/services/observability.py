"""
Observability service for metrics and structured logging.
Requirements: 6.1, 6.2, 6.3, 6.4 - Prometheus metrics and structured logging
"""
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from enum import Enum


# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class LogLevel(str, Enum):
    """Log levels - Requirement 6.2"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# Metrics storage (in production, use prometheus_client)
class MetricsCollector:
    """
    Simple metrics collector for demo purposes.
    Requirement 6.1, 6.4 - Track request_count, request_latency, ticket_count_by_status, error_rate
    """
    
    def __init__(self):
        self.request_count: Dict[str, int] = {}
        self.request_latency: Dict[str, list] = {}
        self.ticket_count_by_status: Dict[str, int] = {
            "Open": 0,
            "Assigned": 0,
            "In_Progress": 0,
            "Closed": 0,
        }
        self.error_count: int = 0
        self.total_requests: int = 0
    
    def increment_request_count(self, endpoint: str, method: str):
        """Increment request count for an endpoint."""
        key = f"{method}:{endpoint}"
        self.request_count[key] = self.request_count.get(key, 0) + 1
        self.total_requests += 1
    
    def record_latency(self, endpoint: str, latency_ms: float):
        """Record request latency."""
        if endpoint not in self.request_latency:
            self.request_latency[endpoint] = []
        self.request_latency[endpoint].append(latency_ms)
    
    def increment_error_count(self):
        """Increment error count."""
        self.error_count += 1
    
    def update_ticket_count(self, status: str, delta: int = 1):
        """Update ticket count by status."""
        if status in self.ticket_count_by_status:
            self.ticket_count_by_status[status] += delta
    
    def get_error_rate(self) -> float:
        """Calculate error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.error_count / self.total_requests
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as dictionary."""
        return {
            "request_count": self.request_count,
            "request_latency_avg": {
                k: sum(v) / len(v) if v else 0
                for k, v in self.request_latency.items()
            },
            "ticket_count_by_status": self.ticket_count_by_status,
            "error_rate": self.get_error_rate(),
            "total_requests": self.total_requests,
            "total_errors": self.error_count,
        }
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Request count
        lines.append("# HELP sap_erp_request_count Total number of requests")
        lines.append("# TYPE sap_erp_request_count counter")
        for key, count in self.request_count.items():
            method, endpoint = key.split(":", 1)
            lines.append(f'sap_erp_request_count{{method="{method}",endpoint="{endpoint}"}} {count}')
        
        # Ticket count by status
        lines.append("# HELP sap_erp_ticket_count Number of tickets by status")
        lines.append("# TYPE sap_erp_ticket_count gauge")
        for status, count in self.ticket_count_by_status.items():
            lines.append(f'sap_erp_ticket_count{{status="{status}"}} {count}')
        
        # Error rate
        lines.append("# HELP sap_erp_error_rate Error rate")
        lines.append("# TYPE sap_erp_error_rate gauge")
        lines.append(f"sap_erp_error_rate {self.get_error_rate():.4f}")
        
        return "\n".join(lines)


# Global metrics collector
metrics = MetricsCollector()


class StructuredLogger:
    """
    Structured JSON logger.
    Requirement 6.2 - Generate structured JSON logs with correlation_id, timestamp, service, log_level
    """
    
    def __init__(self, service_name: str = "sap-erp-backend"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
    
    def _create_log_entry(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a structured log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "log_level": level.value,
            "correlation_id": correlation_id_var.get() or str(uuid.uuid4()),
            "message": message,
        }
        if extra:
            entry["extra"] = extra
        return entry
    
    def _log(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a message with structured format."""
        entry = self._create_log_entry(level, message, extra)
        log_line = json.dumps(entry)
        
        if level == LogLevel.DEBUG:
            self.logger.debug(log_line)
        elif level == LogLevel.INFO:
            self.logger.info(log_line)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_line)
        elif level == LogLevel.ERROR:
            self.logger.error(log_line)
            metrics.increment_error_count()
    
    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, kwargs if kwargs else None)
    
    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, kwargs if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        self._log(LogLevel.WARNING, message, kwargs if kwargs else None)
    
    def error(self, message: str, **kwargs):
        self._log(LogLevel.ERROR, message, kwargs if kwargs else None)


# Global logger
logger = StructuredLogger()


def get_correlation_id() -> str:
    """Get current correlation ID or generate new one."""
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def validate_log_entry(entry: Dict[str, Any]) -> bool:
    """
    Validate that a log entry has required fields.
    Requirement 6.2 - Validate structured log format
    """
    required_fields = {"correlation_id", "timestamp", "service", "log_level"}
    valid_levels = {level.value for level in LogLevel}
    
    # Check required fields
    if not required_fields.issubset(entry.keys()):
        return False
    
    # Check log level is valid
    if entry.get("log_level") not in valid_levels:
        return False
    
    return True
