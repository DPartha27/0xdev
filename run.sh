#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/sensai-backend"
FRONTEND_DIR="$ROOT_DIR/sensai-frontend"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

cleanup() {
  echo ""
  echo -e "${GREEN}Shutting down...${NC}"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

# --- Pre-flight checks ---
echo -e "${GREEN}[1/6] Checking prerequisites...${NC}"

command -v python3.12 >/dev/null 2>&1 || { echo -e "${RED}python3.12 not found. Install with: brew install python@3.12${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}node not found. Install Node 18+.${NC}"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo -e "${RED}uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || { echo -e "${RED}ffmpeg not found. Install with: brew install ffmpeg${NC}"; exit 1; }
command -v pdftotext >/dev/null 2>&1 || { echo -e "${RED}poppler not found. Install with: brew install poppler${NC}"; exit 1; }

# --- Backend setup ---
echo -e "${GREEN}[2/6] Setting up backend virtual environment...${NC}"
cd "$BACKEND_DIR"
if [ ! -d venv ]; then
  python3.12 -m venv venv
fi
source venv/bin/activate

echo -e "${GREEN}[3/6] Installing backend dependencies...${NC}"
uv sync --all-extras --quiet

# Check backend .env.local
if [ ! -f src/api/.env.local ]; then
  echo -e "${RED}Missing src/api/.env.local — copy from src/api/.env.example and fill in credentials.${NC}"
  exit 1
fi

# --- Frontend setup ---
echo -e "${GREEN}[4/6] Installing frontend dependencies...${NC}"
cd "$FRONTEND_DIR"
npm ci --silent 2>/dev/null

# Check frontend .env.local
if [ ! -f .env.local ]; then
  echo -e "${RED}Missing .env.local — copy from .env.example and fill in credentials.${NC}"
  exit 1
fi

# --- Initialize DB and start backend ---
echo -e "${GREEN}[5/6] Initializing database and starting backend on :8001...${NC}"
cd "$BACKEND_DIR/src"
source "$BACKEND_DIR/venv/bin/activate"
uv run python startup.py
uv run uvicorn api.main:app --reload --port 8001 &
BACKEND_PID=$!

# --- Start frontend ---
echo -e "${GREEN}[6/6] Starting frontend on :3000...${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Backend:  http://localhost:8001/docs${NC}"
echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}  Press Ctrl+C to stop both servers${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

wait
