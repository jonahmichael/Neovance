# Setup Guide

This guide provides step-by-step instructions for setting up the Neovance-AI system.

## Prerequisites

### System Requirements
- Python 3.9 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- PostgreSQL (via Docker or local installation)
- 4GB+ RAM recommended

### Development Tools
- Git
- VS Code or similar IDE
- Terminal/Command Line access

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/jonahmichael/Neovance-AI.git
cd Neovance-AI
```

### 2. Backend Setup

#### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Database Setup
```bash
# Start PostgreSQL with TimescaleDB
docker-compose up -d postgres

# Wait for database to be ready (30 seconds)
sleep 30

# Setup database schema
python scripts/setup_hil_database.py
```

#### Train ML Model
```bash
# Generate training data
python scripts/generate_sepsis_training_data.py

# Train the model
python scripts/train_sepsis_model.py
```

### 3. Frontend Setup

```bash
cd frontend/dashboard

# Install dependencies
npm install

# Build the application
npm run build
```

## Running the System

### Start All Services

1. **Database** (if not already running):
   ```bash
   docker-compose up -d postgres
   ```

2. **Backend API**:
   ```bash
   # From project root
   uvicorn backend.sepsis_prediction_service:app --reload --port 8000
   ```

3. **Frontend Dashboard**:
   ```bash
   # From frontend/dashboard directory
   npm run dev
   ```

4. **Data Pipeline** (optional for live data):
   ```bash
   # From project root
   python scripts/run_ml_hil_system.py
   ```

## Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (username: postgres, password: password)

## Default Credentials

### Doctor Login
- **Username**: DR001
- **Password**: password@dr
- **Role**: Doctor (Full access, can respond to alerts)

### Nurse Login
- **Username**: NS001
- **Password**: password@ns
- **Role**: Nurse (Monitor vitals, receive notifications)

## Verification

### Test the Setup
1. Login with doctor credentials
2. Click "Test Doctor Panel" button
3. Select an action and submit
4. Login with nurse credentials in another browser/tab
5. Verify notification appears in nurse dashboard

### Check Database Connection
```bash
python scripts/test_complete_hil_workflow.py
```

## Troubleshooting

### Common Issues

**Database Connection Failed**
- Ensure Docker is running
- Check if PostgreSQL container is started: `docker ps`
- Verify connection: `docker logs neovance_postgres`

**Frontend Build Errors**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version`

**Backend Import Errors**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Model File Missing**
- Run training script: `python scripts/train_sepsis_model.py`
- Check if model file exists: `ls backend/trained_models/`

## Development Mode

For development with auto-reload:

```bash
# Terminal 1 - Backend with auto-reload
uvicorn backend.sepsis_prediction_service:app --reload --port 8000

# Terminal 2 - Frontend with auto-reload
cd frontend/dashboard && npm run dev

# Terminal 3 - Database
docker-compose up postgres
```