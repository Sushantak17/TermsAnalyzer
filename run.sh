#!/bin/bash
trap 'kill 0' EXIT

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Starting TermsAnalyzer..."
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""

source venv/bin/activate
pip install -q fastapi uvicorn python-multipart

export PYTHONPATH="$DIR:$PYTHONPATH"
(cd /tmp && python -m uvicorn server:app --reload --reload-dir "$DIR" --port 8000) &
cd frontend && npm run dev &

wait
