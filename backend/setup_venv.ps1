# Setup script for CTLChat backend virtual environment

Write-Host "Setting up Python virtual environment for CTLChat backend..." -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Cyan
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "`n✓ Virtual environment setup complete!" -ForegroundColor Green
Write-Host "`nTo activate the virtual environment, run:" -ForegroundColor Yellow
Write-Host "  .\backend\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "`nTo deactivate when done, run:" -ForegroundColor Yellow
Write-Host "  deactivate" -ForegroundColor White
