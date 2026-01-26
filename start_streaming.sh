#!/bin/bash

# Start the complete Pathway streaming pipeline

echo "======================================================================"
echo "NEOVANCE-AI: Starting Pathway Streaming Pipeline"
echo "======================================================================"
echo ""

# Check if data directory exists
if [ ! -d "data" ]; then
    mkdir -p data
    echo "[SETUP] Created data directory"
fi

# Start simulator in background
echo "[1/3] Starting Pathway Simulator..."
cd backend
python pathway_simulator.py > ../simulator.log 2>&1 &
SIM_PID=$!
echo "      Simulator running (PID: $SIM_PID)"

sleep 2

# Start Pathway ETL pipeline in background
echo "[2/3] Starting Pathway ETL Pipeline..."
python pathway_etl.py > ../pathway.log 2>&1 &
ETL_PID=$!
echo "      ETL Pipeline running (PID: $ETL_PID)"

sleep 3

# Start FastAPI backend
echo "[3/3] Starting FastAPI Backend..."
cd ..
/mnt/d/Neovance-AI/venv/bin/python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "      Backend API running (PID: $API_PID)"

echo ""
echo "======================================================================"
echo "All services started successfully!"
echo "======================================================================"
echo ""
echo "Services:"
echo "  - Simulator:  PID $SIM_PID (writing to data/stream.csv)"
echo "  - Pathway:    PID $ETL_PID (processing stream -> database)"
echo "  - Backend:    PID $API_PID (http://localhost:8000)"
echo ""
echo "Logs:"
echo "  - Simulator:  tail -f simulator.log"
echo "  - Pathway:    tail -f pathway.log"
echo "  - Backend:    tail -f backend.log"
echo ""
echo "To stop all services:"
echo "  kill $SIM_PID $ETL_PID $API_PID"
echo ""
echo "======================================================================"
echo "Press Ctrl+C to stop monitoring (services will continue running)"
echo "======================================================================"

# Monitor logs
tail -f simulator.log
