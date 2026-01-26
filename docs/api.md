# API Reference

This document provides detailed information about the Neovance-AI backend API endpoints.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently using hardcoded credentials for development. Production deployment will require proper authentication implementation.

## Endpoints

### Health Check

#### GET `/health`
Returns the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T10:30:00Z",
  "version": "1.0.0"
}
```

### Sepsis Prediction

#### POST `/predict_sepsis`
Performs ML-based sepsis risk prediction on provided vital signs data.

**Request Body:**
```json
{
  "baby_id": "B001",
  "hr": 150,
  "spo2": 92,
  "rr": 45,
  "temp": 37.2,
  "map": 35,
  "timestamp": "2026-01-26T10:30:00Z"
}
```

**Response:**
```json
{
  "baby_id": "B001",
  "risk_score": 0.875,
  "prediction": "HIGH_RISK",
  "recommended_action": "IMMEDIATE_ATTENTION",
  "confidence": 0.92,
  "timestamp": "2026-01-26T10:30:00Z",
  "model_version": "1.0.0"
}
```

### Alert Management

#### POST `/alerts`
Creates a new sepsis alert in the system.

**Request Body:**
```json
{
  "baby_id": "B001",
  "risk_score": 0.875,
  "alert_status": "PENDING_DOCTOR_ACTION",
  "vitals_snapshot": {
    "hr": 150,
    "spo2": 92,
    "rr": 45,
    "temp": 37.2,
    "map": 35
  }
}
```

#### GET `/alerts/{alert_id}`
Retrieves details of a specific alert.

#### PUT `/alerts/{alert_id}/action`
Records doctor's action on an alert.

**Request Body:**
```json
{
  "doctor_id": "DR001",
  "action": "ANTIBIOTICS",
  "action_details": "Prescribed Antibiotics: Ampicillin, Gentamicin",
  "antibiotics": ["Ampicillin", "Gentamicin"]
}
```

### Baby Management

#### GET `/babies/{baby_id}`
Retrieves baby information and current vital signs.

**Response:**
```json
{
  "baby_id": "B001",
  "mrn": "B001",
  "full_name": "Baby Smith",
  "dob": "2026-01-20",
  "gestational_age": 32,
  "current_vitals": {
    "hr": 140,
    "spo2": 94,
    "rr": 42,
    "temp": 37.0,
    "map": 38
  },
  "last_updated": "2026-01-26T10:30:00Z"
}
```

#### GET `/babies/{baby_id}/vitals`
Retrieves historical vital signs data.

**Query Parameters:**
- `hours`: Number of hours of data to retrieve (default: 24)
- `resolution`: Data resolution - "minute", "5min", "hour" (default: "5min")

### EOS Calculator

#### POST `/calculate_eos`
Calculates Early-Onset Sepsis (EOS) risk score using established clinical parameters.

**Request Body:**
```json
{
  "gestational_age": 32,
  "birth_weight": 1800,
  "maternal_fever": false,
  "maternal_antibiotics": true,
  "rom_duration": 8,
  "clinical_signs": ["temperature_instability"]
}
```

**Response:**
```json
{
  "eos_score": 0.65,
  "risk_category": "INTERMEDIATE",
  "recommendations": [
    "Monitor vital signs closely",
    "Consider laboratory evaluation"
  ]
}
```

## Data Models

### Vital Signs
```typescript
interface VitalSigns {
  hr: number;        // Heart rate (bpm)
  spo2: number;      // Oxygen saturation (%)
  rr: number;        // Respiratory rate (breaths/min)
  temp: number;      // Temperature (Celsius)
  map: number;       // Mean arterial pressure (mmHg)
  timestamp: string; // ISO 8601 datetime
}
```

### Alert
```typescript
interface Alert {
  alert_id: number;
  baby_id: string;
  risk_score: number;
  alert_status: "PENDING_DOCTOR_ACTION" | "DOCTOR_RESPONDED" | "RESOLVED";
  doctor_action?: string;
  action_details?: string;
  created_at: string;
  updated_at: string;
}
```

### Doctor Action
```typescript
interface DoctorAction {
  action_type: "OBSERVE" | "LAB_TESTS" | "ANTIBIOTICS" | "DISMISS" | "CUSTOM";
  duration?: string;        // For OBSERVE action
  lab_tests?: string[];     // For LAB_TESTS action
  antibiotics?: string[];   // For ANTIBIOTICS action
  dismiss_reason?: string;  // For DISMISS action
  custom_instructions?: string; // For CUSTOM action
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Input data format error |
| 500 | Internal Server Error - Server-side error |

## Rate Limiting

Current implementation has no rate limiting. Production deployment should implement appropriate rate limiting for API security.

## Development

### Testing the API
Use the interactive API documentation available at:
```
http://localhost:8000/docs
```

### Adding New Endpoints
1. Add endpoint function to appropriate module in `/backend`
2. Update this documentation
3. Add tests in `/tests` directory
4. Update frontend integration if needed