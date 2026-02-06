# API Routes package
from backend.api.routes.auth import router as auth_router
from backend.api.routes.tickets import router as tickets_router
from backend.api.routes.pm import router as pm_router
from backend.api.routes.mm import router as mm_router
from backend.api.routes.fi import router as fi_router
from backend.api.routes.sales import router as sales_router
from backend.api.routes.inventory import router as inventory_router
from backend.api.routes.finance import router as finance_router
from backend.api.routes.purchasing import router as purchasing_router
from backend.api.routes.production import router as production_router
from backend.api.routes.customers import router as customers_router
from backend.api.routes.vendors import router as vendors_router
from backend.api.routes.business_partners import router as business_partners_router
from backend.api.routes.reports import router as reports_router
from backend.api.routes.integration import router as integration_router
from backend.api.routes.system import router as system_router
from backend.api.routes.work_order_flow import router as work_order_flow_router
from backend.api.routes.crm_integration import router as crm_integration_router
from backend.api.routes.users import router as users_router

# Also export individual route modules for direct import
from backend.api.routes import (
    auth, tickets, pm, mm, fi, users, sales, inventory,
    finance, purchasing, production, customers, vendors,
    business_partners, reports, integration, system,
    work_order_flow, crm_integration
)

__all__ = [
    "auth_router",
    "tickets_router",
    "pm_router",
    "mm_router",
    "fi_router",
    "sales_router",
    "inventory_router",
    "finance_router",
    "purchasing_router",
    "production_router",
    "customers_router",
    "vendors_router",
    "business_partners_router",
    "reports_router",
    "integration_router",
    "system_router",
    "work_order_flow_router",
    "crm_integration_router",
    "users_router",
    # Module exports
    "auth", "tickets", "pm", "mm", "fi", "users", "sales", "inventory",
    "finance", "purchasing", "production", "customers", "vendors",
    "business_partners", "reports", "integration", "system",
    "work_order_flow", "crm_integration",
]
