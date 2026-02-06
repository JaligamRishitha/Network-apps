"""
Purchase & Procurement Module API routes.
SAP ERP API - Purchase orders, requisitions, and goods receipt
"""
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/purchasing", tags=["Purchase & Procurement"])


# Request/Response Models

class POLineItem(BaseModel):
    line_item: int
    material_id: str
    description: str
    quantity: int
    unit_price: float
    total: float


class PurchaseOrderCreateRequest(BaseModel):
    vendor_id: str
    vendor_name: str
    delivery_date: date
    items: List[POLineItem]
    currency: str = "USD"


class PurchaseOrderResponse(BaseModel):
    po_id: str
    vendor_id: str
    vendor_name: str
    order_date: str
    delivery_date: str
    status: str
    total_amount: float
    currency: str
    items: List[POLineItem]


class POListResponse(BaseModel):
    purchase_orders: List[PurchaseOrderResponse]
    pagination: dict


class RequisitionResponse(BaseModel):
    requisition_id: str
    material_id: str
    material_description: str
    quantity: int
    requested_by: str
    requested_date: str
    status: str
    cost_center: str


class RequisitionListResponse(BaseModel):
    requisitions: List[RequisitionResponse]
    pagination: dict


class GoodsReceiptItem(BaseModel):
    line_item: int
    material_id: str
    quantity_received: int
    storage_location: str


class GoodsReceiptRequest(BaseModel):
    po_id: str
    items: List[GoodsReceiptItem]
    received_by: str
    notes: Optional[str] = None


class GoodsReceiptResponse(BaseModel):
    receipt_id: str
    po_id: str
    receipt_date: str
    received_by: str
    items: List[GoodsReceiptItem]
    status: str


# In-memory storage
_purchase_orders = {}
_requisitions = {}
_goods_receipts = []
_po_counter = 1
_req_counter = 1
_gr_counter = 1


@router.get("/orders", response_model=POListResponse)
async def list_purchase_orders(
    vendor_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List purchase orders with filtering."""
    orders = list(_purchase_orders.values())
    
    if vendor_id:
        orders = [o for o in orders if o["vendor_id"] == vendor_id]
    if status:
        orders = [o for o in orders if o["status"] == status]
    
    total = len(orders)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return POListResponse(
        purchase_orders=[PurchaseOrderResponse(**o) for o in orders[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.get("/orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(po_id: str):
    """Get purchase order details."""
    if po_id not in _purchase_orders:
        raise HTTPException(status_code=404, detail=f"Purchase order not found: {po_id}")
    return PurchaseOrderResponse(**_purchase_orders[po_id])


@router.post("/orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(request: PurchaseOrderCreateRequest):
    """Create a new purchase order."""
    global _po_counter
    
    po_id = f"PO-2024-{_po_counter:05d}"
    _po_counter += 1
    
    total_amount = sum(item.total for item in request.items)
    
    po = {
        "po_id": po_id,
        "vendor_id": request.vendor_id,
        "vendor_name": request.vendor_name,
        "order_date": datetime.now().strftime("%Y-%m-%d"),
        "delivery_date": request.delivery_date.isoformat(),
        "status": "open",
        "total_amount": total_amount,
        "currency": request.currency,
        "items": [item.model_dump() for item in request.items],
    }
    _purchase_orders[po_id] = po
    return PurchaseOrderResponse(**po)


@router.get("/requisitions", response_model=RequisitionListResponse)
async def list_requisitions(
    status: Optional[str] = None,
    material_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List purchase requisitions."""
    reqs = list(_requisitions.values())
    
    if status:
        reqs = [r for r in reqs if r["status"] == status]
    if material_id:
        reqs = [r for r in reqs if r["material_id"] == material_id]
    
    total = len(reqs)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return RequisitionListResponse(
        requisitions=[RequisitionResponse(**r) for r in reqs[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.post("/goods-receipt", response_model=GoodsReceiptResponse)
async def post_goods_receipt(request: GoodsReceiptRequest):
    """Post goods receipt for a purchase order."""
    global _gr_counter
    
    if request.po_id not in _purchase_orders:
        raise HTTPException(status_code=404, detail=f"Purchase order not found: {request.po_id}")
    
    receipt_id = f"GR-2024-{_gr_counter:05d}"
    _gr_counter += 1
    
    receipt = {
        "receipt_id": receipt_id,
        "po_id": request.po_id,
        "receipt_date": datetime.now().isoformat(),
        "received_by": request.received_by,
        "items": [item.model_dump() for item in request.items],
        "status": "posted",
    }
    _goods_receipts.append(receipt)
    
    # Update PO status
    _purchase_orders[request.po_id]["status"] = "received"
    
    return GoodsReceiptResponse(**receipt)
