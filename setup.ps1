# ==============================================================================
# SIH26079: AI-Based Forecast Bust Detection Platform - Windows PowerShell Setup
# ==============================================================================

Write-Host "=== [SIH26079] NCMRWF Forecast Bust Detection System Setup ===" -ForegroundColor Cyan

# Check Python
$pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3.10+ is required but was not found in PATH."
    exit 1
}
Write-Host "[+] Found Python: $(python --version)" -ForegroundColor Green

# Check Flutter
$flutterCmd = Get-Command flutter -ErrorAction SilentlyContinue
if ($flutterCmd) {
    Write-Host "[+] Found Flutter: $(flutter --version | Select-Object -First 1)" -ForegroundColor Green
} else {
    Write-Host "[i] Flutter SDK not detected in PATH. Mobile application sources available in apps/flutter_app." -ForegroundColor Yellow
}

# Check Docker
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    Write-Host "[+] Found Docker: $(docker --version)" -ForegroundColor Green
} else {
    Write-Host "[i] Docker not detected. Operating in local standalone SQLite mode." -ForegroundColor Yellow
}

# Environment file
if (-not (Test-Path ".env")) {
    Write-Host "[+] Creating .env from .env.example..." -ForegroundColor Green
    Copy-Item ".env.example" ".env"
}

# Install dependencies
Write-Host "[+] Installing Python dependencies from requirements.txt..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

Write-Host "[+] Initializing dataset structures..." -ForegroundColor Cyan
python -m scripts.setup_data

Write-Host "[+] Setup completed successfully!" -ForegroundColor Green
Write-Host "Run 'python -m uvicorn backend.app.main:app --reload --port 8000' to start the backend." -ForegroundColor Cyan
