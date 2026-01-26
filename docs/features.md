# Features & Clinical Specification

This document details the current capabilities and underlying clinical models used in the Neovance-AI system.

## 1. Core Clinical Features

Our system provides two levels of risk assessment, combining established medicine with modern ML.

### A. Real-time Risk Assessment (The ML Brain)
- **Engine:** Trained Scikit-learn (RandomForest) model.
- **Goal:** Predicts the probability of the baby developing sepsis (Sepsis Group 1 or 3) within the next **X hours**.
- **Alert Output:** **`ML Risk Score`** (0-1) and **`Onset Window`** (e.g., 6, 12, or 24 hours).
- **Inputs:** The ML model uses a rich feature set, including live vitals, historical trends, patient context, and the output of the classic EOS calculator (see below).

### B. Integrated Clinical Calculator (The Classic Feature)
- **Model:** **Neonatal Early-Onset Sepsis (EOS) Risk Calculator** (Puopolo et al. 2011).
- **Purpose:** The EOS score is calculated in real-time and injected as a **powerful feature** into the ML model, combining established medicine with data-driven pattern detection.

---

## 2. The Human-in-the-Loop (HIL) Decision Cycle

This workflow ensures the AI serves as a *decision support tool*, keeping the human clinician in full control.

### A. Alert Triggering
- **Mechanism:** The Pathway component detects critical instability patterns (not just fixed thresholds) and sends the data snapshot to the FastAPI `/predict_sepsis` endpoint.
- **Alert Condition:** An alert is logged when the **ML Risk Score > 0.75**.
- **Alert Display:** The system displays the warning: **"Baby [MRN] might develop sepsis in [X] hours."**

### B. Role-Based Permissions

| User Role | Access & Privilege | HIL Function |
| :--- | :--- | :--- |
| **Doctor (`DR001`)** | **Full Access.** Can view all data, charts, and history. | **Decision Maker.** **Only** the Doctor can respond to an active alert via the Critical Action Panel. |
| **Nurse (`NS001`)** | **Full Access** to monitor vitals and input bedside observations. | **Action Taker.** Cannot respond to the ML alert. Receives the Doctor's final instruction as a notification. |

### C. Doctor's Critical Action Panel (The HIL Feedback)
When an alert is active, the Doctor must choose one of these actions, which are logged for the model's future retraining:

1.  **Observe Patient:** Doctor sets monitoring duration (1-24 hours). Believes the alert may be manageable with observation.
2.  **Send for Lab Tests:** Doctor selects specific laboratory investigations (CBC, CRP, Blood Culture, etc.). Requires immediate confirmation.
3.  **Treat with Antibiotics:** Doctor selects specific antibiotics (Ampicillin, Gentamicin, etc.). Confirms highest risk level and starts therapy.
4.  **Dismiss Alert:** Doctor provides reason for dismissal, giving high-value **negative feedback** to the AI.
5.  **Custom Instructions:** Doctor provides specific monitoring protocols or custom instructions.

---

## 3. Data Integrity & Continuous Learning

### A. Chain of Custody
- **Action Logging:** Every Doctor action is immediately logged into the PostgreSQL `alerts` table with a timestamp and `doctor_id`.
- **Data Audit:** All changes to a baby's core data (e.g., nurse observation inputs) are tracked to ensure a full audit trail.

### B. The Model's Reward Signal
- **Mechanism:** After an alert is logged, the system waits for the final outcome (`sepsis_confirmed`).
- **Learning Logic:**
    - **Reward (+1):** Model correctly predicted high risk, or correctly predicted low risk (True Positive/True Negative).
    - **Penalty (-1 or -2):** Model was wrong (False Positive or False Negative).
- **Retraining:** The model is periodically retrained on this ever-growing dataset of **State + Action + Outcome** to adapt to the hospital's specific clinical patterns.

---

## 4. Technical Specifications

| Component | Detail |
| :--- | :--- |
| **Time-Series DB** | PostgreSQL with TimescaleDB Extension |
| **Vitals Charts** | Chart.js integration for real-time line charts |
| **APIs** | All HIL and prediction logic is exposed via **FastAPI** (Python) |
| **Frontend Framework** | **Next.js** for modern, high-performance UI |
| **Styling** | **shadcn/ui** and **Tailwind CSS** for clean, professional clinical aesthetic |

---

## 5. Current Capabilities

### Real-time Monitoring
- Heart Rate (HR) with pediatric normal ranges
- Oxygen Saturation (SpO2) with preterm targets
- Respiratory Rate (RR) with apnea detection
- Temperature with infection thresholds
- Mean Arterial Pressure (MAP) with perfusion status

### Alert System
- ML-driven sepsis risk prediction
- Role-based notification system
- Doctor decision capture
- Nurse instruction delivery

### Clinical Decision Support
- EOS calculator integration
- Trend analysis and pattern recognition
- Historical data comparison
- Risk stratification with clinical context