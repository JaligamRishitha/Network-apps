# ServiceNow Clone Application

A ServiceNow-like ITSM (IT Service Management) application built with React.js frontend and Python FastAPI backend.

## Features

- User authentication and authorization
- Incident management
- Service catalog
- Knowledge base
- Dashboard with metrics
- Role-based access control

## Tech Stack

- **Frontend**: React.js, Material-UI, Axios
- **Backend**: Python FastAPI, SQLAlchemy, PostgreSQL
- **Containerization**: Docker, Docker Compose
- **Database**: PostgreSQL

## Quick Start

1. Clone the repository
2. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. Access the application:
   - Frontend: http://localhost:3003
   - Backend API: http://localhost:8002
   - API Documentation: http://localhost:8002/docs

## Default Login
- Username: admin@company.com
- Password: admin123