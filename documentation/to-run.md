# Terminal 1: Start Backend
cd /mnt/d/Neovance-AI/backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend  
cd /mnt/d/Neovance-AI/frontend/dashboard
npm run dev

# Terminal 3: Test Workflow
curl -X POST http://localhost:8000/api/v1/predict_sepsis \
  -H "Content-Type: application/json" \
  -d '{"baby_id":"B001","features":{"hr":160,"spo2":92,"rr":55,"temp":38.2,"map":35}}'

  ---

  