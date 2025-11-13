#!/usr/bin/env pwsh
# run-server.ps1 - Simple FastAPI server launcher
# Usage: .\run-server.ps1

$Port = 8000
$HostIP = "127.0.0.1"
$FallbackPort = 9000

Write-Host "AIEngine FastAPI Server Launcher" -ForegroundColor Green
Write-Host "Primary Port: $Port | Fallback: $FallbackPort" -ForegroundColor Cyan
Write-Host ""

# Test if port is in use
$PortInUse = $null -ne (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)

if ($PortInUse) {
    Write-Host "Port $Port is in use. Attempting to free it..." -ForegroundColor Yellow
    
    # Get all PIDs listening on this port and kill them
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $procId = $conn.OwningProcess
        Write-Host "  Killing PID: $procId" -ForegroundColor Yellow
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue | Out-Null
    }
    
    Start-Sleep -Seconds 2
    
    # Check again
    $PortStillInUse = $null -ne (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)
    if ($PortStillInUse) {
        Write-Host "Port $Port still in use. Switching to fallback port $FallbackPort..." -ForegroundColor Yellow
        $Port = $FallbackPort
    }
    else {
        Write-Host "Port $Port is now free." -ForegroundColor Green
    }
}
else {
    Write-Host "Port $Port is available." -ForegroundColor Green
}

Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\\.venv\\Scripts\\Activate.ps1"

Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Server: http://$HostIP`:$Port" -ForegroundColor Cyan
Write-Host "API Docs: http://$HostIP`:$Port/docs" -ForegroundColor Cyan
Write-Host "Press CTRL+C to stop." -ForegroundColor Gray
Write-Host ("=" * 70) -ForegroundColor Gray

& .\.venv\Scripts\python.exe -m uvicorn main:app --host $HostIP --port $Port

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Gray
