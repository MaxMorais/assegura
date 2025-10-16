#!/usr/bin/env bash
set -e

echo "🧹 Running code quality checks..."

# Check if we're in backend or frontend directory
if [[ -f "backend/pyproject.toml" ]]; then
    echo "📁 Running checks for backend..."
    cd backend
elif [[ -f "frontend/pyproject.toml" ]]; then
    echo "📁 Running checks for frontend..."
    cd frontend
fi

echo "🔍 Running Ruff linter..."
ruff check . --fix

echo "🎨 Running Black formatter..."
black . --diff --color

echo "🔧 Running MyPy type checker..."
mypy src/ || echo "⚠️  MyPy found type issues (continuing...)"

echo "✅ Code quality checks completed!"