#!/usr/bin/env python3
"""
Initialize password reset ticket tables in both MuleSoft and SAP databases.
Run this script to create the database tables for persistent storage.
"""
import asyncio
import sys
import os

# Add paths
sys.path.insert(0, '/home/pradeep1a/Network-apps/Mulesoft-Application/Inte-platform/platform-backend')
sys.path.insert(0, '/home/pradeep1a/Network-apps/SAP_clone/backend')


async def init_mulesoft_db():
    """Initialize MuleSoft database tables"""
    print("Initializing MuleSoft password reset tables...")
    try:
        from app.database import Base, engine
        from app.models import PasswordResetTicket

        Base.metadata.create_all(bind=engine)
        print("✓ MuleSoft tables created successfully")
        return True
    except Exception as e:
        print(f"✗ MuleSoft initialization failed: {e}")
        return False


async def init_sap_db():
    """Initialize SAP database tables"""
    print("Initializing SAP password reset tables...")
    try:
        from backend.db.database import Base, init_db
        from backend.db.models import PasswordResetTicket

        await init_db()
        print("✓ SAP tables created successfully")
        return True
    except Exception as e:
        print(f"✗ SAP initialization failed: {e}")
        return False


async def main():
    print("=" * 60)
    print("Password Reset Ticket Database Initialization")
    print("=" * 60)
    print()

    mulesoft_ok = await init_mulesoft_db()
    print()
    sap_ok = await init_sap_db()
    print()

    if mulesoft_ok and sap_ok:
        print("=" * 60)
        print("✓ All tables created successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart containers: docker-compose restart mulesoft-backend sap-backend")
        print("2. Tickets will now persist after container restarts")
    else:
        print("=" * 60)
        print("✗ Some tables failed to create. Check errors above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
