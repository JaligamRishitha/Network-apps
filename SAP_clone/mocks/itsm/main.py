"""ITSM Mock Service - receives PM ticket events"""
from fastapi import FastAPI, Request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ITSM Mock Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/tickets")
async def receive_ticket(request: Request):
    event = await request.json()
    logger.info(f"ITSM received ticket event: {event.get('event_type')}")
    return {"status": "received", "service": "itsm"}
