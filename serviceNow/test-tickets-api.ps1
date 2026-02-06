# Test script to check tickets API
Write-Host "Testing Tickets API..." -ForegroundColor Green

# Get authentication token
$loginBody = @{
    username = "admin@company.com"
    password = "admin123"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri "http://localhost:8002/token" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin@company.com&password=admin123"
    $token = $tokenResponse.access_token
    Write-Host "✓ Authentication successful" -ForegroundColor Green
    
    # Test tickets endpoint
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $tickets = Invoke-RestMethod -Uri "http://localhost:8002/tickets/?my_tickets=true" -Method GET -Headers $headers
    Write-Host "✓ Tickets endpoint accessible" -ForegroundColor Green
    Write-Host "Number of tickets found: $($tickets.Count)" -ForegroundColor Yellow
    
    if ($tickets.Count -gt 0) {
        Write-Host "Sample ticket:" -ForegroundColor Cyan
        $tickets[0] | ConvertTo-Json -Depth 2
    } else {
        Write-Host "No tickets found in database" -ForegroundColor Red
    }
    
    # Test approvals endpoint
    $approvals = Invoke-RestMethod -Uri "http://localhost:8002/approvals/" -Method GET -Headers $headers
    Write-Host "✓ Approvals endpoint accessible" -ForegroundColor Green
    Write-Host "Number of approvals found: $($approvals.Count)" -ForegroundColor Yellow
    
    if ($approvals.Count -gt 0) {
        Write-Host "Sample approval:" -ForegroundColor Cyan
        $approvals[0] | ConvertTo-Json -Depth 2
    } else {
        Write-Host "No approvals found in database" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}