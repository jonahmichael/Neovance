# Manual Startup Guide for Neovance AI

## If Automatic Startup Fails Due to Port Conflicts

### Step 1: Start Frontend
```bash
cd /mnt/d/Neovance-AI/frontend/dashboard
npm run dev -- --port 5000
```
Frontend will be available at: http://localhost:5000

### Step 2: Start Backend API
```bash
cd /mnt/d/Neovance-AI
source venv/bin/activate
cd backend
python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
```
Backend API will be available at: http://localhost:8000

### Step 3: Generate Test Data (Optional)
```bash
cd /mnt/d/Neovance-AI
source venv/bin/activate
python backend/pathway_eos_simulator.py
```
This will populate the database with EOS test data

## Login Credentials

### Doctor Access:
- **Username**: DR001
- **Password**: password@dr

### Nurse Access:
- **Username**: NS001 
- **Password**: password@ns

## Features Available:

**EOS Risk Calculator** - Validated Puopolo/Kaiser algorithm  
**Role-based Authentication** - Separate doctor/nurse access  
**Real-time Vitals Monitoring** - Live heart rate, SpO2, etc.  
**Critical Action Panel** - Doctor actions trigger nurse alerts  
**Notification System** - Real-time communication between roles  
**Clean UI Design** - White/red/blue/green color scheme only  

## API Documentation:
- Visit: http://localhost:8000/docs for interactive API documentation

## Troubleshooting:
- If port conflicts persist, try using ports 6000, 7000, 8001, etc.
- Make sure no other services are using these ports
- Use `lsof -i :PORT` to check what's using a specific port