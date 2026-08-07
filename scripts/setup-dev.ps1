# OpenMetaphysics Developer Setup (Windows / PowerShell)
Write-Host "=== OpenMetaphysics Developer Setup ===" -ForegroundColor Cyan

# Python (uv)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    irm https://astral.sh/uv/install.ps1 | iex
}
Write-Host "Syncing Python dependencies..."
uv sync --all-extras

# Rust
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    Write-Host "Fetching Rust dependencies..."
    cargo fetch
} else {
    Write-Host "WARNING: Rust not installed. Install from https://rustup.rs"
}

# Go
if (Get-Command go -ErrorAction SilentlyContinue) {
    Write-Host "Fetching Go dependencies..."
    Push-Location services\gateway
    go mod download
    Pop-Location
} else {
    Write-Host "WARNING: Go not installed. Install from https://go.dev/dl/"
}

# pre-commit
if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    Write-Host "Installing pre-commit hooks..."
    pre-commit install
} else {
    Write-Host "WARNING: pre-commit not installed. Install: pip install pre-commit"
}

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  docker compose up -d        # Start infrastructure"
Write-Host "  make test                   # Run tests (or: task test)"
Write-Host "  uvicorn openmetaphysics.api.app:app --reload  # Start API"
