# Automated Google Cloud Run 100% Free Tier Deployment Script
# NCMRWF AI Forecast Bust Detection Platform (SIH26079)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GOOGLE CLOUD RUN (24/7 FREE TIER) DEPLOYMENT SETUP         " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verify gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Google Cloud SDK (gcloud) is not found on your system." -ForegroundColor Yellow
    Write-Host "[+] Installing Google Cloud SDK via winget..." -ForegroundColor Green
    winget install --id Google.CloudSDK -e --silent --accept-package-agreements --accept-source-agreements
    
    # Refresh PATH in current process
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        Write-Host "[!] gcloud was installed. Please restart your PowerShell window and run this script again." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "[+] gcloud CLI detected: $(gcloud --version | Select-Object -First 1)" -ForegroundColor Green

# 2. Check Authentication
Write-Host "`n[+] Checking Google Cloud authentication..." -ForegroundColor Cyan
$activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if (-not $activeAccount) {
    Write-Host "[!] No active Google account found. Launching browser login..." -ForegroundColor Yellow
    gcloud auth login
    $activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)"
}
Write-Host "[+] Logged in as: $activeAccount" -ForegroundColor Green

# 3. Project Configuration
$currentProject = gcloud config get-value project 2>$null
if (-not $currentProject -or $currentProject -eq "(unset)") {
    Write-Host "`n[+] Please enter your Google Cloud Project ID (e.g., sih-forecast-bust-2026):" -ForegroundColor Yellow
    $projectId = Read-Host "Project ID"
    gcloud config set project $projectId
    $currentProject = $projectId
} else {
    Write-Host "[+] Using active GCP Project: $currentProject" -ForegroundColor Green
}

# 4. Enable Services
Write-Host "`n[+] Enabling Cloud Run, Cloud Build & Artifact Registry APIs (Free)..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $currentProject

# 5. Deploy to Cloud Run under Free Tier
Write-Host "`n[+] Deploying backend & web dashboard to Cloud Run (Region: us-central1)..." -ForegroundColor Cyan
Write-Host "    Container will use 1 vCPU, 1 GB RAM (Always Free Tier eligible)" -ForegroundColor Gray

gcloud run deploy forecast-bust-backend `
  --source . `
  --dockerfile docker/Dockerfile.backend `
  --region us-central1 `
  --memory 1Gi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 2 `
  --allow-unauthenticated `
  --project $currentProject

# 6. Retrieve Service URL
$serviceUrl = gcloud run services describe forecast-bust-backend --region us-central1 --format="value(status.url)" --project $currentProject

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host " DEPLOYMENT COMPLETE! SERVICE IS LIVE ONLINE               " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Public HTTPS Base URL: $serviceUrl" -ForegroundColor Cyan
Write-Host "Web Dashboard URL:     $serviceUrl/dashboard/" -ForegroundColor Cyan
Write-Host "API Health Check:      $serviceUrl/health" -ForegroundColor Cyan
Write-Host "`n[!] Next Step to ensure 24/7 zero-sleep running for FREE:" -ForegroundColor Yellow
Write-Host "    Add '$serviceUrl/health' to cron-job.org or UptimeRobot to ping every 5 minutes."
Write-Host "============================================================" -ForegroundColor Green
