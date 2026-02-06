# Test script for ServiceNow Clone API
Write-Host "Testing ServiceNow Clone API..." -ForegroundColor Green

# Test API documentation endpoint
Write-Host "`nTesting API Documentation..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/docs" -Method GET
    Write-Host "✓ API Documentation accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ API Documentation failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test login endpoint
Write-Host "`nTesting Login..." -ForegroundColor Yellow
try {
    $body = @{
        username = "admin@company.com"
        password = "admin123"
    }
    $response = Invoke-WebRequest -Uri "http://localhost:8002/token" -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
    $token = ($response.Content | ConvertFrom-Json).access_token
    Write-Host "✓ Login successful, token received" -ForegroundColor Green
    
    # Test authenticated endpoint
    Write-Host "`nTesting Authenticated Endpoint..." -ForegroundColor Yellow
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    $response = Invoke-WebRequest -Uri "http://localhost:8002/users/me" -Method GET -Headers $headers
    $user = $response.Content | ConvertFrom-Json
    Write-Host "✓ User info retrieved: $($user.full_name) ($($user.email))" -ForegroundColor Green
    
} catch {
    Write-Host "✗ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTesting Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3003" -Method GET
    Write-Host "✓ Frontend accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Frontend failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== ServiceNow Clone Application Status ===" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3003" -ForegroundColor White
Write-Host "Backend API: http://localhost:8002" -ForegroundColor White
Write-Host "API Documentation: http://localhost:8002/docs" -ForegroundColor White
Write-Host "Default Login: admin@company.com / admin123" -ForegroundColor White