"""
Business Partners (Customers/Vendors) API routes.
SAP ERP API - Customer and vendor management
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/business-partners", tags=["Business Partners"])


# Request/Response Models

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
    payment_terms: str
    status: str


class VendorResponse(BaseModel):
    vendor_id: str
    name: str
    type: str
    industry: str
    address: Address
    contact: Contact
    payment_terms: str
    status: str


class BusinessPartnerResponse(BaseModel):
    partner_id: str
    partner_type: str  # customer or vendor
    name: str
    type: str
    industry: str
    address: Address
    contact: Contact
    status: str


class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int


class VendorListResponse(BaseModel):
    vendors: List[VendorResponse]
    total: int


# Demo data
_customers = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Acme Corporation",
        "type": "organization",
        "industry": "Technology",
        "address": {"street": "123 Tech Park", "city": "San Francisco", "country": "US", "postal_code": "94105"},
        "contact": {"email": "contact@acme.com", "phone": "+1-555-0100"},
        "credit_limit": 100000.00,
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
        "payment_terms": "NET45",
        "status": "active",
    },
}

_vendors = {
    "VEND-001": {
        "vendor_id": "VEND-001",
        "name": "Tech Supplies Inc",
        "type": "organization",
        "industry": "Wholesale",
        "address": {"street": "789 Supply Chain Rd", "city": "Dallas", "country": "US", "postal_code": "75201"},
        "contact": {"email": "sales@techsupplies.com", "phone": "+1-555-0300"},
        "payment_terms": "NET30",
        "status": "active",
    },
}


# Business Partners Routes

@router.get("", response_model=List[BusinessPartnerResponse])
async def list_business_partners(
    type: Optional[str] = None,  # customer or vendor
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all business partners (customers and vendors)."""
    partners = []
    
    if type != "vendor":
        for c in _customers.values():
            partners.append({
                "partner_id": c["customer_id"],
                "partner_type": "customer",
                "name": c["name"],
                "type": c["type"],
                "industry": c["industry"],
                "address": c["address"],
                "contact": c["contact"],
                "status": c["status"],
            })
    
    if type != "customer":
        for v in _vendors.values():
            partners.append({
                "partner_id": v["vendor_id"],
                "partner_type": "vendor",
                "name": v["name"],
                "type": v["type"],
                "industry": v["industry"],
                "address": v["address"],
                "contact": v["contact"],
                "status": v["status"],
            })
    
    if status:
        partners = [p for p in partners if p["status"] == status]
    
    start = (page - 1) * page_size
    end = start + page_size
    return [BusinessPartnerResponse(**p) for p in partners[start:end]]


@router.get("/{partner_id}", response_model=BusinessPartnerResponse)
async def get_business_partner(partner_id: str):
    """Get business partner details by ID."""
    if partner_id in _customers:
        c = _customers[partner_id]
        return BusinessPartnerResponse(
            partner_id=c["customer_id"],
            partner_type="customer",
            name=c["name"],
            type=c["type"],
            industry=c["industry"],
            address=Address(**c["address"]),
            contact=Contact(**c["contact"]),
            status=c["status"],
        )
    if partner_id in _vendors:
        v = _vendors[partner_id]
        return BusinessPartnerResponse(
            partner_id=v["vendor_id"],
            partner_type="vendor",
            name=v["name"],
            type=v["type"],
            industry=v["industry"],
            address=Address(**v["address"]),
            contact=Contact(**v["contact"]),
            status=v["status"],
        )
    raise HTTPException(status_code=404, detail=f"Business partner not found: {partner_id}")
