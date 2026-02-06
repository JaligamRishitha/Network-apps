@echo off
echo ========================================
echo Starting SAP ERP Demo - Local Setup
echo ========================================
echo.
echo This will start:
echo - PostgreSQL Database on port 5435
echo - FastAPI Backend on port 2004
echo - React Frontend on port 2003
echo.
echo Press Ctrl+C to stop all services
echo ========================================
echo.

docker-compose up --build
