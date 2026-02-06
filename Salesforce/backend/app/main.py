from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import time

from .database import engine, Base
from .routes import auth, accounts, contacts, leads, opportunities, cases, dashboard, activities, logs, service, platform_events, sap_integration, mulesoft, mulesoft_integration, integration_tracking
from .logger import log_action


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Salesforce Clone API",
    description="A Salesforce-like CRM application API",
    version="1.0.0",
    lifespan=lifespan
)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get user from token if available
    user = "anonymous"
    if "authorization" in request.headers:
        try:
            from .auth import decode_token
            token = request.headers["authorization"].replace("Bearer ", "")
            payload = decode_token(token)
            user = payload.get("sub", "unknown")
        except:
            user = "anonymous"
    
    # Log request
    log_action(
        action_type=f"API_REQUEST",
        user=user,
        details=f"{request.method} {request.url.path}",
        status="pending"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        log_action(
            action_type=f"API_RESPONSE",
            user=user,
            details=f"{request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.2f}s",
            status="success"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        log_action(
            action_type=f"API_ERROR",
            user=user,
            details=f"{request.method} {request.url.path}",
            status="error",
            error=str(e)
        )
        raise

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8090",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8090",
        "http://149.102.158.71:5173",
        "http://149.102.158.71:4799",
        "http://149.102.158.71:8090",
        "*",  # Allow all origins for MCP connections
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(contacts.router)
app.include_router(leads.router)
app.include_router(opportunities.router)
app.include_router(cases.router)
app.include_router(dashboard.router)
app.include_router(activities.router)
app.include_router(logs.router)
app.include_router(service.router)
app.include_router(platform_events.router)
app.include_router(sap_integration.router)
app.include_router(mulesoft.router)
app.include_router(mulesoft_integration.router)
app.include_router(integration_tracking.router)


@app.get("/")
async def root():
    return {"message": "Salesforce Clone API", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# Mount static files for production (frontend build)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
