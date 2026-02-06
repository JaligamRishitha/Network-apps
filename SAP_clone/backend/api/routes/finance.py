"""
Finance & Accounting Module API routes.
SAP ERP API - Invoices, payments, and accounts receivable
"""
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/finance", tags=["Finance & Accounting"])


# Request/Response Models

class InvoiceLineItem(BaseModel):
    line_item: int
    description: str
    quantity: int
    unit_price: float
    total: float


class InvoiceCreateRequest(BaseModel):
    order_id: str
    customer_id: str
    customer_name: str
    due_date: date
    items: List[InvoiceLineItem]
    tax_rate: float = 0.09
    currency: str = "USD"


class InvoiceResponse(BaseModel):
    invoice_id: str
    order_id: str
    customer_id: str
    customer_name: str
    invoice_date: str
    due_date: str
    amount: float
    tax_amount: float
    total_amount: float
    currency: str
    status: str
    payment_status: str


class InvoiceListResponse(BaseModel):
    invoices: List[InvoiceResponse]
    pagination: dict


class PaymentCreateRequest(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str  # bank_transfer, credit_card, check
    reference: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: str
    invoice_id: str
    amount: float
    payment_method: str
    payment_date: str
    reference: Optional[str]
    status: str


class PaymentListResponse(BaseModel):
    payments: List[PaymentResponse]
    pagination: dict


class ARAgingItem(BaseModel):
    customer_id: str
    customer_name: str
    current: float
    days_30: float
    days_60: float
    days_90: float
    over_90: float
    total: float


class ARAgingResponse(BaseModel):
    as_of_date: str
    items: List[ARAgingItem]
    totals: dict


# In-memory storage
_invoices = {}
_payments = []
_invoice_counter = 1
_payment_counter = 1


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    payment_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List invoices with filtering."""
    invoices = list(_invoices.values())
    
    if status:
        invoices = [i for i in invoices if i["status"] == status]
    if customer_id:
        invoices = [i for i in invoices if i["customer_id"] == customer_id]
    if payment_status:
        invoices = [i for i in invoices if i["payment_status"] == payment_status]
    
    total = len(invoices)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return InvoiceListResponse(
        invoices=[InvoiceResponse(**i) for i in invoices[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str):
    """Get invoice details."""
    if invoice_id not in _invoices:
        raise HTTPException(status_code=404, detail=f"Invoice not found: {invoice_id}")
    return InvoiceResponse(**_invoices[invoice_id])


@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(request: InvoiceCreateRequest):
    """Create a new invoice."""
    global _invoice_counter
    
    invoice_id = f"INV-2024-{_invoice_counter:05d}"
    _invoice_counter += 1
    
    amount = sum(item.total for item in request.items)
    tax_amount = amount * request.tax_rate
    total_amount = amount + tax_amount
    
    invoice = {
        "invoice_id": invoice_id,
        "order_id": request.order_id,
        "customer_id": request.customer_id,
        "customer_name": request.customer_name,
        "invoice_date": datetime.now().strftime("%Y-%m-%d"),
        "due_date": request.due_date.isoformat(),
        "amount": amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "currency": request.currency,
        "status": "pending",
        "payment_status": "unpaid",
    }
    _invoices[invoice_id] = invoice
    return InvoiceResponse(**invoice)


@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    invoice_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List payments with filtering."""
    payments = _payments.copy()
    
    if invoice_id:
        payments = [p for p in payments if p["invoice_id"] == invoice_id]
    
    total = len(payments)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaymentListResponse(
        payments=[PaymentResponse(**p) for p in payments[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.post("/payments", response_model=PaymentResponse)
async def record_payment(request: PaymentCreateRequest):
    """Record a payment against an invoice."""
    global _payment_counter
    
    if request.invoice_id not in _invoices:
        raise HTTPException(status_code=404, detail=f"Invoice not found: {request.invoice_id}")
    
    payment_id = f"PAY-2024-{_payment_counter:05d}"
    _payment_counter += 1
    
    payment = {
        "payment_id": payment_id,
        "invoice_id": request.invoice_id,
        "amount": request.amount,
        "payment_method": request.payment_method,
        "payment_date": datetime.now().isoformat(),
        "reference": request.reference,
        "status": "completed",
    }
    _payments.append(payment)
    
    # Update invoice payment status
    invoice = _invoices[request.invoice_id]
    if request.amount >= invoice["total_amount"]:
        invoice["payment_status"] = "paid"
    else:
        invoice["payment_status"] = "partial"
    
    return PaymentResponse(**payment)


@router.get("/accounts-receivable", response_model=ARAgingResponse)
async def get_ar_aging(as_of_date: Optional[str] = None):
    """Get accounts receivable aging report."""
    report_date = as_of_date or datetime.now().strftime("%Y-%m-%d")
    
    # Demo AR aging data
    items = [
        {
            "customer_id": "CUST-001",
            "customer_name": "Acme Corporation",
            "current": 15000.00,
            "days_30": 10000.00,
            "days_60": 5000.00,
            "days_90": 0.00,
            "over_90": 0.00,
            "total": 30000.00,
        },
        {
            "customer_id": "CUST-002",
            "customer_name": "Global Industries",
            "current": 25000.00,
            "days_30": 15000.00,
            "days_60": 8000.00,
            "days_90": 2000.00,
            "over_90": 0.00,
            "total": 50000.00,
        },
    ]
    
    totals = {
        "current": sum(i["current"] for i in items),
        "days_30": sum(i["days_30"] for i in items),
        "days_60": sum(i["days_60"] for i in items),
        "days_90": sum(i["days_90"] for i in items),
        "over_90": sum(i["over_90"] for i in items),
        "total": sum(i["total"] for i in items),
    }
    
    return ARAgingResponse(
        as_of_date=report_date,
        items=[ARAgingItem(**i) for i in items],
        totals=totals,
    )
