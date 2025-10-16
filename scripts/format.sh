#!/usr/bin/env bash
set -e

echo "🎯 Formatting code with Black and Ruff..."

# Check if we're in backend or frontend directory
if [[ -f "backend/pyproject.toml" ]]; then
    echo "📁 Formatting backend code..."
    cd backend
elif [[ -f "frontend/pyproject.toml" ]]; then
    echo "📁 Formatting frontend code..."
    cd frontend
fi

echo "🔧 Running Ruff auto-fixes..."
ruff check . --fix --unsafe-fixes

echo "🎨 Running Black formatter..."
black .

echo "✨ Code formatting completed!"