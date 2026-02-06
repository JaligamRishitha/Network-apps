# Salesforce Backend SQL Migrations

This directory contains SQL migration files for the Salesforce backend application.

## Existing Migrations

1. `add_service_scenarios.sql` - Adds service-related scenarios
2. `add_service_and_fix_accounts.sql` - Updates service and account configurations

## Running SQL Migrations

These migrations are manual SQL scripts and should be run directly against the database:

```bash
# For SQLite
sqlite3 /path/to/salesforce.db < migrations/add_service_scenarios.sql
sqlite3 /path/to/salesforce.db < migrations/add_service_and_fix_accounts.sql

# For PostgreSQL
psql -U username -d database_name -f migrations/add_service_scenarios.sql
psql -U username -d database_name -f migrations/add_service_and_fix_accounts.sql
```

## Converting to Alembic (Optional)

If you want to use Alembic for version control like the other applications:

1. Initialize Alembic:
```bash
cd /home/pradeep1a/Network-apps/Salesforce/backend
alembic init alembic
```

2. Update `alembic/env.py` to import your models

3. Create initial migration:
```bash
alembic revision --autogenerate -m "initial migration"
```

4. Review and run:
```bash
alembic upgrade head
```

## Note

The Salesforce application currently uses SQL-based migrations instead of Alembic. This is a simpler approach suitable for smaller applications with infrequent schema changes.

For consistency with other applications, consider migrating to Alembic using the steps above.
