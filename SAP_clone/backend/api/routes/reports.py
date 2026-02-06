"""
Reports & Analytics Module API routes.
SAP ERP API - Business intelligence and reporting
"""
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


# Response Models

class SalesSummaryItem(BaseModel):
    period: str
    total_orders: int
    total_revenue: float
    average_order_value: float
    top_customer: str
    currency: str


class SalesSummaryResponse(BaseModel):
    period_type: str
    year: int
    data: List[SalesSummaryItem]
    totals: dict


class InventoryValuationItem(BaseModel):
    material_id: str
    description: str
    quantity: int
    unit_cost: float
    total_value: float
    storage_location: str


class InventoryValuationResponse(BaseModel):
    as_of_date: str
    items: List[InventoryValuationItem]
    total_value: float
    currency: str


class CustomerAgingItem(BaseModel):
    customer_id: str
    customer_name: str
    current: float
    days_1_30: float
    days_31_60: float
    days_61_90: float
    over_90: float
    total: float


class CustomerAgingResponse(BaseModel):
    as_of_date: str
    items: List[CustomerAgingItem]
    totals: dict


class ProfitLossItem(BaseModel):
    category: str
    description: str
    amount: float


class ProfitLossResponse(BaseModel):
    from_date: str
    to_date: str
    revenue: List[ProfitLossItem]
    expenses: List[ProfitLossItem]
    total_revenue: float
    total_expenses: float
    net_income: float
    currency: str


@router.get("/sales-summary", response_model=SalesSummaryResponse)
async def get_sales_summary(
    period: str = Query("monthly", pattern="^(daily|weekly|monthly|quarterly|yearly)$"),
    year: int = Query(2024),
):
    """Get sales dashboard summary."""
    # Demo data
    data = [
        {"period": "January", "total_orders": 150, "total_revenue": 450000.00, "average_order_value": 3000.00, "top_customer": "Acme Corp", "currency": "USD"},
        {"period": "February", "total_orders": 175, "total_revenue": 525000.00, "average_order_value": 3000.00, "top_customer": "Global Industries", "currency": "USD"},
        {"period": "March", "total_orders": 200, "total_revenue": 620000.00, "average_order_value": 3100.00, "top_customer": "Acme Corp", "currency": "USD"},
    ]
    
    return SalesSummaryResponse(
        period_type=period,
        year=year,
        data=[SalesSummaryItem(**d) for d in data],
        totals={
            "total_orders": sum(d["total_orders"] for d in data),
            "total_revenue": sum(d["total_revenue"] for d in data),
            "average_order_value": sum(d["total_revenue"] for d in data) / sum(d["total_orders"] for d in data),
        },
    )


@router.get("/inventory-valuation", response_model=InventoryValuationResponse)
async def get_inventory_valuation(as_of_date: Optional[str] = None):
    """Get stock valuation report."""
    report_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
    
    items = [
        {"material_id": "MAT-001", "description": "Enterprise License", "quantity": 500, "unit_cost": 1000.00, "total_value": 500000.00, "storage_location": "WH01"},
        {"material_id": "MAT-002", "description": "Server Hardware", "quantity": 25, "unit_cost": 5000.00, "total_value": 125000.00, "storage_location": "WH01"},
        {"material_id": "RAW-001", "description": "Raw Material 1", "quantity": 1000, "unit_cost": 50.00, "total_value": 50000.00, "storage_location": "WH02"},
    ]
    
    return InventoryValuationResponse(
        as_of_date=report_date,
        items=[InventoryValuationItem(**i) for i in items],
        total_value=sum(i["total_value"] for i in items),
        currency="USD",
    )


@router.get("/customer-aging", response_model=CustomerAgingResponse)
async def get_customer_aging(as_of_date: Optional[str] = None):
    """Get AR aging report by customer."""
    report_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
    
    items = [
        {"customer_id": "CUST-001", "customer_name": "Acme Corporation", "current": 15000.00, "days_1_30": 10000.00, "days_31_60": 5000.00, "days_61_90": 0.00, "over_90": 0.00, "total": 30000.00},
        {"customer_id": "CUST-002", "customer_name": "Global Industries", "current": 25000.00, "days_1_30": 15000.00, "days_31_60": 8000.00, "days_61_90": 2000.00, "over_90": 0.00, "total": 50000.00},
    ]
    
    return CustomerAgingResponse(
        as_of_date=report_date,
        items=[CustomerAgingItem(**i) for i in items],
        totals={
            "current": sum(i["current"] for i in items),
            "days_1_30": sum(i["days_1_30"] for i in items),
            "days_31_60": sum(i["days_31_60"] for i in items),
            "days_61_90": sum(i["days_61_90"] for i in items),
            "over_90": sum(i["over_90"] for i in items),
            "total": sum(i["total"] for i in items),
        },
    )


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def get_profit_loss(
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Get P&L statement for a period."""
    revenue = [
        {"category": "Sales", "description": "Product Sales", "amount": 1500000.00},
        {"category": "Sales", "description": "Service Revenue", "amount": 250000.00},
        {"category": "Other", "description": "Interest Income", "amount": 5000.00},
    ]
    
    expenses = [
        {"category": "COGS", "description": "Cost of Goods Sold", "amount": 750000.00},
        {"category": "Operating", "description": "Salaries & Wages", "amount": 300000.00},
        {"category": "Operating", "description": "Rent & Utilities", "amount": 50000.00},
        {"category": "Operating", "description": "Marketing", "amount": 75000.00},
        {"category": "Admin", "description": "Administrative Expenses", "amount": 25000.00},
    ]
    
    total_revenue = sum(r["amount"] for r in revenue)
    total_expenses = sum(e["amount"] for e in expenses)
    
    return ProfitLossResponse(
        from_date=from_date,
        to_date=to_date,
        revenue=[ProfitLossItem(**r) for r in revenue],
        expenses=[ProfitLossItem(**e) for e in expenses],
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        net_income=total_revenue - total_expenses,
        currency="USD",
    )
