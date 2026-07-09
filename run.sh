#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Local JLens Playground ==="

# Check conda env
if ! conda run -n local-jlens python --version &>/dev/null 2>&1; then
  echo "[1/5] Creating conda environment..."
  conda env create -f "$ROOT/environment.yml"
else
  echo "[1/5] Conda environment 'local-jlens' found."
fi

# Check frontend deps
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "[2/5] Installing frontend dependencies..."
  cd "$ROOT/frontend" && npm install && cd "$ROOT"
else
  echo "[2/5] Frontend dependencies installed."
fi

# Check for model configs
if [ ! -f "$ROOT/configs/models.local.json" ]; then
  echo "[3/5] No local model config found. Only demo mode will be available."
else
  echo "[3/5] Local model config found."
fi

echo "[4/5] Starting backend..."
cd "$ROOT/backend"
conda run -n local-jlens --no-capture-output python -m app.main &
BACKEND_PID=$!
cd "$ROOT"

echo "[5/5] Starting frontend..."
cd "$ROOT/frontend"
npx vite --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!
cd "$ROOT"

# Cleanup on exit
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  wait
}
trap cleanup EXIT INT TERM

echo ""
echo "====================================="
echo "  Backend:  http://127.0.0.1:8787"
echo "  Frontend: http://127.0.0.1:5173"
echo "====================================="
echo ""
echo "Press Ctrl+C to stop both servers."

wait