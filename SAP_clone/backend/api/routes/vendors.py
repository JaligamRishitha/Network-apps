"""
Vendors API routes.
SAP ERP API - Vendor-specific endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/vendors", tags=["Vendors"])


class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str


class Contact(BaseModel):
    email: str
    phone: str


class VendorResponse(BaseModel):
    vendor_id: str
    name: str
    type: str
    industry: str
    address: Address
    contact: Contact
    payment_terms: str
    bank_details: dict
    status: str


class VendorListResponse(BaseModel):
    vendors: List[VendorResponse]
    pagination: dict


# Demo data
_vendors = {
    "VEND-001": {
        "vendor_id": "VEND-001",
        "name": "Tech Supplies Inc",
        "type": "organization",
        "industry": "Wholesale",
        "address": {"street": "789 Supply Chain Rd", "city": "Dallas", "country": "US", "postal_code": "75201"},
        "contact": {"email": "sales@techsupplies.com", "phone": "+1-555-0300"},
        "payment_terms": "NET30",
        "bank_details": {"bank_name": "First National", "account": "****1234"},
        "status": "active",
    },
    "VEND-002": {
        "vendor_id": "VEND-002",
        "name": "Industrial Parts Co",
        "type": "organization",
        "industry": "Manufacturing",
        "address": {"street": "321 Factory Lane", "city": "Detroit", "country": "US", "postal_code": "48201"},
        "contact": {"email": "orders@indparts.com", "phone": "+1-555-0400"},
        "payment_terms": "NET45",
        "bank_details": {"bank_name": "Commerce Bank", "account": "****5678"},
        "status": "active",
    },
}


@router.get("", response_model=VendorListResponse)
async def list_vendors(
    status: Optional[str] = None,
    industry: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all vendors."""
    vendors = list(_vendors.values())
    
    if status:
        vendors = [v for v in vendors if v["status"] == status]
    if industry:
        vendors = [v for v in vendors if v["industry"].lower() == industry.lower()]
    
    total = len(vendors)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return VendorListResponse(
        vendors=[VendorResponse(**v) for v in vendors[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str):
    """Get vendor details."""
    if vendor_id not in _vendors:
        raise HTTPException(status_code=404, detail=f"Vendor not found: {vendor_id}")
    return VendorResponse(**_vendors[vendor_id])
