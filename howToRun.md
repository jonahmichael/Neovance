## Here's how to run the Neovance AI application:

### Step 1: Start the Backend (Terminal 1)
```bash
cd /mnt/d/Neovance-AI
source venv/bin/activate
cd backend && uvicorn main:app --reload --port 8000
```

### Step 2: Start the Pathway Simulator (Terminal 2)
```bash
cd /mnt/d/Neovance-AI
source venv/bin/activate
echo "timestamp,mrn,hr,spo2,rr,temp,map,risk_score,status" > data/stream.csv
python backend/pathway_simulator.py
```

### Step 3: Start the Pathway ETL (Terminal 3)
```bash
cd /mnt/d/Neovance-AI
source venv/bin/activate
python backend/pathway_etl.py
```

### Step 4: Start the Frontend (Terminal 4)
```bash
cd /mnt/d/Neovance-AI/frontend/dashboard
npm run dev
```
### Step 5:
Access the Application
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
