#!/usr/bin/env bash
set -euo pipefail

echo "=== OpenMetaphysics Developer Setup ==="

# Python (uv)
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
echo "Syncing Python dependencies..."
uv sync --all-extras

# Rust
if command -v cargo &>/dev/null; then
    echo "Fetching Rust dependencies..."
    cargo fetch
else
    echo "WARNING: Rust not installed. Install from https://rustup.rs"
fi

# Go
if command -v go &>/dev/null; then
    echo "Fetching Go dependencies..."
    (cd services/gateway && go mod download)
else
    echo "WARNING: Go not installed. Install from https://go.dev/dl/"
fi

# pre-commit
if command -v pre-commit &>/dev/null; then
    echo "Installing pre-commit hooks..."
    pre-commit install
else
    echo "WARNING: pre-commit not installed. Install: pip install pre-commit"
fi

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  docker compose up -d        # Start infrastructure"
echo "  make test                   # Run tests"
echo "  uvicorn openmetaphysics.api.app:app --reload  # Start API"
