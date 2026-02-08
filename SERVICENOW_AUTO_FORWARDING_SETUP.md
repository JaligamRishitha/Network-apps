# ServiceNow Auto-Forwarding Configuration

This guide explains how to configure ServiceNow to automatically forward new and updated incidents to the Ticket Orchestrator.

## Overview

When configured, ServiceNow will automatically send incident data to the Ticket Orchestrator webhook whenever:
- A new incident is created
- An existing incident is updated
- Priority changes
- State changes

## Configuration Steps

### Step 1: Access Business Rules

1. Login to your ServiceNow instance as an administrator
2. Navigate to **System Definition → Business Rules**
3. Click **New** to create a new Business Rule

### Step 2: Configure Basic Settings

**Name:** `Send Incident to Ticket Orchestrator`

**Table:** `Incident [incident]`

**When to run:**
- ✅ **When:** `after`
- ✅ **Insert:** Yes (forward new tickets)
- ✅ **Update:** Yes (forward updated tickets)
- ⬜ **Delete:** No
- ⬜ **Query:** No

**Advanced:** ✅ Check this box

### Step 3: Set Conditions (Optional)

To only forward certain tickets, add conditions:

**Example 1: Only forward P1 and P2 tickets**
```
Priority is 1
OR Priority is 2
```

**Example 2: Only forward unresolved tickets**
```
State is not Resolved
AND State is not Closed
```

**Example 3: Forward all new and updated tickets**
- Leave conditions empty (all tickets will be forwarded)

### Step 4: Add the Script

In the **Script** field, paste the following JavaScript:

```javascript
(function executeRule(current, previous /*null when async*/) {

    // Configuration
    var ORCHESTRATOR_URL = 'http://localhost:2486/api/webhook/servicenow';

    // Prepare incident data
    var incidentData = {
        sys_id: current.sys_id.toString(),
        number: current.number.toString(),
        short_description: current.short_description.toString(),
        description: current.description.toString() || '',
        priority: current.priority.toString(),
        state: current.state.toString(),
        assigned_to: current.assigned_to ? current.assigned_to.toString() : '',
        category: current.category ? current.category.toString() : '',
        subcategory: current.subcategory ? current.subcategory.toString() : ''
    };

    // Log the action
    gs.info('[Orchestrator] Forwarding incident ' + current.number + ' to orchestrator');

    try {
        // Create REST message
        var request = new sn_ws.RESTMessageV2();
        request.setEndpoint(ORCHESTRATOR_URL);
        request.setHttpMethod('POST');
        request.setRequestHeader('Content-Type', 'application/json');
        request.setRequestBody(JSON.stringify(incidentData));

        // Set timeout
        request.setHttpTimeout(30000); // 30 seconds

        // Execute request
        var response = request.execute();
        var responseBody = response.getBody();
        var httpStatus = response.getStatusCode();

        // Log response
        if (httpStatus == 200) {
            var result = JSON.parse(responseBody);
            gs.info('[Orchestrator] SUCCESS: Ticket ' + current.number + ' forwarded. ' +
                   'Orchestration ID: ' + result.orchestration_ticket_id +
                   ', Category: ' + result.category +
                   ', Auto-resolve: ' + result.auto_resolve);

            // Optional: Add a work note to the incident
            current.work_notes = 'Ticket forwarded to AI Orchestrator. ' +
                                'Category: ' + result.category +
                                ', Auto-resolve: ' + result.auto_resolve;
            current.update();
        } else {
            gs.error('[Orchestrator] ERROR: Failed to forward ticket ' + current.number +
                    '. HTTP Status: ' + httpStatus + ', Response: ' + responseBody);
        }

    } catch (ex) {
        gs.error('[Orchestrator] EXCEPTION: Failed to forward ticket ' + current.number +
                '. Error: ' + ex.message);
    }

})(current, previous);
```

### Step 5: Save and Activate

1. Click **Submit** to save the Business Rule
2. Ensure the Business Rule is **Active** (checkbox at the top)
3. Test by creating or updating an incident

## Configuration for Different Environments

### Production Environment

```javascript
var ORCHESTRATOR_URL = 'https://orchestrator.yourcompany.com/api/webhook/servicenow';
```

### Development/Testing Environment

```javascript
var ORCHESTRATOR_URL = 'http://localhost:2486/api/webhook/servicenow';
```

### Using Network Address (if running on different machine)

```javascript
var ORCHESTRATOR_URL = 'http://207.180.217.117:2486/api/webhook/servicenow';
```

## Testing the Configuration

### Test 1: Create a New Incident

1. Navigate to **Incident → Create New**
2. Fill in:
   - **Short description:** "Test ticket - Password reset needed"
   - **Description:** "User test.user@company.com needs password reset"
   - **Priority:** P2
3. Click **Submit**
4. Check ServiceNow logs: Navigate to **System Logs → System Log → All**
5. Look for `[Orchestrator]` entries

### Test 2: Update an Existing Incident

1. Open any incident
2. Change the **Priority** or add a **Work Note**
3. Click **Update**
4. Check logs for forwarding confirmation

### Test 3: Verify in Orchestrator

```bash
# Check orchestrator received the ticket
curl http://localhost:2486/api/tickets

# Check statistics
curl http://localhost:2486/api/stats
```

## Troubleshooting

### Issue: Tickets not being forwarded

**Check 1: Business Rule is Active**
- Navigate to **System Definition → Business Rules**
- Find "Send Incident to Ticket Orchestrator"
- Ensure **Active** checkbox is checked

**Check 2: Orchestrator is Running**
```bash
curl http://localhost:2486/api/health
```

**Check 3: Check ServiceNow Logs**
- Navigate to **System Logs → System Log → All**
- Filter by **Source: Business Rules**
- Look for `[Orchestrator]` entries
- Check for ERROR or EXCEPTION messages

**Check 4: Network Connectivity**
- If orchestrator is on a different machine, ensure firewall allows connections
- Test connectivity: `curl http://<orchestrator-ip>:2486/api/health`

### Issue: Getting 404 or connection errors

**Solution 1: Check URL**
- Ensure the `ORCHESTRATOR_URL` in the script is correct
- Include the full path: `/api/webhook/servicenow`

**Solution 2: Check Orchestrator Logs**
```bash
tail -f ticket_orchestrator.log
```

### Issue: Tickets forwarded but not auto-resolving

**Check:** Ticket description must contain keywords for auto-resolve:
- Password reset: "password reset", "forgot password", "locked out"
- User creation: "create user", "new user", "onboard"
- User deactivation: "deactivate user", "remove user", "offboard"

## Advanced Configuration

### Only Forward Specific Categories

Add condition to Business Rule:
```javascript
if (current.category != 'User Account') {
    return; // Don't forward this ticket
}
```

### Add Retry Logic

```javascript
var MAX_RETRIES = 3;
for (var i = 0; i < MAX_RETRIES; i++) {
    try {
        var response = request.execute();
        if (response.getStatusCode() == 200) {
            break;  // Success
        }
    } catch (ex) {
        if (i == MAX_RETRIES - 1) {
            gs.error('[Orchestrator] All retries failed for ' + current.number);
        }
    }
}
```

### Queue Failed Forwards

Store failed forwards in a custom table for later retry:
```javascript
if (httpStatus != 200) {
    var gr = new GlideRecord('u_orchestrator_queue');
    gr.initialize();
    gr.u_incident = current.sys_id;
    gr.u_retry_count = 0;
    gr.insert();
}
```

## Monitoring

### View Forwarded Tickets in Orchestrator

```bash
# List all tickets
curl http://localhost:2486/api/tickets | jq '.tickets[] | {id, title, status}'

# View statistics
curl http://localhost:2486/api/stats | jq '.'

# Check health
curl http://localhost:2486/api/health
```

### ServiceNow Logs

Filter logs to see only orchestrator-related entries:
1. Navigate to **System Logs → System Log → All**
2. Add filter: **Message contains [Orchestrator]**

## Security Considerations

1. **Authentication:** Consider adding API key authentication to the orchestrator
2. **HTTPS:** Use HTTPS in production: `https://orchestrator.company.com`
3. **Network Security:** Restrict orchestrator port access to ServiceNow IP only
4. **Logging:** Ensure sensitive data is not logged in work notes

## Summary

✅ **What you've configured:**
- Automatic ticket forwarding from ServiceNow → Orchestrator
- Real-time forwarding on create/update
- Error handling and logging
- Auto-classification and routing

✅ **What happens now:**
1. User creates/updates incident in ServiceNow
2. Business Rule triggers and sends data to orchestrator
3. Orchestrator classifies the ticket
4. If auto-resolvable: Sent to AI agent
5. If requires human: Marked for manual intervention
6. Results written back to ServiceNow

---

**For additional help, check:**
- Orchestrator logs: `tail -f ticket_orchestrator.log`
- ServiceNow logs: System Logs → System Log → All
- Orchestrator API docs: http://localhost:2486/docs
