"""
Script to delete all Load Enhancement Request tickets
"""
import asyncio
import sys
from sqlalchemy import select, delete

# Add parent directory to path
sys.path.insert(0, '/app')

from backend.db.database import _get_session_factory
from backend.models.ticket_models import Ticket


async def delete_all_load_requests():
    """Delete all Load Enhancement tickets"""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        # Find all tickets with "Load Enhancement" in title
        stmt = select(Ticket).where(
            Ticket.title.like('%Load Enhancement%')
        )
        
        result = await session.execute(stmt)
        tickets = result.scalars().all()
        
        if not tickets:
            print("No Load Enhancement tickets found")
            return
        
        print(f"Found {len(tickets)} Load Enhancement tickets:")
        for ticket in tickets:
            print(f"  - {ticket.ticket_id}: {ticket.title} (Created: {ticket.created_at})")
        
        print("\nProceeding with deletion...")
        
        # Delete the tickets (cascade will delete audit entries)
        delete_stmt = delete(Ticket).where(
            Ticket.title.like('%Load Enhancement%')
        )
        
        result = await session.execute(delete_stmt)
        await session.commit()
        
        print(f"\nDeleted {result.rowcount} tickets successfully!")


if __name__ == "__main__":
    asyncio.run(delete_all_load_requests())
