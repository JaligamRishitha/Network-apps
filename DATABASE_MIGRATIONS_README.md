# Database Migrations Guide

This document provides comprehensive information about database migrations for all applications in the Network-apps project.

## Overview

Database migrations have been set up for the following applications:

1. **SAP_clone** - SAP ERP Backend (PostgreSQL/SQLite)
2. **Mulesoft-Application** - Integration Platform (SQLite)
3. **serviceNow** - ServiceNow Backend (SQLite)
4. **Salesforce** - Salesforce Integration (SQL migrations)

## Migration Framework

All applications use **Alembic** for database migrations, which provides:
- Version control for database schema
- Automatic schema migration generation
- Rollback capabilities
- Support for multiple database engines

## Directory Structure

```
Network-apps/
├── run_all_migrations.py              # Master script to run all migrations
│
├── SAP_clone/backend/
│   ├── alembic.ini                    # Alembic configuration
│   ├── run_migrations.py              # SAP migration runner
│   └── alembic/
│       ├── env.py                     # Alembic environment setup
│       ├── script.py.mako             # Migration template
│       └── versions/
│           ├── 001_create_schemas.py
│           ├── ...
│           └── 009_add_password_reset_tickets.py  # NEW
│
├── Mulesoft-Application/Inte-platform/platform-backend/
│   ├── alembic.ini                    # Alembic configuration
│   ├── run_migrations.py              # Mulesoft migration runner
│   └── alembic/
│       ├── env.py                     # Alembic environment setup
│       ├── script.py.mako             # Migration template
│       └── versions/
│           └── 001_initial_migration.py  # NEW
│
└── serviceNow/backend/
    ├── alembic.ini                    # Alembic configuration
    ├── run_migrations.py              # ServiceNow migration runner
    └── alembic/
        ├── env.py                     # Alembic environment setup
        ├── script.py.mako             # Migration template
        └── versions/
            └── 001_initial_migration.py  # NEW
```

## Quick Start

### Run All Migrations

To run migrations for all applications at once:

```bash
cd /home/pradeep1a/Network-apps
python3 run_all_migrations.py
```

### Run Individual Application Migrations

#### SAP Clone
```bash
cd /home/pradeep1a/Network-apps/SAP_clone/backend
python3 run_migrations.py
```

#### Mulesoft Integration Platform
```bash
cd /home/pradeep1a/Network-apps/Mulesoft-Application/Inte-platform/platform-backend
python3 run_migrations.py
```

#### ServiceNow Backend
```bash
cd /home/pradeep1a/Network-apps/serviceNow/backend
python3 run_migrations.py
```

## Database Tables Created

### SAP Clone (009_add_password_reset_tickets)

**password_reset_tickets**
- id (Primary Key)
- sap_ticket_id (Unique Index)
- servicenow_ticket_id
- username
- user_email
- requester_name
- requester_email
- reason
- priority
- status
- assigned_to
- correlation_id
- callback_url
- temp_password
- comments (JSON)
- created_at
- updated_at

### Mulesoft Integration Platform (001_initial_migration)

**Tables:**
1. **users** - User accounts with roles (admin, developer, viewer)
2. **integrations** - Integration flow configurations
3. **integration_logs** - Logging for integration executions
4. **api_endpoints** - API endpoint configurations
5. **api_keys** - API key management
6. **connectors** - External system connectors (SAP, Salesforce, ServiceNow, etc.)
7. **salesforce_cases** - Synchronized Salesforce cases
8. **password_reset_tickets** - Password reset workflow tracking
9. **user_creation_approvals** - User creation approval workflow

### ServiceNow Backend (001_initial_migration)

**Tables:**
1. **users** - User accounts (admin, agent, user roles)
2. **incidents** - Incident management
3. **service_catalog_items** - Service catalog items
4. **knowledge_articles** - Knowledge base articles
5. **tickets** - Main ticketing system
6. **approvals** - Ticket approval workflow
7. **assignment_groups** - Support team groups
8. **assignment_group_members** - Group membership
9. **category_assignment_mappings** - Auto-assignment rules
10. **sla_definitions** - SLA policies
11. **ticket_slas** - Active SLA tracking per ticket
12. **notifications** - Notification queue and history

## Advanced Usage

### Check Current Migration Version

```bash
cd <application-directory>
alembic current
```

### View Migration History

```bash
cd <application-directory>
alembic history
```

### Upgrade to Specific Version

```bash
cd <application-directory>
alembic upgrade <revision_id>
```

### Rollback Migration

```bash
cd <application-directory>
alembic downgrade -1  # Rollback one version
```

Or rollback to a specific version:

```bash
cd <application-directory>
alembic downgrade <revision_id>
```

### Create New Migration

```bash
cd <application-directory>
alembic revision -m "description of changes"
```

### Auto-generate Migration from Model Changes

```bash
cd <application-directory>
alembic revision --autogenerate -m "description of changes"
```

**Note:** Always review auto-generated migrations before applying them!

## Database Configuration

### SAP Clone
- Uses PostgreSQL by default
- Connection string in `alembic.ini`: `postgresql+asyncpg://sapuser:sappassword@localhost:5432/saperp`
- Can be overridden via environment variable `DATABASE_URL`

### Mulesoft Integration Platform
- Uses SQLite by default
- Database file: `integration_platform.db`
- Connection string in `alembic.ini`: `sqlite:///./integration_platform.db`

### ServiceNow Backend
- Uses SQLite by default
- Database file: `servicenow.db`
- Connection string in `alembic.ini`: `sqlite:///./servicenow.db`

## Troubleshooting

### Migration Script Not Found
If you see "Migration script not found", ensure you're in the correct directory and the script has execute permissions:

```bash
chmod +x run_migrations.py
```

### Database Connection Error
1. Verify database is running (for PostgreSQL/MySQL)
2. Check connection string in `alembic.ini`
3. Ensure database user has proper permissions

### Migration Conflict
If you see "Multiple head revisions" error:

```bash
alembic merge heads -m "merge conflicting revisions"
alembic upgrade head
```

### Already Exists Error
If table already exists, you may need to stamp the database:

```bash
alembic stamp head  # Mark current state as migrated
```

## Best Practices

1. **Always backup your database** before running migrations in production
2. **Review auto-generated migrations** - they may not always be correct
3. **Test migrations** in a development environment first
4. **Use descriptive revision messages** for better tracking
5. **Never edit applied migrations** - create a new migration instead
6. **Keep migrations small** - one logical change per migration
7. **Document complex migrations** with comments in the migration file

## Dependencies

Ensure you have the required Python packages:

```bash
pip install alembic sqlalchemy
```

For PostgreSQL support:
```bash
pip install psycopg2-binary
# or
pip install asyncpg
```

## Integration with Docker

If running applications in Docker, migrations can be run as part of the container startup:

```dockerfile
# In your Dockerfile
COPY alembic.ini alembic/ ./
RUN python run_migrations.py
```

Or as a separate init container in docker-compose:

```yaml
services:
  db-migrate:
    image: your-app:latest
    command: python run_migrations.py
    depends_on:
      - database
```

## Support

For issues or questions about migrations:
1. Check the migration output for specific error messages
2. Verify database connectivity
3. Review the Alembic documentation: https://alembic.sqlalchemy.org/
4. Check application-specific README files

## Files Created

This migration setup created the following new files:

### SAP Clone
- `SAP_clone/backend/alembic/versions/009_add_password_reset_tickets.py`

### Mulesoft
- `Mulesoft-Application/Inte-platform/platform-backend/alembic.ini`
- `Mulesoft-Application/Inte-platform/platform-backend/alembic/env.py`
- `Mulesoft-Application/Inte-platform/platform-backend/alembic/script.py.mako`
- `Mulesoft-Application/Inte-platform/platform-backend/alembic/versions/001_initial_migration.py`
- `Mulesoft-Application/Inte-platform/platform-backend/run_migrations.py`

### ServiceNow
- `serviceNow/backend/alembic.ini`
- `serviceNow/backend/alembic/env.py`
- `serviceNow/backend/alembic/script.py.mako`
- `serviceNow/backend/alembic/versions/001_initial_migration.py`
- `serviceNow/backend/run_migrations.py`

### Root Level
- `run_all_migrations.py` - Master migration orchestrator

---

**Last Updated:** 2026-02-06
**Version:** 1.0
