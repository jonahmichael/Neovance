# Neovance-AI: Smart NICU Clinical Decision Support

## 30 Hours. 1 Developer. 1 Life-Saving AI. 1st Place at IIT

Hey.. I built this! @ **Singularity**, a 30-hour AI hackathon at IIT Dharwad powered by **Pathway**. We were expected to "build a real-world AI application using Pathway," & I decided to take up this challenge **ALL BY MYSELF**.

I chose a problem statement in the **MedTech domain**, inspired by a research article on "Artificial & Human Intelligence for Early Identification of Neonatal Sepsis."

### The Problem

Premature newborns don't have fully developed organs & are very prone to infections due to their lack of immunity, & thus are under constant surveillance in a NICU. **Neonatal sepsis** is a bloodstream infection in infants within the first 28 days of life, causing inflammation, organ dysfunction & mortality. But the problem is that newborns do not show clear "infection" symptoms like older children or adults.

Current monitoring systems rely on fixed thresholds: if the heart rate goes too high or too low, or if oxygen levels drop, these systems alert. But these vitals cannot be used solely to conclude sepsis, thus doctors are informed about the baby's condition, for example, the nurse informs, "Baby was restless, didn't feed well, and had trouble breathing." So the doctor considers these & takes necessary action.

### The Solution: Neovance

So I built **Neovance** to bridge this gap where the live data & nurses' observations are no longer independent. Neovance is a real-time clinical decision support system that continuously analyzes live data such as heart rate, respiratory rate, temperature & SpO2 levels along with the observations manually entered by nurses. Using this, the system generates a **"Risk Score"** based on evolving physiological & clinical patterns.

When the risk score crosses a defined threshold, our system alerts the doctor, where they can choose to observe the baby for a specified time, order diagnostic tests, initiate antibiotics, or dismiss the alert. This ensures that the doctors are the final decision-makers & creating a **human-in-the-loop workflow** rather than a fully automated one. Also, our system follows role-based access control, wherein the doctors can view complete patient data, trends, & alert history, while nurses can monitor vitals & act based on the doctor's instructions.

I built the prototype solo within 30 hours using **FastAPI**, **Pathway**, **Next.js** (shadcn/ui, Chart.js), **PostgreSQL**, and **LLM** for ideation & research.

### The Result

After an intensive 30 hours of coding & a presentation round, **Neovance was awarded first place at the hackathon**. Came back with boosted morale & quite some goodies!!

After this hackathon, I'm really driven to start building AI solutions for niche scientific fields where there's so much room for creativity & innovation to be explored by young developers like me. & to you, who is reading this, you could be one too!!

---

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
