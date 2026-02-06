"""
Script to delete Load Enhancement Request tickets created on 20/1/2026
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.insert(0, '/app')

from backend.db.database import _get_session_factory
from backend.models.ticket_models import Ticket


async def delete_tickets_by_date():
    """Delete tickets created on 2026-01-20"""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        # Define the date range for 20/1/2026
        start_date = datetime(2026, 1, 20, 0, 0, 0)
        end_date = datetime(2026, 1, 21, 0, 0, 0)
        
        # Find tickets created on that date with "Load Enhancement" in title
        stmt = select(Ticket).where(
            Ticket.created_at >= start_date,
            Ticket.created_at < end_date,
            Ticket.title.like('%Load Enhancement%')
        )
        
        result = await session.execute(stmt)
        tickets = result.scalars().all()
        
        if not tickets:
            print("No Load Enhancement tickets found for 20/1/2026")
            return
        
        print(f"Found {len(tickets)} Load Enhancement tickets created on 20/1/2026:")
        for ticket in tickets:
            print(f"  - {ticket.ticket_id}: {ticket.title} (Created: {ticket.created_at})")
        
        # Confirm deletion
        print("\nProceeding with deletion...")
        # Auto-confirm for script execution
        
        # Delete the tickets (cascade will delete audit entries)
        delete_stmt = delete(Ticket).where(
            Ticket.created_at >= start_date,
            Ticket.created_at < end_date,
            Ticket.title.like('%Load Enhancement%')
        )
        
        result = await session.execute(delete_stmt)
        await session.commit()
        
        print(f"\nDeleted {result.rowcount} tickets successfully!")


if __name__ == "__main__":
    asyncio.run(delete_tickets_by_date())
