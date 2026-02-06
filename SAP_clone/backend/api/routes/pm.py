"""
Plant Maintenance (PM) API routes.
Requirements: 2.1, 2.2, 2.3 - Asset, maintenance order, and incident management
"""
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.pm_models import AssetType, AssetStatus, OrderType, FaultType
from backend.models.ticket_models import Priority
from backend.services.pm_service import PMService, AssetNotFoundError


router = APIRouter(prefix="/pm", tags=["Plant Maintenance"])


# Request/Response Models

class AssetCreateRequest(BaseModel):
    asset_type: str
    name: str
    location: str
    installation_date: date
    status: str = "operational"
    description: Optional[str] = None


class AssetResponse(BaseModel):
    asset_id: str
    asset_type: str
    name: str
    location: str
    installation_date: str
    status: str
    description: Optional[str]


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int


class MaintenanceOrderCreateRequest(BaseModel):
    asset_id: str
    order_type: str
    description: str
    scheduled_date: datetime
    created_by: str
    priority: str = "P3"


class MaintenanceOrderResponse(BaseModel):
    order_id: str
    asset_id: str
    ticket_id: Optional[str]
    order_type: str
    status: str
    description: str
    scheduled_date: str


class IncidentCreateRequest(BaseModel):
    asset_id: str
    fault_type: str
    description: str
    reported_by: str
    severity: str = "P2"


class IncidentResponse(BaseModel):
    incident_id: str
    asset_id: str
    ticket_id: Optional[str]
    fault_type: str
    description: str
    reported_by: str
    reported_at: str


# Asset Routes

@router.post("/assets", response_model=AssetResponse)
async def create_asset(
    request: AssetCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new asset. Requirement 2.1"""
    service = PMService(db)
    
    try:
        asset_type = AssetType(request.asset_type)
        status = AssetStatus(request.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    asset = await service.create_asset(
        asset_type=asset_type,
        name=request.name,
        location=request.location,
        installation_date=request.installation_date,
        status=status,
        description=request.description,
    )
    await db.commit()
    
    return AssetResponse(
        asset_id=asset.asset_id,
        asset_type=asset.asset_type.value,
        name=asset.name,
        location=asset.location,
        installation_date=asset.installation_date.isoformat(),
        status=asset.status.value,
        description=asset.description,
    )


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List assets with optional filtering."""
    service = PMService(db)
    
    type_enum = AssetType(asset_type) if asset_type else None
    status_enum = AssetStatus(status) if status else None
    
    assets, total = await service.list_assets(
        asset_type=type_enum,
        status=status_enum,
        limit=limit,
        offset=offset,
    )
    
    return AssetListResponse(
        assets=[
            AssetResponse(
                asset_id=a.asset_id,
                asset_type=a.asset_type.value,
                name=a.name,
                location=a.location,
                installation_date=a.installation_date.isoformat(),
                status=a.status.value,
                description=a.description,
            )
            for a in assets
        ],
        total=total,
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an asset by ID."""
    service = PMService(db)
    
    try:
        asset = await service.get_asset_or_raise(asset_id)
        return AssetResponse(
            asset_id=asset.asset_id,
            asset_type=asset.asset_type.value,
            name=asset.name,
            location=asset.location,
            installation_date=asset.installation_date.isoformat(),
            status=asset.status.value,
            description=asset.description,
        )
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")


# Maintenance Order Routes

@router.post("/maintenance-orders", response_model=MaintenanceOrderResponse)
async def create_maintenance_order(
    request: MaintenanceOrderCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a maintenance order. Requirement 2.2"""
    service = PMService(db)
    
    try:
        order_type = OrderType(request.order_type)
        priority = Priority(request.priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        order, ticket = await service.create_maintenance_order(
            asset_id=request.asset_id,
            order_type=order_type,
            description=request.description,
            scheduled_date=request.scheduled_date,
            created_by=request.created_by,
            priority=priority,
        )
        await db.commit()
        
        return MaintenanceOrderResponse(
            order_id=order.order_id,
            asset_id=order.asset_id,
            ticket_id=order.ticket_id,
            order_type=order.order_type.value,
            status=order.status.value,
            description=order.description,
            scheduled_date=order.scheduled_date.isoformat(),
        )
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Asset not found: {request.asset_id}")


@router.get("/maintenance-orders", response_model=List[MaintenanceOrderResponse])
async def list_maintenance_orders(
    asset_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List maintenance orders."""
    service = PMService(db)
    
    from backend.models.pm_models import OrderStatus
    status_enum = OrderStatus(status) if status else None
    
    orders, total = await service.list_maintenance_orders(
        asset_id=asset_id,
        status=status_enum,
        limit=limit,
        offset=offset,
    )
    
    return [
        MaintenanceOrderResponse(
            order_id=o.order_id,
            asset_id=o.asset_id,
            ticket_id=o.ticket_id,
            order_type=o.order_type.value,
            status=o.status.value,
            description=o.description,
            scheduled_date=o.scheduled_date.isoformat(),
        )
        for o in orders
    ]


# Incident Routes

@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(
    request: IncidentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create an incident. Requirement 2.3"""
    service = PMService(db)
    
    try:
        fault_type = FaultType(request.fault_type)
        severity = Priority(request.severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        incident, ticket = await service.create_incident(
            asset_id=request.asset_id,
            fault_type=fault_type,
            description=request.description,
            reported_by=request.reported_by,
            severity=severity,
        )
        await db.commit()
        
        return IncidentResponse(
            incident_id=incident.incident_id,
            asset_id=incident.asset_id,
            ticket_id=incident.ticket_id,
            fault_type=incident.fault_type.value,
            description=incident.description,
            reported_by=incident.reported_by,
            reported_at=incident.reported_at.isoformat(),
        )
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Asset not found: {request.asset_id}")


# Seed Data Route

@router.post("/seed-equipment")
async def seed_equipment(db: AsyncSession = Depends(get_db)):
    """Seed the database with dummy equipment for testing."""
    from datetime import date as date_type

    service = PMService(db)

    # Check if equipment already exists
    existing, _ = await service.list_assets(limit=1)
    if existing:
        return {"message": "Equipment already exists", "count": len(existing)}

    # Dummy equipment data
    dummy_equipment = [
        {
            "asset_type": AssetType.TRANSFORMER,
            "name": "Diesel Generator",
            "location": "1000-UTL-GEN1 Generator Room",
            "installation_date": date_type(2020, 5, 15),
            "status": AssetStatus.OPERATIONAL,
            "description": "Main diesel generator for backup power"
        },
        {
            "asset_type": AssetType.TRANSFORMER,
            "name": "Main Transformer T1",
            "location": "1000-UTL-TRF1 Transformer Yard",
            "installation_date": date_type(2018, 3, 10),
            "status": AssetStatus.OPERATIONAL,
            "description": "132kV/33kV main power transformer"
        },
        {
            "asset_type": AssetType.SUBSTATION,
            "name": "Substation SS-01",
            "location": "1000-PWR-SS01 Main Substation",
            "installation_date": date_type(2015, 8, 20),
            "status": AssetStatus.OPERATIONAL,
            "description": "Primary distribution substation"
        },
        {
            "asset_type": AssetType.FEEDER,
            "name": "Feeder Line F-101",
            "location": "1000-PWR-FDR1 North Section",
            "installation_date": date_type(2019, 11, 5),
            "status": AssetStatus.OPERATIONAL,
            "description": "11kV distribution feeder line"
        },
        {
            "asset_type": AssetType.TRANSFORMER,
            "name": "Auxiliary Transformer T2",
            "location": "1000-UTL-TRF2 Plant Area",
            "installation_date": date_type(2021, 2, 28),
            "status": AssetStatus.OPERATIONAL,
            "description": "33kV/11kV auxiliary transformer"
        },
        {
            "asset_type": AssetType.SUBSTATION,
            "name": "Substation SS-02",
            "location": "1000-PWR-SS02 East Wing",
            "installation_date": date_type(2017, 6, 12),
            "status": AssetStatus.UNDER_MAINTENANCE,
            "description": "Secondary distribution substation"
        },
        {
            "asset_type": AssetType.FEEDER,
            "name": "Feeder Line F-102",
            "location": "1000-PWR-FDR2 South Section",
            "installation_date": date_type(2020, 9, 18),
            "status": AssetStatus.OPERATIONAL,
            "description": "11kV distribution feeder line - South"
        },
        {
            "asset_type": AssetType.TRANSFORMER,
            "name": "Emergency Generator EG-01",
            "location": "1000-UTL-EMG1 Emergency Room",
            "installation_date": date_type(2022, 1, 10),
            "status": AssetStatus.OPERATIONAL,
            "description": "Emergency backup generator 500kVA"
        },
        {
            "asset_type": AssetType.SUBSTATION,
            "name": "Control Room Panel CP-01",
            "location": "1000-CTL-PNL1 Control Center",
            "installation_date": date_type(2016, 4, 25),
            "status": AssetStatus.OPERATIONAL,
            "description": "Main control panel and switchgear"
        },
        {
            "asset_type": AssetType.FEEDER,
            "name": "Feeder Line F-103",
            "location": "1000-PWR-FDR3 West Section",
            "installation_date": date_type(2021, 7, 30),
            "status": AssetStatus.OPERATIONAL,
            "description": "11kV distribution feeder line - West"
        },
    ]

    created_count = 0
    for eq_data in dummy_equipment:
        try:
            await service.create_asset(**eq_data)
            created_count += 1
        except Exception as e:
            print(f"Error creating asset: {e}")

    await db.commit()
    return {"message": f"Successfully created {created_count} equipment items", "count": created_count}
