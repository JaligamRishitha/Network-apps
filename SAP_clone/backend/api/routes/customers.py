"""
Customers API routes.
SAP ERP API - Customer-specific endpoints with credit info
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/customers", tags=["Customers"])


class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str


class Contact(BaseModel):
    email: str
    phone: str


class CustomerResponse(BaseModel):
    customer_id: str
    name: str
    type: str
    industry: str
    address: Address
    contact: Contact
    credit_limit: float
    credit_used: float
    credit_available: float
    payment_terms: str
    status: str


class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    pagination: dict


# Demo data with credit info
_customers = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Acme Corporation",
        "type": "organization",
        "industry": "Technology",
        "address": {"street": "123 Tech Park", "city": "San Francisco", "country": "US", "postal_code": "94105"},
        "contact": {"email": "contact@acme.com", "phone": "+1-555-0100"},
        "credit_limit": 100000.00,
        "credit_used": 45000.00,
        "credit_available": 55000.00,
        "payment_terms": "NET30",
        "status": "active",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Global Industries",
        "type": "organization",
        "industry": "Manufacturing",
        "address": {"street": "456 Industrial Ave", "city": "Chicago", "country": "US", "postal_code": "60601"},
        "contact": {"email": "info@globalind.com", "phone": "+1-555-0200"},
        "credit_limit": 250000.00,
        "credit_used": 120000.00,
        "credit_available": 130000.00,
        "payment_terms": "NET45",
        "status": "active",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "StartUp Ventures",
        "type": "organization",
        "industry": "Finance",
        "address": {"street": "789 Innovation Blvd", "city": "New York", "country": "US", "postal_code": "10001"},
        "contact": {"email": "hello@startupventures.com", "phone": "+1-555-0300"},
        "credit_limit": 50000.00,
        "credit_used": 48000.00,
        "credit_available": 2000.00,
        "payment_terms": "NET15",
        "status": "active",
    },
}


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    status: Optional[str] = None,
    industry: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all customers with credit information."""
    customers = list(_customers.values())
    
    if status:
        customers = [c for c in customers if c["status"] == status]
    if industry:
        customers = [c for c in customers if c["industry"].lower() == industry.lower()]
    
    total = len(customers)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return CustomerListResponse(
        customers=[CustomerResponse(**c) for c in customers[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str):
    """Get customer details including credit information."""
    if customer_id not in _customers:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
    return CustomerResponse(**_customers[customer_id])
