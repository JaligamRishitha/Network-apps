"""Apache Camel-like integration router (simplified Python implementation)"""
from fastapi import FastAPI, Request, Response
import httpx
import os
import xml.etree.ElementTree as ET

app = FastAPI(title="SAP ERP Integration Router")

ITSM_MOCK_URL = os.getenv("ITSM_MOCK_URL", "http://itsm-mock:8082")
ERP_MOCK_URL = os.getenv("ERP_MOCK_URL", "http://erp-mock:8083")
CRM_MOCK_URL = os.getenv("CRM_MOCK_URL", "http://crm-mock:8084")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook")
async def route_event(request: Request):
    """Route events to appropriate mock endpoints based on event_type prefix"""
    event = await request.json()
    event_type = event.get("event_type", "")
    
    async with httpx.AsyncClient() as client:
        if event_type.startswith("PM_"):
            await client.post(f"{ITSM_MOCK_URL}/tickets", json=event)
        elif event_type.startswith("MM_"):
            await client.post(f"{ERP_MOCK_URL}/inventory", json=event)
        elif event_type.startswith("FI_"):
            await client.post(f"{CRM_MOCK_URL}/approvals", json=event)
    
    return {"status": "routed", "event_type": event_type}

@app.post("/api/ticket-status")
async def receive_ticket_status(request: Request):
    """Receive ticket status updates from SAP ERP backend in XML format"""
    try:
        xml_content = await request.body()
        xml_string = xml_content.decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(xml_string)
        
        ticket_id = root.find("TicketID").text
        correlation_id = root.find("CorrelationID").text
        module = root.find("Module").text
        status = root.find("Status").text
        updated_by = root.find("UpdatedBy").text
        updated_at = root.find("UpdatedAt").text
        comment = root.find("Comment").text
        
        print(f"Received ticket status update:")
        print(f"  Ticket ID: {ticket_id}")
        print(f"  Correlation ID: {correlation_id}")
        print(f"  Module: {module}")
        print(f"  Status: {status}")
        print(f"  Updated By: {updated_by}")
        print(f"  Updated At: {updated_at}")
        print(f"  Comment: {comment}")
        
        # Forward to MuleSoft events API
        mulesoft_events_url = "http://host.docker.internal:3001/events"
        
        event_payload = {
            "event_type": "ticket_status_update",
            "ticket_id": ticket_id,
            "correlation_id": correlation_id,
            "module": module,
            "status": status,
            "updated_by": updated_by,
            "timestamp": updated_at,
            "comment": comment
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    mulesoft_events_url,
                    json=event_payload,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code in [200, 201]:
                    print(f"Successfully forwarded to MuleSoft events API: {response.status_code}")
                else:
                    print(f"MuleSoft events API returned: {response.status_code}")
        except Exception as e:
            print(f"Error forwarding to MuleSoft events API: {str(e)}")
            # Continue even if forwarding fails
        
        return Response(
            content="<Response><Status>Success</Status></Response>",
            media_type="application/xml",
            status_code=200
        )
    except Exception as e:
        print(f"Error processing ticket status: {str(e)}")
        return Response(
            content=f"<Response><Status>Error</Status><Message>{str(e)}</Message></Response>",
            media_type="application/xml",
            status_code=500
        )
