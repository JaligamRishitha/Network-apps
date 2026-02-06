# Database Migration Quick Reference Card

## 🚀 Quick Start Commands

### Run ALL Migrations
```bash
cd /home/pradeep1a/Network-apps
python3 run_all_migrations.py
```

### Run Individual Application Migrations

```bash
# SAP Clone
cd SAP_clone/backend && python3 run_migrations.py

# Mulesoft
cd Mulesoft-Application/Inte-platform/platform-backend && python3 run_migrations.py

# ServiceNow
cd serviceNow/backend && python3 run_migrations.py
```

## 📊 Check Status

```bash
# Check current migration version
alembic current

# View migration history
alembic history --verbose

# Show SQL without executing
alembic upgrade head --sql
```

## ⬆️ Upgrade

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision_id>

# Upgrade one version forward
alembic upgrade +1
```

## ⬇️ Downgrade / Rollback

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

## 🆕 Create New Migration

```bash
# Create empty migration
alembic revision -m "description"

# Auto-generate from model changes
alembic revision --autogenerate -m "description"

# Always review auto-generated migrations before running!
```

## 🔍 Inspection

```bash
# Show current revision
alembic current

# Show pending migrations
alembic upgrade head --sql > preview.sql

# Show migration details
alembic show <revision_id>
```

## 🛠️ Advanced Operations

```bash
# Stamp database to specific version (without running migrations)
alembic stamp <revision_id>

# Merge multiple head revisions
alembic merge heads -m "merge message"

# Show branches
alembic branches
```

## 📦 Applications & Databases

| Application | Database | Tables | Migration Files |
|------------|----------|--------|----------------|
| **SAP Clone** | PostgreSQL | 20+ | 001-009 |
| **Mulesoft** | SQLite | 9 | 001 |
| **ServiceNow** | SQLite | 13 | 001 |
| **Salesforce** | SQLite | N/A | SQL files |

## ⚡ One-Liners

```bash
# Run all migrations and check status
python3 run_all_migrations.py && echo "✓ All migrations complete"

# Rollback all applications (use with caution!)
for app in SAP_clone/backend Mulesoft-Application/Inte-platform/platform-backend serviceNow/backend; do
    cd $app && alembic downgrade -1 && cd -
done

# Check all application statuses
for app in SAP_clone/backend Mulesoft-Application/Inte-platform/platform-backend serviceNow/backend; do
    echo "=== $app ===" && cd $app && alembic current && cd -
done
```

## 🚨 Common Issues & Solutions

### Issue: "Can't locate revision identified by 'head'"
**Solution:** Database not initialized. Run `alembic upgrade head`

### Issue: "Table already exists"
**Solution:** Database already has schema. Run `alembic stamp head` to mark as migrated

### Issue: "Multiple head revisions"
**Solution:** Merge branches: `alembic merge heads -m "merge"`

### Issue: "Target database is not up to date"
**Solution:** Run `alembic upgrade head` first

### Issue: "No module named 'alembic'"
**Solution:** Install dependencies: `pip install alembic sqlalchemy`

## 🔒 Safety Checklist

Before running migrations in production:

- [ ] Backup database
- [ ] Test migrations in staging
- [ ] Review migration SQL
- [ ] Check disk space
- [ ] Verify connection string
- [ ] Plan rollback strategy
- [ ] Schedule maintenance window
- [ ] Notify stakeholders

## 📞 Getting Help

- Full documentation: `DATABASE_MIGRATIONS_README.md`
- Alembic docs: https://alembic.sqlalchemy.org/
- SQLAlchemy docs: https://docs.sqlalchemy.org/

---
**Pro Tip:** Always test migrations in a development environment first!
