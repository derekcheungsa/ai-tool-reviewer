#!/bin/bash
set -e

echo "=== AI Tool Review Aggregator ==="
echo "CWD: $(pwd)"

# Find project root
if [ -d "/app/backend" ]; then
  PROJECT_ROOT="/app"
elif [ -d "/app/ai-tool-reviewer/backend" ]; then
  PROJECT_ROOT="/app/ai-tool-reviewer"
else
  echo "ERROR: Cannot find backend directory"
  find /app -maxdepth 4 -type d 2>/dev/null | sort
  exit 1
fi

echo "PROJECT_ROOT=$PROJECT_ROOT"

# Start FastAPI
echo "Starting FastAPI backend on port 8000..."
cd "$PROJECT_ROOT/backend"
if [ -f /opt/venv/bin/python3 ]; then
  PYTHON=/opt/venv/bin/python3
else
  PYTHON=python3
fi
nohup $PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd "$PROJECT_ROOT"
sleep 3

# Verify backend
echo "Backend PID: $BACKEND_PID"
curl -sf http://127.0.0.1:8000/health && echo "Backend OK" || echo "Backend NOT responding"

# Start Next.js
echo "Starting Next.js frontend on port ${PORT:-3000}..."
NEXT_PUBLIC_API_URL="http://127.0.0.1:8000" npx next start --port ${PORT:-3000} -H 0.0.0.0

kill $BACKEND_PID 2>/dev/null
