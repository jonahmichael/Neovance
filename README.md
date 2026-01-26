# Neovance-AI: Smart NICU Clinical Decision Support

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-In%20Development-yellow.svg)
![SepsisAlert](https://img.shields.io/badge/ML%20Model-Sepsis%20Predictor-brightgreen.svg)

## The Problem: Alarm Fatigue in the NICU

Critically ill newborns in the NICU are monitored 24/7, but traditional alarm systems are notorious for **false alarms**. These systems alert doctors and nurses the moment a single vital sign crosses a fixed threshold, leading to **alarm fatigue**. When every alarm is noisy, clinicians eventually stop listening when it truly matters.

**Neovance-AI is our solution.** We are building a smart clinical assistant that moves beyond simple thresholds. It monitors complex physiological patterns and trends to deliver alerts only when they are **genuinely meaningful** and tied to real patient deterioration (like sepsis).

## Our Innovation: The Human-in-the-Loop (HIL) Learning

Our system doesn't just notify; **it learns from the experts.**

We capture the doctor's final decision—whether to **Treat**, **Observe**, or **Dismiss** an alert. This decision, paired with the eventual patient outcome (sepsis confirmed or not), is used as continuous, high-value feedback to retrain and refine our ML model. **This creates a continuous learning loop where the AI adapts to real-world clinical behavior and reduces unnecessary alerts over time.**

---

## Tech Stack & Architecture

Neovance-AI is a full-stack, real-time MLOps application built on modern data technologies:

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend/UI** | **Next.js** + **shadcn/ui** | Role-based clinical dashboard (Doctor/Nurse views). |
| **Backend/API** | **FastAPI** | High-performance API for ML prediction and logging. |
| **Data Stream** | **Pathway** | Ingests live sensor data, calculates real-time trends. |
| **Database** | **PostgreSQL + TimescaleDB** | Stores time-series vitals and the crucial HIL action logs. |
| **ML/AI** | **Scikit-learn (RandomForest)** | Offline-trained sepsis prediction model. |

---

## Quick Start: Running Neovance-AI

Follow these steps to get the full application running locally.

### Prerequisites

You will need:
- Python 3.9+
- Node.js (v18+)
- Docker (for easy PostgreSQL setup)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jonahmichael/Neovance-AI.git
   cd Neovance-AI
   ```

2. **Setup PostgreSQL & TimescaleDB (via Docker):**
   ```bash
   docker-compose up -d postgres
   # (Wait for the container to start)
   # Run the schema setup script (details in docs/setup.md)
   ```

3. **Install Python Dependencies (Backend & Pathway):**
   ```bash
   # Make sure you are using the virtual environment
   pip install -r requirements.txt 
   ```

4. **Install Frontend Dependencies:**
   ```bash
   cd frontend/dashboard
   npm install
   cd ../..
   ```

### Running the System (3 Steps)

1. **Train the ML Model:** (This creates the .pkl file the API uses)
   ```bash
   python scripts/train_sepsis_model.py
   ```

2. **Start the Backend API:** (The Prediction Service)
   ```bash
   uvicorn backend.sepsis_prediction_service:app --reload --port 8000
   ```

3. **Start the Frontend UI:**
   ```bash
   cd frontend/dashboard
   npm run dev
   ```

Open your browser to `http://localhost:3000` and login with the credentials in `docs/credentials.md`!

---

## Project Structure

```
Neovance-AI/
├── backend/           # FastAPI services and ML models
├── frontend/          # Next.js dashboard application
├── scripts/           # Training and utility scripts
├── data/              # Sample data and datasets
├── docs/              # Complete documentation
└── tests/             # Test suites
```

## Documentation

Comprehensive documentation is available in the `/docs` folder:

- **[Setup Guide](docs/setup.md)** - Complete installation and configuration
- **[Features](docs/features.md)** - Clinical specifications and ML model details
- **[API Reference](docs/api.md)** - Backend endpoints and data models
- **[Deployment](docs/deployment.md)** - Production deployment guide

---

## Project Status & Contribution

This is an actively developed project. If you're passionate about clinical AI and real-time systems, we welcome contributions! Check out `docs/features.md` for our roadmap.

*   **License:** [MIT License](LICENSE)
*   **Author:** Jonah Michael
