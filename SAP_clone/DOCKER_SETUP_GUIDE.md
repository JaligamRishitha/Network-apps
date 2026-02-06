# Docker Setup Guide

## Current Situation

You have **10 containers** running, but you only need **3** for the core application to work.

## Container Breakdown

### ✅ Essential (Always Needed)
1. **postgres** - Database for storing all data
2. **backend** - FastAPI backend API
3. **frontend** - React UI application

### ⚠️ Optional (Can be disabled)
4. **kong** - API Gateway (adds routing, rate limiting, authentication)
5. **camel** - Integration layer (only for electricity load requests via MuleSoft)
6. **itsm-mock** - Mock ITSM service (only used by camel)
7. **erp-mock** - Mock ERP service (only used by camel)
8. **crm-mock** - Mock CRM service (only used by camel)
9. **prometheus** - Metrics collection (monitoring)
10. **grafana** - Metrics dashboard (monitoring)

## Options

### Option 1: Minimal Setup (Recommended for Development)

Use only the 3 essential containers:

```bash
# Use the minimal docker-compose
docker-compose -f docker-compose.minimal.yml up -d

# Or stop all and start minimal
docker-compose down
docker-compose -f docker-compose.minimal.yml up -d
```

**What works:**
- ✅ Login and authentication
- ✅ User management
- ✅ All tickets (PM, MM, FI)
- ✅ All SAP modules
- ✅ Dashboard
- ❌ Electricity load requests (needs camel + mocks)
- ❌ API Gateway features (needs kong)
- ❌ Monitoring dashboards (needs prometheus + grafana)

### Option 2: With Integration Layer

If you need the electricity load request feature:

```bash
# Start core + integration services
docker-compose -f docker-compose.full.yml --profile integration up -d
```

**Adds:**
- ✅ Electricity load requests
- ✅ MuleSoft integration
- ✅ Mock external services

### Option 3: With Monitoring

If you want metrics and dashboards:

```bash
# Start core + monitoring services
docker-compose -f docker-compose.full.yml --profile monitoring up -d
```

**Adds:**
- ✅ Prometheus metrics
- ✅ Grafana dashboards
- ✅ Performance monitoring

### Option 4: Full Setup (Everything)

Run all services:

```bash
# Start everything
docker-compose -f docker-compose.full.yml --profile full up -d

# Or use the original docker-compose.yml
docker-compose up -d
```

## Recommendation

**For most development work, use Option 1 (Minimal Setup):**

```bash
docker-compose -f docker-compose.minimal.yml up -d
```

This gives you:
- Faster startup time
- Less memory usage
- Simpler debugging
- All core features working

**Only enable optional services when you specifically need them.**

## Updating Your Current Setup

If you want to switch to minimal setup:

```bash
# Stop all current containers
docker-compose down

# Start minimal setup
docker-compose -f docker-compose.minimal.yml up -d

# Check status
docker-compose -f docker-compose.minimal.yml ps
```

## Making Minimal the Default

If you want to make the minimal setup your default, you can:

1. **Backup current docker-compose.yml:**
   ```bash
   copy docker-compose.yml docker-compose.backup.yml
   ```

2. **Replace with minimal:**
   ```bash
   copy docker-compose.minimal.yml docker-compose.yml
   ```

3. **Now you can use normal commands:**
   ```bash
   docker-compose up -d
   docker-compose down
   docker-compose logs -f
   ```

## Resource Usage Comparison

### Full Setup (10 containers)
- Memory: ~4-6 GB
- Startup time: ~60-90 seconds
- Disk space: ~3-4 GB

### Minimal Setup (3 containers)
- Memory: ~1-2 GB
- Startup time: ~15-30 seconds
- Disk space: ~1 GB

## Summary

**You don't need all those containers!** The minimal setup with just postgres, backend, and frontend is enough for 95% of your development work. Only add the optional services when you specifically need their features.
