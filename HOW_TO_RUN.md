# How to Run Neovance AI - NICU Monitoring System

## 🏥 **Quick Start - EOS Risk Calculator Demo**

For a quick demonstration of the **Puopolo/Kaiser EOS Risk Calculator** (the core clinical feature):

```bash
cd /mnt/d/Neovance-AI
python run_eos_demo.py
```

This will:
✅ Run validation tests with 5 clinical scenarios  
✅ Demonstrate real-time EOS risk calculation  
✅ Show database integration  
✅ Validate all risk categories (ROUTINE_CARE, ENHANCED_MONITORING, HIGH_RISK)

## 🚀 **Full Application Stack**

To run the complete NICU monitoring system with dashboard:

```bash
cd /mnt/d/Neovance-AI
python run_neovance.py
```

This will start:
- 🔧 **Backend API** (FastAPI): http://localhost:8000
- 📊 **Frontend Dashboard** (Next.js): http://localhost:3005  
- 🔬 **EOS Risk Calculator**: Real-time risk assessment
- 💾 **Database**: SQLite with live vitals storage
- 🌐 **WebSocket**: Live data streaming

## 📋 **Prerequisites**

### Essential (for EOS demo):
- Python 3.8+
- Basic Python packages (fastapi, uvicorn, sqlalchemy)

### Full Stack:
- Node.js 18+ (for dashboard)
- Virtual environment (recommended)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend/dashboard
npm install
cd ../..
```

## 🏥 **EOS Risk Calculator Features**

The **Puopolo/Kaiser Early-Onset Sepsis Risk Calculator** provides:

### **Risk Categories:**
- 🟢 **ROUTINE_CARE** (<1/1000): Standard newborn care
- 🟠 **ENHANCED_MONITORING** (1-3/1000): Enhanced monitoring, consider labs  
- 🔴 **HIGH_RISK** (≥3/1000): Empiric antibiotics recommended

### **Maternal Risk Factors:**
- Gestational age (weeks + days)
- Maternal temperature (°C) 
- Rupture of membranes duration (hours)
- GBS colonization status
- Antibiotic administration
- Clinical exam findings

### **Clinical Validation:**
- Based on peer-reviewed research (Puopolo et al.)
- Validated risk thresholds
- Evidence-based clinical decision support

## 🔧 **Troubleshooting**

### Port Conflicts:
- Frontend may use port 3005 if 3000 is occupied
- Backend always uses port 8000

### Virtual Environment:
- The system can run without venv but packages may be missing
- For full functionality, use virtual environment

### Dependencies:
- EOS calculator requires only Python standard library
- Full stack needs FastAPI, React/Next.js dependencies

## 📊 **Database Access**

EOS risk scores are stored in SQLite:

```bash
# View recent EOS calculations
python -c "
import sqlite3
conn = sqlite3.connect('backend/neonatal_ehr.db')
cursor = conn.cursor()
cursor.execute('SELECT mrn, risk_score, status, created_at FROM live_vitals ORDER BY created_at DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'MRN:{row[0]} EOS:{row[1]}/1000 Status:{row[2]} Time:{row[3]}')
conn.close()
"
```

## 🏆 **Production Deployment**

The EOS Risk Calculator is production-ready with:
- ✅ Validated clinical algorithm
- ✅ Real-time processing capability  
- ✅ Database persistence
- ✅ WebSocket streaming
- ✅ Clinical decision support integration

---

**🎯 The EOS Risk Calculator represents the most important clinical feature - providing validated, evidence-based sepsis risk stratification for NICU patients.**