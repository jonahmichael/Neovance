# Neovance-AI: Hour-by-Hour Development Timeline

This document tracks the detailed progress of the Neovance-AI NICU monitoring system development, providing a comprehensive timeline beyond git commit history.

---

## Project Overview
**Project Name:** Neovance-AI  
**Purpose:** Real-time NICU monitoring system for premature babies  
**Start Date:** January 25, 2026  

---

## Development Timeline

### Hour 1: Initial Setup and Core Simulator Development
**Time:** [Current Session Start]  
**Status:** COMPLETED

#### Tasks Completed:
1. **Project Initialization**
   - Created project structure at `d:\Neovance-AI`
   - Established README.md foundation

2. **Simulator Script Development (`simulator.py`)**
   - Implemented `NICUSimulator` class with state machine architecture
   - Created two operational modes:
     - **NORMAL Mode:** Stable vitals with Gaussian noise
     - **SEPSIS Mode:** Deteriorating vitals with continuous drift logic
   
3. **Core Features Implemented:**
   - Real-time data generation (1-second intervals)
   - CSV file output to `data/stream.csv`
   - Automatic header creation on first run
   - File buffer flushing after every write (critical for real-time pipeline)
   - Keyboard-based mode switching:
     - Press 's' → SEPSIS mode
     - Press 'n' → NORMAL mode
   
4. **Patient Configuration:**
   - Patient ID: "Baby_A"
   - Baseline vitals configured:
     - HR (Heart Rate): 145 bpm
     - SpO2 (Oxygen Saturation): 98%
     - RR (Respiratory Rate): 50 breaths/min
     - Temp (Temperature): 37.0°C
     - MAP (Mean Arterial Pressure): 35 mmHg

5. **Safety Mechanisms:**
   - SpO2 floor limit: 40% (prevents death scenario)
   - HR ceiling limit: 220 bpm (prevents unrealistic values)
   - Temperature floor: 35.0°C (hypothermia protection)

6. **Sepsis Drift Logic:**
   - HR increases: +1 bpm per second
   - SpO2 decreases: -0.5% per second
   - Temperature decreases: -0.02°C per second
   - RR variability increased (respiratory distress simulation)

7. **Code Refinement:**
   - Removed all emoji characters for professional output
   - Implemented clean logging with prefixes: `[INFO]`, `[ALERT]`, `[NORMAL]`, `[SEPSIS]`
   - Added comprehensive docstrings and comments

#### Technical Decisions:
- **Library Choice:** Used `keyboard` library for non-blocking input
- **Data Format:** CSV with ISO timestamp format
- **File I/O:** Append mode with immediate flush for real-time visibility
- **State Management:** Object-oriented approach with drift accumulators

#### Files Created:
- `simulator.py` (Main data generation script)
- `hour by hour.md` (This timeline document)

#### Dependencies Required:
```
keyboard
```

#### Next Steps Planned:
- Test simulator with Pathway data pipeline
- Monitor CSV file growth and performance
- Validate real-time data streaming
- Consider adding more patient profiles
- Implement data validation layer
- Add logging to file for debugging

---

## Notes and Observations

### Design Considerations:
- **Why 1-second intervals?** Balance between real-world simulation and system performance
- **Why CSV format?** Simple, human-readable, compatible with Pathway streaming
- **Why keyboard library?** Enables live mode switching during demonstrations without GUI overhead

### Potential Future Enhancements:
1. Multi-patient simulation (Baby_A, Baby_B, Baby_C)
2. Additional pathological states (apnea, bradycardia)
3. Configuration file for baseline values
4. Web dashboard for real-time visualization
5. Integration with ML model for anomaly detection
6. Alert thresholds with notification system
7. Data replay functionality from historical CSV
8. Synthetic noise patterns based on medical literature

---

## Session Log Format

Each session entry should include:
- **Time:** Hour marker or timestamp
- **Status:** COMPLETED | IN PROGRESS | BLOCKED | PLANNED
- **Tasks Completed:** Bullet list of what was accomplished
- **Technical Decisions:** Key architectural or implementation choices
- **Files Modified/Created:** List of changed files
- **Blockers/Issues:** Any problems encountered
- **Next Steps:** What to work on next

---

*Last Updated: January 25, 2026*
