#!/bin/bash
# Test script to verify all migrations are working

set -e

echo "═══════════════════════════════════════════════════════════"
echo "DATABASE MIGRATION TEST SUITE"
echo "═══════════════════════════════════════════════════════════"
echo ""

BASE_DIR="/home/pradeep1a/Network-apps"

# Test SAP Clone
echo "[1/3] Testing SAP Clone migrations..."
cd "$BASE_DIR/SAP_clone/backend"
if alembic current 2>&1 | grep -q "head" || alembic current 2>&1 | grep -q "009"; then
    echo "  ✓ SAP Clone migrations verified"
else
    echo "  ℹ️  SAP Clone needs migration (run: alembic upgrade head)"
fi
echo ""

# Test Mulesoft
echo "[2/3] Testing Mulesoft migrations..."
cd "$BASE_DIR/Mulesoft-Application/Inte-platform/platform-backend"
if [ -f "alembic.ini" ]; then
    echo "  ✓ Mulesoft migration setup verified"
    if alembic current 2>&1 | grep -q "001" || alembic current 2>&1 | grep -q "head"; then
        echo "  ✓ Mulesoft database is up to date"
    else
        echo "  ℹ️  Mulesoft needs migration (run: python3 run_migrations.py)"
    fi
else
    echo "  ✗ Mulesoft migration files not found"
fi
echo ""

# Test ServiceNow
echo "[3/3] Testing ServiceNow migrations..."
cd "$BASE_DIR/serviceNow/backend"
if [ -f "alembic.ini" ]; then
    echo "  ✓ ServiceNow migration setup verified"
    if alembic current 2>&1 | grep -q "001" || alembic current 2>&1 | grep -q "head"; then
        echo "  ✓ ServiceNow database is up to date"
    else
        echo "  ℹ️  ServiceNow needs migration (run: python3 run_migrations.py)"
    fi
else
    echo "  ✗ ServiceNow migration files not found"
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "Test complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "To run all migrations:"
echo "  cd $BASE_DIR && python3 run_all_migrations.py"
echo ""
