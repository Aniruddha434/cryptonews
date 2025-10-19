# Kill all Python processes running bot.py
Write-Host "🔍 Searching for Python bot processes..." -ForegroundColor Yellow

# Get all Python processes
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es)" -ForegroundColor Cyan
    
    foreach ($process in $pythonProcesses) {
        Write-Host "  → Killing Python process (PID: $($process.Id))..." -ForegroundColor Red
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "✅ All Python processes killed!" -ForegroundColor Green
} else {
    Write-Host "✅ No Python processes found running" -ForegroundColor Green
}

Write-Host ""
Write-Host "You can now run: python bot.py" -ForegroundColor Cyan

