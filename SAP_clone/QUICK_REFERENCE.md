# ⚡ Electricity Load Integration - Quick Reference

## 🚀 Start Testing in 30 Seconds

```bash
# 1. Start backend
docker-compose up backend

# 2. Run test (in new terminal)
test_electricity_api.bat

# 3. Done! ✓
```

## 📡 API Endpoints

### JSON
```bash
POST http://localhost:8000/api/integration/mulesoft/load-request
```

### XML
```bash
POST http://localhost:8000/api/integration/mulesoft/load-request/xml
```

## 📋 Sample Request

```json
{
  "RequestID": "SF-REQ-10021",
  "CustomerID": "CUST-88991",
  "CurrentLoad": 5,
  "RequestedLoad": 10,
  "ConnectionType": "RESIDENTIAL",
  "City": "Hyderabad",
  "PinCode": "500081"
}
```

## 📊 Business Rules

| Load Increase | Priority | Tickets Created |
|--------------|----------|-----------------|
| < 5 kW | P4 | PM only |
| 5-10 kW | P3 | PM + FI |
| 10-20 kW | P2 | PM + FI |
| > 20 kW | P1 | PM + FI + MM |

## 🧪 Test Commands

```bash
# Windows
test_electricity_api.bat

# Python
python backend/tests/test_electricity_integration.py

# Linux/Mac
./curl_examples.sh

# Swagger UI
http://localhost:8000/docs
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| README_ELECTRICITY_INTEGRATION.md | Main guide |
| QUICK_TEST_ELECTRICITY.md | Quick start |
| IMPLEMENTATION_COMPLETE.md | Full summary |

## ✅ What It Does

1. Receives load request from MuleSoft
2. Calculates cost and priority
3. Creates tickets (PM/FI/MM)
4. Returns ticket IDs
5. Logs events

## 🎯 Example Response

```json
{
  "status": "accepted",
  "estimated_cost": 17500.0,
  "priority": "P3",
  "tickets_created": {
    "pm_ticket": "TKT-PM-20260120-0001",
    "fi_ticket": "TKT-FI-20260120-0001",
    "mm_ticket": null
  }
}
```

## 🔍 Verify Tickets

```bash
curl http://localhost:8000/api/v1/pm/tickets
curl http://localhost:8000/api/v1/fi/tickets
curl http://localhost:8000/api/v1/mm/tickets
```

## 💡 Cost Formula

```
Base: ₹5,000
Residential: ₹2,500/kW
Commercial: ₹3,500/kW

Total = Base + (Increase × Rate)
```

## 🎓 Examples

**Small (3→5 kW)**: ₹10,000, PM only
**Medium (5→10 kW)**: ₹17,500, PM+FI
**Large (10→30 kW)**: ₹75,000, PM+FI+MM

---

**Status**: ✅ Ready to Use
**Version**: 1.0.0
