"""
Appointment Validation API Routes
For agents to validate appointment requests against SAP master data
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from backend.db.database import get_db
from backend.services.appointment_validation_service import AppointmentValidationService


router = APIRouter(prefix="/api/appointments", tags=["appointment-validation"])


class AppointmentValidationRequest(BaseModel):
    """Request model for appointment validation"""
    required_parts: Optional[str] = None
    required_skills: Optional[str] = None
    location: Optional[str] = None
    cost_center_id: Optional[str] = None
    estimated_cost: float = 0.0


@router.post("/validate")
async def validate_appointment(
    request: AppointmentValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate an appointment request against SAP master data

    Checks:
    - Parts availability in inventory
    - Technician availability with required skills
    - Location/asset existence
    - Budget availability

    Example:
    ```json
    {
        "required_parts": "Air filter, Coolant",
        "required_skills": "HVAC Certified, Electrical Safety",
        "location": "Building A, Floor 3",
        "cost_center_id": "CC-HVAC-001",
        "estimated_cost": 5000.00
    }
    ```
    """
    service = AppointmentValidationService(db)

    validation_result = await service.validate_appointment_request(
        required_parts=request.required_parts,
        required_skills=request.required_skills,
        location=request.location,
        cost_center_id=request.cost_center_id,
        estimated_cost=request.estimated_cost
    )

    return validation_result


@router.get("/parts/search")
async def search_parts(
    query: str = Query(..., min_length=2, description="Search query for parts"),
    db: Session = Depends(get_db)
):
    """
    Search for parts in SAP inventory

    Example: GET /api/appointments/parts/search?query=air filter
    """
    service = AppointmentValidationService(db)

    parts_result = await service.validate_parts_availability(query)

    return {
        "query": query,
        "parts_found": parts_result["parts_status"]
    }


@router.get("/technicians/available")
async def get_available_technicians(
    skill: Optional[str] = Query(None, description="Filter by skill"),
    db: Session = Depends(get_db)
):
    """
    Get list of available technicians

    Example:
    - GET /api/appointments/technicians/available
    - GET /api/appointments/technicians/available?skill=HVAC
    """
    service = AppointmentValidationService(db)

    technicians = await service.get_available_technicians(skill=skill)

    return {
        "count": len(technicians),
        "technicians": technicians
    }


@router.get("/technicians/validate")
async def validate_technician_skills(
    required_skills: str = Query(..., description="Comma-separated skills"),
    db: Session = Depends(get_db)
):
    """
    Check if technicians with required skills are available

    Example: GET /api/appointments/technicians/validate?required_skills=HVAC Certified,Electrical Safety
    """
    service = AppointmentValidationService(db)

    result = await service.validate_technician_availability(required_skills)

    return result


@router.get("/locations/search")
async def search_locations(
    location: str = Query(..., min_length=2, description="Location to search"),
    db: Session = Depends(get_db)
):
    """
    Search for locations/assets in SAP

    Example: GET /api/appointments/locations/search?location=Building A
    """
    service = AppointmentValidationService(db)

    result = await service.validate_location(location)

    return result


@router.get("/budget/check")
async def check_budget(
    cost_center_id: str = Query(..., description="Cost center ID"),
    estimated_cost: float = Query(..., description="Estimated cost"),
    db: Session = Depends(get_db)
):
    """
    Check if cost center has sufficient budget

    Example: GET /api/appointments/budget/check?cost_center_id=CC-HVAC-001&estimated_cost=5000
    """
    service = AppointmentValidationService(db)

    result = await service.validate_budget(cost_center_id, estimated_cost)

    return result


@router.get("/materials/recommendations")
async def get_material_recommendations(
    asset_id: Optional[str] = Query(None, description="Asset ID for context"),
    db: Session = Depends(get_db)
):
    """
    Get recommended materials for appointments

    Example: GET /api/appointments/materials/recommendations
    """
    service = AppointmentValidationService(db)

    recommendations = await service.get_material_recommendations(asset_id=asset_id)

    return {
        "count": len(recommendations),
        "materials": recommendations
    }
