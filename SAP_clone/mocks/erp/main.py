"""ERP Mock Service - receives MM stock events"""
from fastapi import FastAPI, Request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ERP Mock Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/inventory")
async def receive_inventory(request: Request):
    event = await request.json()
    logger.info(f"ERP received inventory event: {event.get('event_type')}")
    return {"status": "received", "service": "erp"}
