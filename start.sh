#!/bin/bash
# Railway start script — runs FastAPI backend + Next.js frontend
set -e

echo "=== AI Tool Review Aggregator ==="

# Start FastAPI backend in background
echo "Starting FastAPI backend on port 8000..."
cd /app/backend
pip install -r requirements.txt -q 2>/dev/null
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start Next.js frontend in foreground (Railway watches this process)
echo "Starting Next.js frontend on port 3000..."
cd /app
NEXT_PUBLIC_API_URL="http://localhost:8000" npx next start --port 3000 -H 0.0.0.0

# If Next.js exits, kill backend
kill $BACKEND_PID 2>/dev/null
