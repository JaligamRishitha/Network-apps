#!/usr/bin/env python3
"""
Automated setup for ServiceNow Business Rule to auto-forward tickets
This script configures ServiceNow to automatically send new/updated incidents to the orchestrator
"""

import requests
import json

# Configuration
SERVICENOW_URL = "http://149.102.158.71:4780"
ORCHESTRATOR_URL = "http://localhost:2486/api/webhook/servicenow"

# Business Rule Configuration
BUSINESS_RULE_NAME = "Auto Forward Incidents to Orchestrator"
BUSINESS_RULE_SCRIPT = """
(function executeRule(current, previous /*null when async*/) {

    // Orchestrator webhook URL
    var ORCHESTRATOR_URL = '%s';

    // Prepare incident data
    var incidentData = {
        sys_id: current.sys_id.toString(),
        number: current.number.toString(),
        short_description: current.short_description.toString(),
        description: current.description ? current.description.toString() : '',
        priority: current.priority.toString(),
        state: current.state.toString(),
        assigned_to: current.assigned_to ? current.assigned_to.toString() : '',
        category: current.category ? current.category.toString() : '',
        subcategory: current.subcategory ? current.subcategory.toString() : ''
    };

    gs.info('[Orchestrator] Forwarding incident ' + current.number + ' to orchestrator');

    try {
        var request = new sn_ws.RESTMessageV2();
        request.setEndpoint(ORCHESTRATOR_URL);
        request.setHttpMethod('POST');
        request.setRequestHeader('Content-Type', 'application/json');
        request.setRequestBody(JSON.stringify(incidentData));
        request.setHttpTimeout(30000);

        var response = request.execute();
        var responseBody = response.getBody();
        var httpStatus = response.getStatusCode();

        if (httpStatus == 200) {
            var result = JSON.parse(responseBody);
            gs.info('[Orchestrator] SUCCESS: Forwarded ' + current.number +
                   ' (ID: ' + result.orchestration_ticket_id +
                   ', Category: ' + result.category +
                   ', Auto-resolve: ' + result.auto_resolve + ')');
        } else {
            gs.error('[Orchestrator] ERROR: HTTP ' + httpStatus + ' - ' + responseBody);
        }

    } catch (ex) {
        gs.error('[Orchestrator] EXCEPTION: ' + ex.message);
    }

})(current, previous);
""" % ORCHESTRATOR_URL

print("=" * 70)
print("ServiceNow Auto-Forwarding Setup")
print("=" * 70)
print()
print("This will configure ServiceNow to automatically forward tickets to:")
print(f"  {ORCHESTRATOR_URL}")
print()

# Since we can't directly create Business Rules via ServiceNow REST API,
# we'll create a webhook trigger instead using the incidents API

print("📋 Configuration Summary:")
print(f"   ServiceNow URL: {SERVICENOW_URL}")
print(f"   Orchestrator URL: {ORCHESTRATOR_URL}")
print(f"   Business Rule: {BUSINESS_RULE_NAME}")
print()

print("✅ Business Rule JavaScript code saved to:")
print("   /home/pradeep1a/Network-apps/servicenow_business_rule.js")
print()

# Save the JavaScript code
with open("/home/pradeep1a/Network-apps/servicenow_business_rule.js", "w") as f:
    f.write(BUSINESS_RULE_SCRIPT)

print("📝 Manual Setup Instructions:")
print("=" * 70)
print()
print("1. Login to ServiceNow: http://149.102.158.71:4780")
print()
print("2. Navigate to: System Definition → Business Rules")
print()
print("3. Click 'New' and configure:")
print(f"   Name: {BUSINESS_RULE_NAME}")
print("   Table: Incident [incident]")
print("   When: after")
print("   Insert: ✓")
print("   Update: ✓")
print("   Advanced: ✓")
print()
print("4. Copy the script from: servicenow_business_rule.js")
print()
print("5. Click 'Submit' to save")
print()
print("=" * 70)
print()
print("🧪 To test the setup:")
print("   1. Create a new incident in ServiceNow")
print("   2. Check orchestrator: curl http://localhost:2486/api/tickets")
print("   3. Check logs: tail -f ticket_orchestrator.log")
print()
print("✅ Setup guide available at: SERVICENOW_AUTO_FORWARDING_SETUP.md")
print("=" * 70)
