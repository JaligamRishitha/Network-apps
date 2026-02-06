#!/usr/bin/env python3
"""
Run Alembic migrations for ServiceNow Backend
"""
import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations"""
    # Get the directory containing this script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Create Alembic config
    alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))

    print("=" * 60)
    print("Running ServiceNow Backend Migrations")
    print("=" * 60)

    try:
        # Run upgrade to head
        print("\n[1/2] Upgrading database to latest version...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Database upgraded successfully!")

        # Show current revision
        print("\n[2/2] Checking current database version...")
        command.current(alembic_cfg)

        print("\n" + "=" * 60)
        print("✓ Migrations completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
