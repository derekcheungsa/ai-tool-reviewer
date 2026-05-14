#!/bin/bash
# Railway start script — starts FastAPI backend + Next.js frontend
set -e

echo "=== AI Tool Review Aggregator ==="

# Find project root — works with both /app and /app/ai-tool-reviewer layouts
if [ -d "/app/ai-tool-reviewer/backend" ]; then
  PROJECT_ROOT="/app/ai-tool-reviewer"
elif [ -d "/app/backend" ]; then
  PROJECT_ROOT="/app"
else
  echo "ERROR: Cannot find backend directory"
  exit 1
fi

# Start FastAPI backend in background (auto-seeds DB on startup)
echo "Starting FastAPI backend on port 8000..."
cd "$PROJECT_ROOT/backend"

# Use venv path if exists (Nixpacks), otherwise system python (Docker/Railpack)
if [ -f /opt/venv/bin/python3 ]; then
  PYTHON=/opt/venv/bin/python3
else
  PYTHON=python3
fi
$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# Wait for backend to be ready
sleep 3

# Start Next.js frontend in foreground on Railway's PORT (default 3000)
echo "Starting Next.js frontend on port ${PORT:-3000}..."
cd "$PROJECT_ROOT"
NEXT_PUBLIC_API_URL="http://localhost:8000" npx next start --port ${PORT:-3000} -H 0.0.0.0

# If Next.js exits, kill backend
kill $BACKEND_PID 2>/dev/null
