#!/usr/bin/env python3
"""
Master script to run all database migrations across all applications
"""
import os
import sys
import subprocess
from pathlib import Path

# Define migration locations for each application
MIGRATIONS = {
    "SAP_clone": {
        "path": "SAP_clone/backend",
        "script": "run_migrations.py",
        "description": "SAP ERP Backend"
    },
    "Mulesoft": {
        "path": "Mulesoft-Application/Inte-platform/platform-backend",
        "script": "run_migrations.py",
        "description": "Mulesoft Integration Platform"
    },
    "ServiceNow": {
        "path": "serviceNow/backend",
        "script": "run_migrations.py",
        "description": "ServiceNow Backend"
    }
}

def run_migration(app_name, config):
    """Run migration for a specific application"""
    print("\n" + "=" * 80)
    print(f"MIGRATING: {app_name} - {config['description']}")
    print("=" * 80)

    base_dir = Path(__file__).parent
    migration_dir = base_dir / config['path']
    script_path = migration_dir / config['script']

    # Check if migration script exists
    if not script_path.exists():
        print(f"⚠ Warning: Migration script not found at {script_path}")
        print(f"  Skipping {app_name}...")
        return False

    # Change to migration directory and run script
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(migration_dir),
            capture_output=True,
            text=True
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            print(f"\n✗ Migration failed for {app_name}")
            if result.stderr:
                print("Error output:")
                print(result.stderr)
            return False

        print(f"✓ {app_name} migration completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Error running migration for {app_name}: {str(e)}")
        return False

def main():
    """Run all migrations"""
    print("=" * 80)
    print("DATABASE MIGRATION ORCHESTRATOR")
    print("Running migrations for all applications...")
    print("=" * 80)

    results = {}

    for app_name, config in MIGRATIONS.items():
        success = run_migration(app_name, config)
        results[app_name] = success

    # Print summary
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)

    for app_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status:12} - {app_name}")

    # Exit with error if any migration failed
    if not all(results.values()):
        print("\n⚠ Some migrations failed. Please check the output above.")
        sys.exit(1)
    else:
        print("\n✓ All migrations completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
