#!/bin/bash
# Railway start script — seeds DB, starts FastAPI backend + Next.js frontend
set -e

echo "=== AI Tool Review Aggregator ==="

# Seed database with tools catalog (idempotent — skips existing)
echo "Seeding database..."
cd backend
/opt/venv/bin/python3 -m scripts.seed
cd ..

# Start FastAPI backend in background
echo "Starting FastAPI backend on port 8000..."
cd backend
/opt/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
sleep 3

# Start Next.js frontend in foreground on Railway's PORT (default 3000)
echo "Starting Next.js frontend on port ${PORT:-3000}..."
NEXT_PUBLIC_API_URL="http://localhost:8000" npx next start --port ${PORT:-3000} -H 0.0.0.0

# If Next.js exits, kill backend
kill $BACKEND_PID 2>/dev/null
