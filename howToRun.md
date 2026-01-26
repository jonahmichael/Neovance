# How to Run Neovance AI - NICU Monitoring System

## 🚀 **One-Command Operation**

The Neovance AI system now features a comprehensive, integrated runner with multiple modes:

### **🏥 EOS Risk Calculator Demo**
Quick demonstration of the Puopolo/Kaiser EOS Risk Calculator:

```bash
cd /mnt/d/Neovance-AI
python run_neovance.py --demo
```

This runs:
✅ Validation tests with 5 clinical scenarios  
✅ Real-time EOS risk calculation simulation  
✅ Database integration verification  
✅ Complete feature demonstration

### **🌐 Full Application Stack**
Complete NICU monitoring system with dashboard:

```bash
cd /mnt/d/Neovance-AI
python run_neovance.py
# OR explicitly:
python run_neovance.py --full-stack
```

This starts:
- 🔧 **Backend API** (FastAPI): http://localhost:8000
- 📊 **Frontend Dashboard** (Next.js): http://localhost:3000  
- 🔬 **EOS Risk Calculator**: Real-time clinical decision support
- 💾 **Database**: SQLite with live vitals storage
- 🌐 **WebSocket**: Live data streaming

### **⚙️ Advanced Options**

```bash
# Backend services only (no frontend)
python run_neovance.py --skip-frontend

# Verbose output for debugging
python run_neovance.py --demo --verbose

# Help and all options
python run_neovance.py --help
```

## 📋 **Prerequisites**

### **Essential (for EOS demo):**
- Python 3.8+
- Basic packages: `pip install fastapi uvicorn sqlalchemy`

### **Full Stack:**
- Node.js 18+ (for dashboard)
- Virtual environment (recommended)

```bash
# Quick setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend dependencies (for full stack)
cd frontend/dashboard && npm install && cd ../..
```

## 🏥 **EOS Risk Calculator Features**

### **Clinical Categories:**
- 🟢 **ROUTINE_CARE** (<1/1000): Standard newborn care
- 🟠 **ENHANCED_MONITORING** (1-3/1000): Enhanced monitoring, consider labs  
- 🔴 **HIGH_RISK** (≥3/1000): Empiric antibiotics recommended

### **Maternal Risk Assessment:**
- Gestational age (weeks + days)
- Maternal intrapartum temperature
- Rupture of membranes duration
- GBS colonization status  
- Antibiotic prophylaxis adequacy
- Clinical chorioamnionitis signs

## 🔧 **Troubleshooting**

- **Ports**: Frontend uses 3000 (or 3005 if occupied), Backend uses 8000
- **Dependencies**: EOS calculator works with Python standard library only
- **Virtual Environment**: Recommended but not required for basic demo

## 📊 **Quick Database Check**

```bash
# View recent EOS calculations
python -c "
import sqlite3
conn = sqlite3.connect('backend/neonatal_ehr.db')
cursor = conn.cursor()
cursor.execute('SELECT mrn, risk_score, status, created_at FROM live_vitals ORDER BY created_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(f'MRN:{row[0]} EOS:{row[1]}/1000 Status:{row[2]} Time:{row[3]}')
conn.close()
"
```

---

**🎯 The integrated runner provides seamless operation of the validated Puopolo/Kaiser EOS Risk Calculator - the most critical clinical feature for NICU sepsis risk stratification.**
