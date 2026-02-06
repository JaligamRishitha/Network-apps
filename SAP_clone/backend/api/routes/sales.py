"""
Sales & Orders Module API routes.
SAP ERP API - Sales order management
"""
from datetime import datetime, date
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db


router = APIRouter(prefix="/sales", tags=["Sales & Orders"])


# Request/Response Models

class OrderLineItem(BaseModel):
    line_item: int
    material_id: str
    description: str
    quantity: int
    unit_price: float
    total: float


class SalesOrderCreateRequest(BaseModel):
    customer_id: str
    customer_name: str
    delivery_date: date
    items: List[OrderLineItem]
    currency: str = "USD"


class SalesOrderUpdateRequest(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    delivery_date: Optional[date] = None
    items: Optional[List[OrderLineItem]] = None
    status: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    status: str


class SalesOrderResponse(BaseModel):
    order_id: str
    customer_id: str
    customer_name: str
    order_date: str
    delivery_date: str
    status: str
    total_amount: float
    currency: str
    items: List[OrderLineItem]


class PaginationInfo(BaseModel):
    page: int
    total_pages: int
    total_records: int


class SalesOrderListResponse(BaseModel):
    orders: List[SalesOrderResponse]
    pagination: PaginationInfo


# In-memory storage for demo - with seed data matching customers
_sales_orders = {
    "SO-2024-00001": {
        "order_id": "SO-2024-00001",
        "customer_id": "CUST-001",
        "customer_name": "Acme Corporation",
        "order_date": "2026-01-10",
        "delivery_date": "2026-02-15",
        "status": "processing",
        "total_amount": 12500.00,
        "currency": "USD",
        "items": [
            {
                "line_item": 1,
                "material_id": "MAT-001",
                "description": "Copper Wire 10mm",
                "quantity": 200,
                "unit_price": 25.00,
                "total": 5000.00,
            },
            {
                "line_item": 2,
                "material_id": "MAT-002",
                "description": "Circuit Breaker 100A",
                "quantity": 10,
                "unit_price": 750.00,
                "total": 7500.00,
            },
        ],
    },
    "SO-2024-00002": {
        "order_id": "SO-2024-00002",
        "customer_id": "CUST-002",
        "customer_name": "Global Industries",
        "order_date": "2026-01-12",
        "delivery_date": "2026-02-20",
        "status": "new",
        "total_amount": 45000.00,
        "currency": "USD",
        "items": [
            {
                "line_item": 1,
                "material_id": "MAT-003",
                "description": "Transformer Oil",
                "quantity": 500,
                "unit_price": 80.00,
                "total": 40000.00,
            },
            {
                "line_item": 2,
                "material_id": "MAT-005",
                "description": "Fuse 30A",
                "quantity": 50,
                "unit_price": 100.00,
                "total": 5000.00,
            },
        ],
    },
}
_order_counter = 3


def _generate_order_id():
    global _order_counter
    order_id = f"SO-2024-{_order_counter:05d}"
    _order_counter += 1
    return order_id


@router.get("/orders", response_model=SalesOrderListResponse)
async def list_sales_orders(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    modified_since: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all sales orders with pagination and filtering."""
    orders = list(_sales_orders.values())
    
    if status:
        orders = [o for o in orders if o["status"] == status]
    if customer_id:
        orders = [o for o in orders if o["customer_id"] == customer_id]
    
    total = len(orders)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return SalesOrderListResponse(
        orders=[SalesOrderResponse(**o) for o in orders[start:end]],
        pagination=PaginationInfo(page=page, total_pages=total_pages, total_records=total),
    )


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(order_id: str):
    """Get single order details with line items."""
    if order_id not in _sales_orders:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    return SalesOrderResponse(**_sales_orders[order_id])


@router.post("/orders", response_model=SalesOrderResponse)
async def create_sales_order(request: SalesOrderCreateRequest):
    """Create new sales order."""
    order_id = _generate_order_id()
    total_amount = sum(item.total for item in request.items)
    
    order = {
        "order_id": order_id,
        "customer_id": request.customer_id,
        "customer_name": request.customer_name,
        "order_date": datetime.now().strftime("%Y-%m-%d"),
        "delivery_date": request.delivery_date.isoformat(),
        "status": "new",
        "total_amount": total_amount,
        "currency": request.currency,
        "items": [item.model_dump() for item in request.items],
    }
    _sales_orders[order_id] = order
    return SalesOrderResponse(**order)


@router.put("/orders/{order_id}", response_model=SalesOrderResponse)
async def update_sales_order(order_id: str, request: SalesOrderUpdateRequest):
    """Update existing sales order."""
    if order_id not in _sales_orders:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    
    order = _sales_orders[order_id]
    if request.customer_id:
        order["customer_id"] = request.customer_id
    if request.customer_name:
        order["customer_name"] = request.customer_name
    if request.delivery_date:
        order["delivery_date"] = request.delivery_date.isoformat()
    if request.items:
        order["items"] = [item.model_dump() for item in request.items]
        order["total_amount"] = sum(item.total for item in request.items)
    if request.status:
        order["status"] = request.status
    
    return SalesOrderResponse(**order)


@router.patch("/orders/{order_id}/status", response_model=SalesOrderResponse)
async def update_order_status(order_id: str, request: StatusUpdateRequest):
    """Update order status (e.g., processing, shipped, delivered)."""
    if order_id not in _sales_orders:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    
    valid_statuses = ["new", "processing", "shipped", "delivered", "cancelled"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    _sales_orders[order_id]["status"] = request.status
    return SalesOrderResponse(**_sales_orders[order_id])
