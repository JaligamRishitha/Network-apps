# ServiceNow Clone - Deployment Guide

## 🚀 Quick Start

Your ServiceNow clone application is now running! Here's how to access it:

### Application URLs
- **Frontend**: http://localhost:3003
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs

### Default Login Credentials
- **Email**: admin@company.com
- **Password**: admin123

## 🏗️ Architecture

### Frontend (React.js)
- **Port**: 3003
- **Technology**: React.js with Material-UI
- **Features**: 
  - User authentication
  - Dashboard with incident metrics
  - Incident management
  - Service catalog
  - Responsive design

### Backend (Python FastAPI)
- **Port**: 8002
- **Technology**: Python FastAPI with SQLAlchemy
- **Features**:
  - JWT authentication
  - RESTful API
  - Automatic API documentation
  - Database ORM with PostgreSQL

### Database (PostgreSQL)
- **Port**: 5435
- **Technology**: PostgreSQL 15
- **Features**:
  - User management
  - Incident tracking
  - Service catalog items

## 🐳 Docker Services

The application runs in 3 Docker containers:
1. **servicenow-frontend-1**: React.js development server
2. **servicenow-backend-1**: FastAPI application server
3. **servicenow-db-1**: PostgreSQL database

## 📋 Available Features

### ✅ Implemented
- User authentication and authorization
- Dashboard with incident statistics
- Incident creation and management
- Service catalog browsing
- Role-based access control (Admin, Agent, User)
- Responsive Material-UI design

### 🔄 Core ServiceNow Features Covered
- **Incident Management**: Create, view, and track incidents
- **Service Catalog**: Browse and request IT services
- **User Management**: Role-based access control
- **Dashboard**: Real-time metrics and quick actions

## 🛠️ Management Commands

### Start the Application
```bash
docker-compose up --build
```

### Stop the Application
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### Rebuild Containers
```bash
docker-compose up --build --force-recreate
```

## 🔧 Development

### Adding New Features
1. **Backend**: Add new endpoints in `backend/main.py`
2. **Frontend**: Add new components in `frontend/src/components/`
3. **Database**: Modify models in `backend/models.py`

### Environment Variables
- Copy `.env.example` to `.env` and modify as needed
- Update `docker-compose.yml` for production deployment

## 📊 Default Data

The application comes pre-loaded with:
- Admin user (admin@company.com / admin123)
- Sample service catalog items:
  - New Laptop Request
  - Software Installation
  - Access Request

## 🔒 Security Features

- JWT token-based authentication
- Password hashing with bcrypt
- Role-based access control
- CORS protection
- Input validation with Pydantic

## 🎯 Next Steps

To extend this application, consider adding:
- Knowledge base management
- Change management
- Asset management
- Reporting and analytics
- Email notifications
- File attachments
- Advanced workflow automation

## 🐛 Troubleshooting

### Common Issues
1. **Port conflicts**: Modify ports in `docker-compose.yml`
2. **Database connection**: Ensure PostgreSQL container is healthy
3. **CORS errors**: Update allowed origins in `backend/main.py`

### Logs
Check container logs for debugging:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## 📝 API Documentation

Visit http://localhost:8002/docs for interactive API documentation with Swagger UI.

---

**Congratulations!** Your ServiceNow clone is ready for use and development. 🎉