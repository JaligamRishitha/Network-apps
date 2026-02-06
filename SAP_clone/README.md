# SAP ERP Demo System

A comprehensive enterprise resource planning (ERP) demonstration application featuring authentic SAP Fiori and SAP GUI Classic design patterns. This system showcases three core SAP modules with full integration capabilities, event-driven architecture, and enterprise-grade observability.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [User Guide](#user-guide)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

This SAP ERP Demo System is a full-stack application designed to demonstrate enterprise resource planning capabilities with an authentic SAP user experience. It implements three critical SAP modules:

- **Plant Maintenance (PM)**: Equipment lifecycle management, work orders, and maintenance scheduling
- **Materials Management (MM)**: Inventory control, procurement, and warehouse management
- **Financial Accounting (FI)**: Cost center management, approval workflows, and general ledger

The system features a modern microservices architecture with API gateway, event-driven integration, and comprehensive monitoring capabilities.

## Features

### User Interface

- **Authentic SAP Design**: Pixel-perfect recreation of SAP Fiori launchpad and SAP GUI Classic
- **Responsive Dashboard**: System health monitoring with real-time KPIs
- **Module Navigation**: Hierarchical menu structure with role-based access
- **Professional Components**: Tables, forms, dialogs, and status indicators matching SAP standards
- **SAP Color Palette**: Official Belize theme colors and typography

### Core Modules

#### Plant Maintenance (PM)
- Equipment master data management
- Work order creation and tracking
- Maintenance scheduling
- Equipment status monitoring
- Incident reporting and resolution
- Equipment hierarchy and relationships

#### Materials Management (MM)
- Material master data
- Inventory tracking and valuation
- Purchase requisitions and orders
- Automatic reorder point management
- Stock transactions (goods receipt/issue)
- Vendor management
- Storage location tracking

#### Financial Accounting (FI)
- Cost center management
- Budget planning and tracking
- Approval workflow system
- General ledger accounts
- Financial reporting
- Multi-level approval chains
- Cost allocation and tracking

### Integration & Infrastructure

- **API Gateway**: Kong for request routing, rate limiting, and security
- **Event Bus**: Apache Camel for event-driven integration
- **Mock Services**: ITSM, ERP, and CRM integration endpoints
- **Observability**: Prometheus metrics and Grafana dashboards
- **Authentication**: JWT-based security with role-based access control
- **Database**: PostgreSQL with async support and migrations

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React 18 + TypeScript + Vite                        │  │
│  │  - SAP Fiori Components                              │  │
│  │  - Ant Design UI Library                             │  │
│  │  - React Router for Navigation                       │  │
│  │  - Axios for API Communication                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Kong API Gateway                                    │  │
│  │  - Request Routing                                   │  │
│  │  - Rate Limiting                                     │  │
│  │  - Authentication                                    │  │
│  │  - Logging & Monitoring                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Python 3.11+)                      │  │
│  │  ┌────────────┬────────────┬────────────┐           │  │
│  │  │ PM Module  │ MM Module  │ FI Module  │           │  │
│  │  └────────────┴────────────┴────────────┘           │  │
│  │  ┌────────────────────────────────────────┐         │  │
│  │  │  Shared Services                       │         │  │
│  │  │  - Auth Service                        │         │  │
│  │  │  - Ticket Service                      │         │  │
│  │  │  - Event Service                       │         │  │
│  │  │  - Observability Service               │         │  │
│  │  └────────────────────────────────────────┘         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Integration Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Apache Camel                                        │  │
│  │  - Event Routing                                     │  │
│  │  - Message Transformation                            │  │
│  │  - External System Integration                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│  ITSM Mock   │      │  ERP Mock    │     │  CRM Mock    │
│  Service     │      │  Service     │     │  Service     │
└──────────────┘      └──────────────┘     └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 15                                       │  │
│  │  - Async SQLAlchemy ORM                              │  │
│  │  - Alembic Migrations                                │  │
│  │  - Connection Pooling                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Observability Layer                       │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │  Prometheus        │      │  Grafana           │        │
│  │  - Metrics         │─────▶│  - Dashboards      │        │
│  │  - Alerting        │      │  - Visualization   │        │
│  └────────────────────┘      └────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request**: Frontend sends authenticated request
2. **Gateway**: Kong validates and routes to backend
3. **Processing**: FastAPI processes business logic
4. **Events**: Camel routes events to external systems
5. **Storage**: PostgreSQL persists data
6. **Monitoring**: Prometheus collects metrics
7. **Response**: Data flows back through gateway to frontend

## Technology Stack

### Frontend
- **Framework**: React 18.2 with TypeScript
- **Build Tool**: Vite 5.0
- **UI Library**: Ant Design 5.13
- **Styling**: Tailwind CSS 3.4 + Custom SAP Theme
- **Routing**: React Router 6.21
- **HTTP Client**: Axios 1.6
- **State Management**: React Context API

### Backend
- **Framework**: FastAPI 0.109
- **Language**: Python 3.11+
- **Server**: Uvicorn with async support
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 15
- **Migrations**: Alembic 1.13
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic 2.5
- **Testing**: Pytest + Hypothesis

### Infrastructure
- **API Gateway**: Kong 3.4
- **Integration**: Apache Camel
- **Monitoring**: Prometheus 2.48
- **Visualization**: Grafana 10.2
- **Containerization**: Docker + Docker Compose
- **Database**: PostgreSQL 15 Alpine

## Getting Started

### Prerequisites

Ensure you have the following installed:

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Node.js**: Version 18+ (for local frontend development)
- **Python**: Version 3.11+ (for local backend development)
- **Git**: For cloning the repository

### Installation

1. **Clone the Repository**

```bash
git clone <repository-url>
cd sap-erp-demo
```

2. **Configure Environment**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your preferred settings (optional)
# Default values work out of the box
```

3. **Start All Services**

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

4. **Initialize Database**

The database is automatically initialized with:
- Schema creation via Alembic migrations
- Seed data for demo users and sample records
- Test data for all three modules

5. **Access the Application**

Open your browser and navigate to: http://localhost:3010

### Service Endpoints

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| Frontend | http://localhost:3010 | 3010 | React application |
| Backend API | http://localhost:8100 | 8100 | FastAPI REST API |
| API Documentation | http://localhost:8100/docs | 8100 | Swagger UI |
| Kong Gateway | http://localhost:8180 | 8180 | API Gateway |
| Kong Admin | http://localhost:8101 | 8101 | Gateway admin |
| Camel Integration | http://localhost:8181 | 8181 | Integration layer |
| ITSM Mock | http://localhost:8182 | 8182 | Mock ITSM service |
| ERP Mock | http://localhost:8183 | 8183 | Mock ERP service |
| CRM Mock | http://localhost:8184 | 8184 | Mock CRM service |
| Prometheus | http://localhost:9190 | 9190 | Metrics collection |
| Grafana | http://localhost:3011 | 3011 | Monitoring dashboards |
| PostgreSQL | localhost:5435 | 5435 | Database |

### Demo Credentials

| Username | Password | Role | Access |
|----------|----------|------|--------|
| admin | admin123 | Administrator | Full system access |
| engineer | engineer123 | Maintenance Engineer | PM module |
| manager | manager123 | Store Manager | MM module |
| finance | finance123 | Finance Officer | FI module |

## User Guide

### Dashboard Overview

The dashboard provides a comprehensive view of system health:

- **System Status Tiles**: Monitor active systems, alerts, and health
- **Module Cards**: Quick access to PM, MM, and FI modules
- **Recent Activity**: View latest tickets and transactions

### Plant Maintenance (PM) Module

**Equipment Management**
1. Navigate to PM module from dashboard
2. View equipment list with status indicators
3. Create new equipment with master data
4. Track maintenance history

**Work Orders**
1. Create work orders for equipment
2. Assign to maintenance engineers
3. Track progress and completion
4. View work order history

**Incident Management**
1. Report equipment incidents
2. Auto-generate tickets
3. Track resolution status
4. Link to work orders

### Materials Management (MM) Module

**Material Master**
1. View all materials with stock levels
2. Search by material number or description
3. Create new materials with UOM
4. Set reorder levels

**Inventory Management**
1. Monitor stock levels
2. View low stock alerts
3. Track inventory value
4. Process stock transactions

**Purchase Requisitions**
1. Create purchase requisitions
2. Track approval status
3. View requisition history
4. Link to materials

### Financial Accounting (FI) Module

**Approvals Inbox**
1. View pending approval requests
2. Review request details
3. Approve or reject with comments
4. Track approval history

**Cost Centers**
1. Create and manage cost centers
2. Set budget allocations
3. Track spending vs budget
4. View cost center hierarchy

**General Ledger**
1. View GL accounts
2. Check account balances
3. View transaction history
4. Generate financial reports

## API Documentation

### Authentication

All API requests require JWT authentication (except login).

**Login**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

**Using Token**
```bash
GET /api/v1/tickets
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Key Endpoints

#### Tickets
- `GET /api/v1/tickets` - List all tickets
- `POST /api/v1/tickets` - Create ticket
- `GET /api/v1/tickets/{id}` - Get ticket details
- `PATCH /api/v1/tickets/{id}` - Update ticket

#### Plant Maintenance
- `GET /api/v1/pm/equipment` - List equipment
- `POST /api/v1/pm/equipment` - Create equipment
- `GET /api/v1/pm/work-orders` - List work orders
- `POST /api/v1/pm/work-orders` - Create work order

#### Materials Management
- `GET /api/v1/mm/materials` - List materials
- `POST /api/v1/mm/materials` - Create material
- `GET /api/v1/mm/requisitions` - List requisitions
- `POST /api/v1/mm/requisitions` - Create requisition

#### Financial Accounting
- `GET /api/v1/fi/cost-centers` - List cost centers
- `POST /api/v1/fi/cost-centers` - Create cost center
- `GET /api/v1/fi/approvals` - List approvals
- `POST /api/v1/fi/approvals/{id}/approve` - Approve request
- `POST /api/v1/fi/approvals/{id}/reject` - Reject request

Full API documentation available at: http://localhost:8100/docs

## Development

### Local Backend Development

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://sapuser:sappassword@localhost:5435/saperp"
export JWT_SECRET="your-secret-key"

# Run migrations
alembic upgrade head

# Seed database
python scripts/seed_data.py

# Start development server
uvicorn main:app --reload --port 8000

# API available at http://localhost:8000
```

### Local Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set API URL
echo "VITE_API_URL=http://localhost:8100/api/v1" > .env.local

# Start development server
npm run dev

# Application available at http://localhost:5173
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Code Structure

```
sap-erp-demo/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── api/
│   │   └── routes/           # API endpoints
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   ├── tests/                # Test suites
│   ├── config.py             # Configuration
│   └── main.py               # Application entry
├── frontend/
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # Context providers
│   │   ├── hooks/            # Custom hooks
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   └── styles/           # CSS and themes
│   └── package.json
├── camel/                    # Integration layer
├── kong/                     # API gateway config
├── mocks/                    # Mock services
├── prometheus/               # Monitoring config
├── grafana/                  # Dashboard config
└── docker-compose.yml        # Container orchestration
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/property/test_pm_properties.py

# Run property-based tests
pytest tests/property/ -v

# Run with verbose output
pytest -v -s
```

### Test Categories

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test API endpoints and database
- **Property Tests**: Hypothesis-based property testing
- **End-to-End Tests**: Full workflow testing

### Frontend Tests

```bash
cd frontend

# Run tests (when configured)
npm test

# Run with coverage
npm test -- --coverage
```

## Deployment

### Production Considerations

1. **Environment Variables**
   - Set strong JWT_SECRET
   - Use production database credentials
   - Configure proper CORS origins
   - Set secure cookie flags

2. **Database**
   - Use managed PostgreSQL service
   - Enable SSL connections
   - Configure backup strategy
   - Set up replication

3. **Security**
   - Enable HTTPS/TLS
   - Configure Kong rate limiting
   - Implement API key management
   - Set up WAF rules

4. **Monitoring**
   - Configure Prometheus alerts
   - Set up Grafana notifications
   - Enable application logging
   - Implement error tracking

5. **Scaling**
   - Use container orchestration (Kubernetes)
   - Configure horizontal pod autoscaling
   - Set up load balancing
   - Implement caching strategy

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Frontend Can't Connect to Backend**
```bash
# Check backend health
curl http://localhost:8100/health

# Verify VITE_API_URL in frontend
cat frontend/.env.local

# Check CORS configuration in backend
```

**Kong Gateway Issues**
```bash
# Check Kong configuration
docker-compose logs kong

# Verify Kong health
curl http://localhost:8101/status

# Reload Kong configuration
docker-compose restart kong
```

**Port Conflicts**
```bash
# Check what's using a port
lsof -i :3010  # On Mac/Linux
netstat -ano | findstr :3010  # On Windows

# Change ports in docker-compose.yml
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend

# Enable debug mode in backend
# Set LOG_LEVEL=DEBUG in .env
```

### Reset Everything

```bash
# Stop all services
docker-compose down

# Remove volumes (deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Update documentation
6. Submit a pull request

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow ESLint rules
- **Commits**: Use conventional commit messages

## License

MIT License - This is a demonstration project for educational purposes only.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at /docs

## Acknowledgments

- SAP Fiori Design Guidelines
- SAP GUI Classic patterns
- FastAPI framework
- React and TypeScript communities
