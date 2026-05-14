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
$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd "$PROJECT_ROOT"

# Wait for backend
sleep 4

# Check if backend process is alive and listening
if kill -0 $BACKEND_PID 2>/dev/null; then
  echo "Backend PID $BACKEND_PID is running"
else
  echo "ERROR: Backend process died"
  exit 1
fi

# Start Next.js
echo "Starting Next.js frontend on port ${PORT:-3000}..."
NEXT_PUBLIC_API_URL="http://127.0.0.1:8000" npx next start --port ${PORT:-3000} -H 0.0.0.0

kill $BACKEND_PID 2>/dev/null
