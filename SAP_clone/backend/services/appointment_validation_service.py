"""
Appointment Validation Service
Validates appointment requests against SAP master data
"""
import re
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, or_

from backend.models.mm_models import Material
from backend.models.pm_models import Asset, AssetStatus
from backend.models.fi_models import CostCenter


class AppointmentValidationService:
    """Service to validate appointment requests against SAP master data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_appointment_request(
        self,
        required_parts: Optional[str] = None,
        required_skills: Optional[str] = None,
        location: Optional[str] = None,
        cost_center_id: Optional[str] = None,
        estimated_cost: float = 0.0
    ) -> Dict:
        """
        Comprehensive validation of appointment request

        Returns:
            {
                "valid": bool,
                "parts_validation": {...},
                "technician_validation": {...},
                "location_validation": {...},
                "budget_validation": {...},
                "issues": [...],
                "recommendations": [...]
            }
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "recommendations": [],
            "parts_validation": {},
            "technician_validation": {},
            "location_validation": {},
            "budget_validation": {}
        }

        # 1. Validate Parts Availability
        if required_parts:
            parts_result = await self.validate_parts_availability(required_parts)
            validation_result["parts_validation"] = parts_result

            if not parts_result["all_available"]:
                validation_result["valid"] = False
                validation_result["issues"].extend(parts_result["issues"])

            if parts_result.get("recommendations"):
                validation_result["recommendations"].extend(parts_result["recommendations"])

        # 2. Validate Technician Skills
        if required_skills:
            tech_result = await self.validate_technician_availability(required_skills)
            validation_result["technician_validation"] = tech_result

            if not tech_result["technicians_available"]:
                validation_result["valid"] = False
                validation_result["issues"].append(
                    f"No available technicians with required skills: {required_skills}"
                )
            else:
                validation_result["recommendations"].append(
                    f"Recommended technician: {tech_result['recommended_technician']['name']}"
                )

        # 3. Validate Location/Asset
        if location:
            location_result = await self.validate_location(location)
            validation_result["location_validation"] = location_result

            if not location_result["location_found"]:
                validation_result["issues"].append(
                    f"Location not found in SAP: {location}"
                )

        # 4. Validate Budget
        if cost_center_id and estimated_cost > 0:
            budget_result = await self.validate_budget(cost_center_id, estimated_cost)
            validation_result["budget_validation"] = budget_result

            if not budget_result["budget_sufficient"]:
                validation_result["valid"] = False
                validation_result["issues"].append(
                    f"Insufficient budget in cost center {cost_center_id}"
                )

        return validation_result

    async def validate_parts_availability(self, required_parts: str) -> Dict:
        """
        Check if required parts are available in inventory

        Args:
            required_parts: Comma-separated list of part descriptions
                e.g., "Air filter, Coolant, Thermostat"

        Returns:
            {
                "all_available": bool,
                "parts_status": [...],
                "issues": [...],
                "recommendations": [...]
            }
        """
        result = {
            "all_available": True,
            "parts_status": [],
            "issues": [],
            "recommendations": []
        }

        # Parse required parts
        parts_list = [p.strip().lower() for p in required_parts.split(",")]

        for part_desc in parts_list:
            # Strip trailing quantity/unit info like "(40 meters)", "(1 units)", "(2 nos)"
            # so "33kV Underground Cable XLPE 3-Core 300mm² (40 meters)" becomes
            # "33kV Underground Cable XLPE 3-Core 300mm²" which matches the DB
            clean_desc = re.sub(r'\s*\(\d+\s*\w+\)\s*$', '', part_desc).strip()

            # Search: try clean name first, fall back to original
            search_terms = [clean_desc] if clean_desc != part_desc else []
            search_terms.append(part_desc)

            materials = []
            for term in search_terms:
                stmt = select(Material).filter(
                    Material.description.ilike(f"%{term}%")
                )
                query_result = await self.db.execute(stmt)
                materials = query_result.scalars().all()
                if materials:
                    break

            if not materials:
                result["all_available"] = False
                result["issues"].append(f"Part not found in inventory: {part_desc}")
                result["parts_status"].append({
                    "part": part_desc,
                    "available": False,
                    "quantity": 0,
                    "material_id": None
                })
            else:
                # Check quantity for each match
                available_materials = []
                for material in materials:
                    if material.quantity > 0:
                        available_materials.append({
                            "material_id": material.material_id,
                            "description": material.description,
                            "quantity": material.quantity,
                            "storage_location": material.storage_location,
                            "below_reorder": material.is_below_reorder_level()
                        })

                if available_materials:
                    best_match = available_materials[0]
                    result["parts_status"].append({
                        "part": part_desc,
                        "available": True,
                        "quantity": best_match["quantity"],
                        "material_id": best_match["material_id"],
                        "storage_location": best_match["storage_location"]
                    })

                    # Check if below reorder level
                    if best_match["below_reorder"]:
                        result["recommendations"].append(
                            f"Material {best_match['material_id']} is below reorder level"
                        )
                else:
                    result["all_available"] = False
                    result["issues"].append(
                        f"Part found but out of stock: {part_desc}"
                    )
                    result["parts_status"].append({
                        "part": part_desc,
                        "available": False,
                        "quantity": 0,
                        "material_id": materials[0].material_id
                    })

        return result

    async def validate_technician_availability(self, required_skills: str) -> Dict:
        """
        Check if technicians with required skills are available

        Args:
            required_skills: Comma-separated skills
                e.g., "HVAC Certified, Electrical Safety"

        Returns:
            {
                "technicians_available": bool,
                "matching_technicians": [...],
                "recommended_technician": {...}
            }
        """
        result = {
            "technicians_available": False,
            "matching_technicians": [],
            "recommended_technician": None
        }

        # Parse required skills
        skills_list = [s.strip().lower() for s in required_skills.split(",")]

        # Query technicians table
        query = text("""
            SELECT technician_id, name, skills, certification_level,
                   availability_status, assigned_territory, phone, email
            FROM core.technicians
            WHERE availability_status = 'Available'
        """)

        query_result = await self.db.execute(query)
        technicians = query_result.fetchall()

        for tech in technicians:
            tech_skills_lower = tech.skills.lower()

            # Check if technician has all required skills
            has_all_skills = all(
                skill in tech_skills_lower for skill in skills_list
            )

            if has_all_skills:
                tech_data = {
                    "technician_id": tech.technician_id,
                    "name": tech.name,
                    "skills": tech.skills,
                    "certification_level": tech.certification_level,
                    "assigned_territory": tech.assigned_territory,
                    "phone": tech.phone,
                    "email": tech.email
                }
                result["matching_technicians"].append(tech_data)

        if result["matching_technicians"]:
            result["technicians_available"] = True

            # Recommend senior technician first
            senior_techs = [
                t for t in result["matching_technicians"]
                if t["certification_level"] == "Senior"
            ]

            if senior_techs:
                result["recommended_technician"] = senior_techs[0]
            else:
                result["recommended_technician"] = result["matching_technicians"][0]

        return result

    async def validate_location(self, location: str) -> Dict:
        """
        Validate if location exists in SAP asset database

        Args:
            location: Location string to search for

        Returns:
            {
                "location_found": bool,
                "matching_assets": [...],
                "nearest_asset": {...}
            }
        """
        result = {
            "location_found": False,
            "matching_assets": [],
            "nearest_asset": None
        }

        # Search for assets matching location
        stmt = select(Asset).filter(
            Asset.location.ilike(f"%{location}%")
        )
        query_result = await self.db.execute(stmt)
        assets = query_result.scalars().all()

        if assets:
            result["location_found"] = True

            for asset in assets:
                result["matching_assets"].append({
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "location": asset.location,
                    "status": asset.status.value,
                    "asset_type": asset.asset_type.value
                })

            # Find operational asset
            operational = [
                a for a in result["matching_assets"]
                if a["status"] == "operational"
            ]

            if operational:
                result["nearest_asset"] = operational[0]
            else:
                result["nearest_asset"] = result["matching_assets"][0]

        return result

    async def validate_budget(self, cost_center_id: str, estimated_cost: float) -> Dict:
        """
        Check if cost center has sufficient budget

        Args:
            cost_center_id: Cost center ID
            estimated_cost: Estimated cost of appointment

        Returns:
            {
                "budget_sufficient": bool,
                "cost_center": {...},
                "available_budget": float,
                "budget_utilization": float
            }
        """
        result = {
            "budget_sufficient": False,
            "cost_center": None,
            "available_budget": 0.0,
            "budget_utilization": 0.0
        }

        # Query cost center
        stmt = select(CostCenter).filter(
            CostCenter.cost_center_id == cost_center_id
        )
        query_result = await self.db.execute(stmt)
        cost_center = query_result.scalars().first()

        if cost_center:
            available = float(cost_center.budget_allocated - cost_center.budget_spent)
            utilization = (float(cost_center.budget_spent) / float(cost_center.budget_allocated)) * 100

            result["cost_center"] = {
                "cost_center_id": cost_center.cost_center_id,
                "name": cost_center.name,
                "budget_allocated": float(cost_center.budget_allocated),
                "budget_spent": float(cost_center.budget_spent),
                "responsible_manager": cost_center.responsible_manager
            }
            result["available_budget"] = available
            result["budget_utilization"] = round(utilization, 2)

            # Check if sufficient budget
            if available >= estimated_cost:
                result["budget_sufficient"] = True

        return result

    async def get_material_recommendations(self, asset_id: Optional[str] = None) -> List[Dict]:
        """
        Get recommended materials based on asset type or common parts

        Returns list of commonly used materials
        """
        # Get top materials by quantity
        stmt = select(Material).filter(
            Material.quantity > 0
        ).order_by(Material.quantity.desc()).limit(10)
        query_result = await self.db.execute(stmt)
        materials = query_result.scalars().all()

        recommendations = []
        for material in materials:
            recommendations.append({
                "material_id": material.material_id,
                "description": material.description,
                "quantity": material.quantity,
                "storage_location": material.storage_location,
                "unit_of_measure": material.unit_of_measure
            })

        return recommendations

    async def get_available_technicians(self, skill: Optional[str] = None) -> List[Dict]:
        """
        Get list of available technicians, optionally filtered by skill

        Returns list of available technicians
        """
        query_str = """
            SELECT technician_id, name, skills, certification_level,
                   availability_status, assigned_territory, phone, email
            FROM core.technicians
            WHERE availability_status = 'Available'
        """

        if skill:
            query_str += f" AND skills ILIKE '%{skill}%'"

        query_str += " ORDER BY certification_level DESC"

        query_result = await self.db.execute(text(query_str))
        technicians = query_result.fetchall()

        result = []
        for tech in technicians:
            result.append({
                "technician_id": tech.technician_id,
                "name": tech.name,
                "skills": tech.skills,
                "certification_level": tech.certification_level,
                "assigned_territory": tech.assigned_territory,
                "phone": tech.phone,
                "email": tech.email
            })

        return result
