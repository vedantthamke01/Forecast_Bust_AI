#!/usr/bin/env bash
# ==============================================================================
# SIH26079: AI-Based Forecast Bust Detection Platform - Environment Bootstrap
# ==============================================================================
set -e

echo "=== [SIH26079] NCMRWF Forecast Bust Detection System Setup ==="

# Check Python version
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[-] Error: Python is not installed. Python 3.10+ required."
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo "[+] Found Python: $($PYTHON_CMD --version)"

# Check Flutter (Optional for backend / web, required for mobile)
if command -v flutter &> /dev/null; then
    echo "[+] Found Flutter: $(flutter --version | head -n 1)"
else
    echo "[i] Flutter SDK not detected in PATH. Flutter mobile app can be built after installing Flutter."
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "[+] Found Docker: $(docker --version)"
else
    echo "[i] Docker not detected. Operating in local standalone mode."
fi

# Create Virtual Environment if not active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ ! -d "venv" ]; then
        echo "[+] Creating Python virtual environment (venv)..."
        $PYTHON_CMD -m venv venv
    fi
    echo "[+] Activating virtual environment..."
    source venv/bin/activate || source venv/Scripts/activate
    PIP_CMD="pip"
else
    echo "[+] Using active virtual environment: $VIRTUAL_ENV"
    PIP_CMD="pip"
fi

# Environment file
if [ ! -f ".env" ]; then
    echo "[+] Creating .env from .env.example..."
    cp .env.example .env
fi

# Install dependencies
echo "[+] Installing Python dependencies..."
$PIP_CMD install -r requirements.txt

# Run initial setup script to seed datasets and verify environment
echo "[+] Initializing dataset structures and demo data..."
$PYTHON_CMD -m scripts.setup_data

echo "[+] Setup completed successfully!"
echo "Run 'make dev' or 'python -m uvicorn backend.app.main:app --reload' to start the application."
