@echo off
echo Starting ServiceNow Clone Application...
echo.
echo This will start the application using Docker Compose.
echo Make sure Docker Desktop is running.
echo.
pause

echo Building and starting containers...
docker-compose up --build

pause