"""CRM Mock Service - receives FI approval events"""
from fastapi import FastAPI, Request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CRM Mock Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/approvals")
async def receive_approval(request: Request):
    event = await request.json()
    logger.info(f"CRM received approval event: {event.get('event_type')}")
    return {"status": "received", "service": "crm"}
