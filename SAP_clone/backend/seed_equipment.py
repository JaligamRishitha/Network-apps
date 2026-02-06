"""
Seed script to add dummy equipment to the database.
Run this script to populate the database with sample equipment for testing.
"""
import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_async_session, engine
from backend.models.pm_models import Asset, AssetType, AssetStatus

# Dummy equipment data matching SAP PM style
DUMMY_EQUIPMENT = [
    {
        "asset_id": "10005394",
        "asset_type": AssetType.TRANSFORMER,
        "name": "Diesel Generator",
        "location": "1000-UTL-GEN1 Generator Room",
        "installation_date": date(2020, 5, 15),
        "status": AssetStatus.OPERATIONAL,
        "description": "Main diesel generator for backup power"
    },
    {
        "asset_id": "10005395",
        "asset_type": AssetType.TRANSFORMER,
        "name": "Main Transformer T1",
        "location": "1000-UTL-TRF1 Transformer Yard",
        "installation_date": date(2018, 3, 10),
        "status": AssetStatus.OPERATIONAL,
        "description": "132kV/33kV main power transformer"
    },
    {
        "asset_id": "10005396",
        "asset_type": AssetType.SUBSTATION,
        "name": "Substation SS-01",
        "location": "1000-PWR-SS01 Main Substation",
        "installation_date": date(2015, 8, 20),
        "status": AssetStatus.OPERATIONAL,
        "description": "Primary distribution substation"
    },
    {
        "asset_id": "10005397",
        "asset_type": AssetType.FEEDER,
        "name": "Feeder Line F-101",
        "location": "1000-PWR-FDR1 North Section",
        "installation_date": date(2019, 11, 5),
        "status": AssetStatus.OPERATIONAL,
        "description": "11kV distribution feeder line"
    },
    {
        "asset_id": "10005398",
        "asset_type": AssetType.TRANSFORMER,
        "name": "Auxiliary Transformer T2",
        "location": "1000-UTL-TRF2 Plant Area",
        "installation_date": date(2021, 2, 28),
        "status": AssetStatus.OPERATIONAL,
        "description": "33kV/11kV auxiliary transformer"
    },
    {
        "asset_id": "10005399",
        "asset_type": AssetType.SUBSTATION,
        "name": "Substation SS-02",
        "location": "1000-PWR-SS02 East Wing",
        "installation_date": date(2017, 6, 12),
        "status": AssetStatus.UNDER_MAINTENANCE,
        "description": "Secondary distribution substation"
    },
    {
        "asset_id": "10005400",
        "asset_type": AssetType.FEEDER,
        "name": "Feeder Line F-102",
        "location": "1000-PWR-FDR2 South Section",
        "installation_date": date(2020, 9, 18),
        "status": AssetStatus.OPERATIONAL,
        "description": "11kV distribution feeder line - South"
    },
    {
        "asset_id": "10005401",
        "asset_type": AssetType.TRANSFORMER,
        "name": "Emergency Generator EG-01",
        "location": "1000-UTL-EMG1 Emergency Room",
        "installation_date": date(2022, 1, 10),
        "status": AssetStatus.OPERATIONAL,
        "description": "Emergency backup generator 500kVA"
    },
    {
        "asset_id": "10005402",
        "asset_type": AssetType.SUBSTATION,
        "name": "Control Room Panel CP-01",
        "location": "1000-CTL-PNL1 Control Center",
        "installation_date": date(2016, 4, 25),
        "status": AssetStatus.OPERATIONAL,
        "description": "Main control panel and switchgear"
    },
    {
        "asset_id": "10005403",
        "asset_type": AssetType.FEEDER,
        "name": "Feeder Line F-103",
        "location": "1000-PWR-FDR3 West Section",
        "installation_date": date(2021, 7, 30),
        "status": AssetStatus.OPERATIONAL,
        "description": "11kV distribution feeder line - West"
    },
]


async def seed_equipment():
    """Add dummy equipment to the database."""
    async for session in get_async_session():
        try:
            # Check if equipment already exists
            from sqlalchemy import select
            result = await session.execute(select(Asset).limit(1))
            existing = result.scalar_one_or_none()

            if existing:
                print("Equipment already exists in database. Skipping seed.")
                return

            # Add dummy equipment
            for eq_data in DUMMY_EQUIPMENT:
                asset = Asset(**eq_data)
                session.add(asset)

            await session.commit()
            print(f"Successfully added {len(DUMMY_EQUIPMENT)} equipment items to database.")

        except Exception as e:
            print(f"Error seeding equipment: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_equipment())
