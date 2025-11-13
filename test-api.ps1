#!/usr/bin/env pwsh
# test-api.ps1 - Test FastAPI endpoints to verify server is running

Write-Host "AIEngine FastAPI Endpoint Tester" -ForegroundColor Green
Write-Host ""

# Try ports
$ports = @(8000, 9000)

foreach ($port in $ports) {
    $url = "http://127.0.0.1:$port/health"
    Write-Host "Testing $url..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✓ SUCCESS! Server is running on port $port" -ForegroundColor Green
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
        Write-Host ""
        
        # Now test /reviews endpoint
        $reviewUrl = "http://127.0.0.1:$port/reviews"
        Write-Host "Testing GET $reviewUrl..." -ForegroundColor Cyan
        $reviewResponse = Invoke-WebRequest -Uri $reviewUrl -UseBasicParsing -Method Get -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✓ SUCCESS! GET /reviews returned:" -ForegroundColor Green
        Write-Host "$($reviewResponse.Content)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Server Details:" -ForegroundColor Cyan
        Write-Host "  Port: $port" -ForegroundColor Cyan
        Write-Host "  Health Endpoint: $url" -ForegroundColor Cyan
        Write-Host "  Reviews Endpoint: $reviewUrl" -ForegroundColor Cyan
        Write-Host "  API Docs: http://127.0.0.1:$port/docs" -ForegroundColor Cyan
        
        exit 0
    }
    catch {
        Write-Host "✗ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "No server found on ports 8000 or 9000!" -ForegroundColor Red
Write-Host "Make sure to run .\run-server.ps1 first" -ForegroundColor Yellow
