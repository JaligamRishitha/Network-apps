"""
System & Authentication Module API routes.
SAP ERP API - Health checks, configuration, and OAuth
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional


router = APIRouter(prefix="/system", tags=["System"])


# Response Models

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    components: dict


class ConfigResponse(BaseModel):
    company_code: str
    company_name: str
    currency: str
    fiscal_year_start: str
    timezone: str
    modules_enabled: list
    integration_endpoints: dict


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for container orchestration.
    Returns service status and component health.
    """
    return HealthResponse(
        status="healthy",
        service="sap-erp-backend",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        components={
            "database": "healthy",
            "cache": "healthy",
            "message_queue": "healthy",
        },
    )


@router.get("/config", response_model=ConfigResponse)
async def get_system_config():
    """
    Get system configuration and company settings.
    """
    return ConfigResponse(
        company_code="1000",
        company_name="Demo Corporation",
        currency="USD",
        fiscal_year_start="01-01",
        timezone="America/New_York",
        modules_enabled=["SD", "MM", "FI", "PM", "PP"],
        integration_endpoints={
            "crm": "http://sap-erp-crm-mock:8084",
            "itsm": "http://sap-erp-itsm-mock:8085",
        },
    )


@router.get("/modules")
async def list_modules():
    """List available SAP modules and their status."""
    return {
        "modules": [
            {"code": "SD", "name": "Sales & Distribution", "status": "active"},
            {"code": "MM", "name": "Materials Management", "status": "active"},
            {"code": "FI", "name": "Financial Accounting", "status": "active"},
            {"code": "PM", "name": "Plant Maintenance", "status": "active"},
            {"code": "PP", "name": "Production Planning", "status": "active"},
            {"code": "HR", "name": "Human Resources", "status": "inactive"},
        ]
    }


@router.get("/version")
async def get_version():
    """Get API version information."""
    return {
        "api_version": "1.0.0",
        "build": "2024.01.15",
        "environment": "demo",
    }
