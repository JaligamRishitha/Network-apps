Write-Host "Testing Tickets API..." -ForegroundColor Green

$tokenResponse = Invoke-RestMethod -Uri "http://localhost:8002/token" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "username=admin@company.com&password=admin123"
$token = $tokenResponse.access_token
Write-Host "Token obtained successfully" -ForegroundColor Green

$headers = @{ "Authorization" = "Bearer $token" }

$tickets = Invoke-RestMethod -Uri "http://localhost:8002/tickets/?my_tickets=true" -Method GET -Headers $headers
Write-Host "Tickets found: $($tickets.Count)" -ForegroundColor Yellow

$approvals = Invoke-RestMethod -Uri "http://localhost:8002/approvals/" -Method GET -Headers $headers  
Write-Host "Approvals found: $($approvals.Count)" -ForegroundColor Yellow