# ⚡ Electricity Load Requests - Frontend Guide

## Overview

A dedicated SAP Fiori-style frontend page for viewing and managing electricity load enhancement requests integrated with MuleSoft.

## Features

### 1. Dashboard Integration
- New tile on the main dashboard with ⚡ icon
- Highlighted with blue border for visibility
- Quick access from "My Home" page

### 2. Navigation
- Added to top navigation bar as "⚡ Electricity Load Requests"
- Accessible via `/electricity` route
- Integrated with existing SAP ERP navigation

### 3. Main Page Features

#### Statistics Cards
- **Total Requests**: Count of all load enhancement requests
- **Total Tickets**: All tickets created (PM, FI, MM)
- **Open Tickets**: Tickets awaiting action
- **Closed Tickets**: Completed tickets

#### Request List
- Groups tickets by correlation ID (request ID)
- Expandable rows to view all related tickets
- Shows PM, FI, and MM tickets for each request
- Color-coded module badges
- Priority and status indicators

#### Create New Request Form
- **Request ID**: Auto-generated or custom
- **Customer ID**: Customer identifier
- **Current Load**: Existing connection load (kW)
- **Requested Load**: Desired connection load (kW)
- **Connection Type**: Residential or Commercial
- **City**: Installation location
- **Pin Code**: Area code
- **Cost Preview**: Real-time estimated cost calculation

## How to Use

### Access the Page

1. **From Dashboard**:
   - Login to the application
   - Click on "⚡ Electricity Load Requests" tile

2. **From Navigation**:
   - Use top navigation bar
   - Click "⚡ Electricity Load Requests"

3. **Direct URL**:
   - Navigate to: `http://localhost:3000/electricity`

### Submit a New Request

1. Click "+ New Load Request" button
2. Fill in the form:
   - Enter Customer ID (e.g., CUST-88991)
   - Set Current Load (e.g., 5 kW)
   - Set Requested Load (e.g., 10 kW)
   - Select Connection Type
   - Enter City and Pin Code
3. Review estimated cost
4. Click "Submit Request"
5. View success message with ticket IDs

### View Requests

1. **Request Cards**:
   - Each card shows request ID and priority
   - Module badges indicate which tickets were created
   - Click to expand and see details

2. **Ticket Details**:
   - Ticket ID (clickable)
   - Module (PM/FI/MM)
   - Type (Maintenance/Finance_Approval/Procurement)
   - Title and description
   - Status (Open/Assigned/In_Progress/Closed)
   - SLA deadline

## UI Components

### Status Badges
- **Open**: Blue background
- **Assigned**: Yellow background
- **In_Progress**: Orange background
- **Closed**: Green background

### Priority Badges
- **P1**: Red (Critical - 4h SLA)
- **P2**: Orange (High - 8h SLA)
- **P3**: Yellow (Medium - 24h SLA)
- **P4**: Green (Low - 72h SLA)

### Module Badges
- **PM**: Blue (Plant Maintenance)
- **FI**: Green (Finance)
- **MM**: Orange (Materials Management)

## Cost Calculation

The form shows real-time cost estimation:

```
Base Fee: ₹5,000
Residential Rate: ₹2,500/kW
Commercial Rate: ₹3,500/kW

Example (5kW → 10kW, Residential):
= ₹5,000 + (5 × ₹2,500)
= ₹17,500
```

## Integration Flow

```
User Submits Form
      ↓
POST /api/integration/mulesoft/load-request
      ↓
Backend Creates Tickets
      ↓
Response with Ticket IDs
      ↓
Success Alert Shown
      ↓
Page Refreshes to Show New Tickets
```

## Files Created/Modified

### New Files
- `frontend/src/pages/ElectricityLoadRequests.tsx` - Main page component

### Modified Files
- `frontend/src/App.tsx` - Added route
- `frontend/src/components/TopNavLayout.tsx` - Added navigation link
- `frontend/src/pages/Dashboard.tsx` - Added dashboard tile

## API Endpoints Used

### Integration API
```typescript
POST /api/integration/mulesoft/load-request
Content-Type: application/json

{
  "RequestID": "SF-REQ-10021",
  "CustomerID": "CUST-88991",
  "CurrentLoad": 5,
  "RequestedLoad": 10,
  "ConnectionType": "RESIDENTIAL",
  "City": "Hyderabad",
  "PinCode": "500081"
}
```

### Tickets API
```typescript
GET /api/v1/tickets?limit=100
```

## Example Scenarios

### Scenario 1: Small Residential Load
```
Customer: CUST-001
Current: 3 kW
Requested: 5 kW
Type: Residential

Result:
- PM Ticket: TKT-PM-20260120-0001
- Cost: ₹10,000
- Priority: P4
```

### Scenario 2: Medium Commercial Load
```
Customer: CUST-002
Current: 5 kW
Requested: 15 kW
Type: Commercial

Result:
- PM Ticket: TKT-PM-20260120-0002
- FI Ticket: TKT-FI-20260120-0001
- Cost: ₹40,000
- Priority: P3
```

### Scenario 3: Large Commercial Load
```
Customer: CUST-003
Current: 10 kW
Requested: 30 kW
Type: Commercial

Result:
- PM Ticket: TKT-PM-20260120-0003
- FI Ticket: TKT-FI-20260120-0002
- MM Ticket: TKT-MM-20260120-0001
- Cost: ₹75,000
- Priority: P2
```

## Styling

The page follows SAP Fiori design guidelines:
- Clean, minimal interface
- Card-based layout
- Consistent spacing and typography
- Professional color scheme
- Responsive design

## Testing

### Manual Testing

1. **Start Application**:
   ```bash
   docker-compose up
   ```

2. **Login**:
   - Username: admin
   - Password: admin123

3. **Navigate to Page**:
   - Click dashboard tile or navigation link

4. **Submit Test Request**:
   - Use sample data provided
   - Verify success message
   - Check tickets are created

5. **View Tickets**:
   - Expand request cards
   - Verify all ticket details
   - Check status and priority

### Automated Testing

```bash
# Run frontend tests
cd frontend
npm test
```

## Troubleshooting

### Page Not Loading
- Check if backend is running
- Verify API endpoint configuration
- Check browser console for errors

### Request Submission Fails
- Verify backend is accessible
- Check network tab for API errors
- Ensure all required fields are filled

### Tickets Not Showing
- Wait a moment and refresh
- Check if tickets were created in backend
- Verify API response in network tab

## Future Enhancements

- [ ] Real-time updates with WebSocket
- [ ] Advanced filtering and search
- [ ] Export to PDF/Excel
- [ ] Ticket status updates from UI
- [ ] Customer details integration
- [ ] Cost approval workflow
- [ ] Equipment tracking
- [ ] Notification system
- [ ] Analytics dashboard
- [ ] Mobile responsive improvements

## Support

For issues or questions:
- Check browser console for errors
- Review backend logs
- Verify API connectivity
- Check authentication status

---

**Status**: ✅ Ready to Use
**Version**: 1.0.0
**Last Updated**: January 20, 2026
