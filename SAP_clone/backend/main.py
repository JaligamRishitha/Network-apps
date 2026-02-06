"""SAP ERP Demo Backend - FastAPI Application Entry Point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from backend.api.routes import (
    auth, tickets, pm, mm, fi, users,
    sales, inventory, finance, purchasing, production,
    customers, vendors, business_partners,
    reports, integration, system, work_order_flow, crm_integration,
    appointment_validation
)

settings = get_settings()

app = FastAPI(
    title="SAP ERP Demo",
    description="Demo-grade SAP-like ERP application with full SAP module coverage",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api/v1 (existing routes)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(pm.router, prefix="/api/v1")
app.include_router(mm.router, prefix="/api/v1")
app.include_router(fi.router, prefix="/api/v1")
app.include_router(work_order_flow.router, prefix="/api/v1")
# CRM Integration routes for MuleSoft
app.include_router(crm_integration.router, prefix="/api/v1")

# Register new SAP ERP API routes under /api
# Sales & Orders Module
app.include_router(sales.router, prefix="/api")
# Materials & Inventory Module
app.include_router(inventory.router, prefix="/api")
# Business Partners (Customers/Vendors)
app.include_router(customers.router, prefix="/api")
app.include_router(vendors.router, prefix="/api")
app.include_router(business_partners.router, prefix="/api")
# Finance & Accounting Module
app.include_router(finance.router, prefix="/api")
# Purchase & Procurement Module
app.include_router(purchasing.router, prefix="/api")
# Production & Manufacturing Module
app.include_router(production.router, prefix="/api")
# Reports & Analytics Module
app.include_router(reports.router, prefix="/api")
# Integration Endpoints (for Camel flows)
app.include_router(integration.router, prefix="/api")
# System & Authentication
app.include_router(system.router, prefix="/api")
# Appointment Validation (for agent validation)
app.include_router(appointment_validation.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy", "service": "sap-erp-backend", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with API overview"""
    return {
        "message": "SAP ERP Demo API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "modules": {
            "sales": "/api/sales/orders",
            "inventory": "/api/inventory/stock",
            "customers": "/api/customers",
            "vendors": "/api/vendors",
            "finance": "/api/finance/invoices",
            "purchasing": "/api/purchasing/orders",
            "production": "/api/production/orders",
            "reports": "/api/reports/sales-summary",
            "integration": "/api/integration/changes",
            "system": "/api/system/health",
        },
    }
