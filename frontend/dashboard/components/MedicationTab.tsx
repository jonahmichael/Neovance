"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";

interface Medication {
  id: number;
  name: string;
  dosage: string;
  route: string;
  frequency: string;
  startDate: string;
  duration: string;
  status: "Active" | "Completed" | "Pending Approval";
  prescribedBy: string;
  category: string;
}

export default function MedicationTab() {
  const [showAlert, setShowAlert] = useState(false);
  const [selectedAntibiotic, setSelectedAntibiotic] = useState("");

  const currentMedications: Medication[] = [
    {
      id: 1,
      name: "Vitamin K (Phytonadione)",
      dosage: "1 mg",
      route: "IM",
      frequency: "Single dose",
      startDate: "2026-01-20",
      duration: "One-time",
      status: "Completed",
      prescribedBy: "Dr. Rajesh Kumar",
      category: "Prophylaxis",
    },
    {
      id: 2,
      name: "Hepatitis B Vaccine",
      dosage: "0.5 mL",
      route: "IM",
      frequency: "Per schedule",
      startDate: "2026-01-20",
      duration: "As per immunization schedule",
      status: "Completed",
      prescribedBy: "Dr. Rajesh Kumar",
      category: "Immunization",
    },
  ];

  const antibioticOptions = {
    earlyOnset: [
      { name: "Ampicillin + Gentamicin", indication: "First-line for E. coli and Group B Strep" },
      { name: "Ampicillin + Amikacin", indication: "Alternative first-line" },
    ],
    lateOnset: [
      { name: "Cefotaxime + Amikacin", indication: "Broad spectrum coverage" },
      { name: "Piperacillin-Tazobactam + Amikacin", indication: "Extended spectrum" },
      { name: "Vancomycin", indication: "If MRSA suspected" },
    ],
    severe: [
      { name: "Meropenem", indication: "Multi-drug resistant organisms" },
      { name: "Imipenem", indication: "Severe NICU infections" },
      { name: "Linezolid", indication: "Resistant gram-positive" },
      { name: "Colistin", indication: "Last resort for MDR infections" },
    ],
    fungal: [
      { name: "Fluconazole", indication: "Candida infection" },
      { name: "Amphotericin B", indication: "Severe fungal sepsis" },
    ],
  };

  const supportiveMedications = [
    { name: "IV Fluids", purpose: "Hydration and electrolyte balance" },
    { name: "Oxygen", purpose: "Respiratory support" },
    { name: "Glucose 10%", purpose: "Prevent hypoglycemia" },
    { name: "Dopamine/Dobutamine", purpose: "Inotropic support if shock" },
    { name: "Paracetamol", purpose: "Fever management" },
  ];

  const handleAlertDoctor = () => {
    setShowAlert(true);
    setTimeout(() => setShowAlert(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Alert Banner */}
      {showAlert && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <span>Doctor has been notified about antibiotic recommendation: {selectedAntibiotic}</span>
        </div>
      )}

      {/* Current Medications */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Current Medications</h3>
        <div className="space-y-3">
          {currentMedications.map((med) => (
            <div key={med.id} className="border border-border rounded-lg p-4 bg-secondary/20">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold text-foreground">{med.name}</h4>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-1 mt-2 text-sm">
                    <p><span className="text-muted-foreground">Dosage:</span> {med.dosage}</p>
                    <p><span className="text-muted-foreground">Route:</span> {med.route}</p>
                    <p><span className="text-muted-foreground">Frequency:</span> {med.frequency}</p>
                    <p><span className="text-muted-foreground">Prescribed by:</span> {med.prescribedBy}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  med.status === "Completed" ? "bg-green-100 text-green-700" :
                  med.status === "Active" ? "bg-blue-100 text-blue-700" :
                  "bg-yellow-100 text-yellow-700"
                }`}>
                  {med.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Antibiotic Recommendations */}
      <div className="bg-card rounded-xl p-5 shadow-sm border-2 border-primary/30">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-primary">Antibiotic Recommendations (If Sepsis Suspected)</h3>
        </div>
        
        <p className="text-sm text-muted-foreground mb-4">
          Select appropriate antibiotic based on sepsis type. Doctor approval required before administration.
        </p>

        {/* Early-onset */}
        <div className="mb-4">
          <h4 className="font-medium text-foreground mb-2">Early-onset Sepsis (within 72 hours of birth)</h4>
          <div className="grid gap-2">
            {antibioticOptions.earlyOnset.map((ab) => (
              <label key={ab.name} className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-secondary/30 cursor-pointer">
                <input
                  type="radio"
                  name="antibiotic"
                  value={ab.name}
                  onChange={(e) => setSelectedAntibiotic(e.target.value)}
                  className="w-4 h-4 text-primary"
                />
                <div>
                  <span className="font-medium text-sm">{ab.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">- {ab.indication}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Late-onset */}
        <div className="mb-4">
          <h4 className="font-medium text-foreground mb-2">Late-onset Sepsis (after 72 hours)</h4>
          <div className="grid gap-2">
            {antibioticOptions.lateOnset.map((ab) => (
              <label key={ab.name} className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-secondary/30 cursor-pointer">
                <input
                  type="radio"
                  name="antibiotic"
                  value={ab.name}
                  onChange={(e) => setSelectedAntibiotic(e.target.value)}
                  className="w-4 h-4 text-primary"
                />
                <div>
                  <span className="font-medium text-sm">{ab.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">- {ab.indication}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Severe/Resistant */}
        <div className="mb-4">
          <h4 className="font-medium text-foreground mb-2">Severe/Resistant Infections (NICU cases)</h4>
          <div className="grid gap-2">
            {antibioticOptions.severe.map((ab) => (
              <label key={ab.name} className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-secondary/30 cursor-pointer">
                <input
                  type="radio"
                  name="antibiotic"
                  value={ab.name}
                  onChange={(e) => setSelectedAntibiotic(e.target.value)}
                  className="w-4 h-4 text-primary"
                />
                <div>
                  <span className="font-medium text-sm">{ab.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">- {ab.indication}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Fungal */}
        <div className="mb-4">
          <h4 className="font-medium text-foreground mb-2">Fungal Sepsis</h4>
          <div className="grid gap-2">
            {antibioticOptions.fungal.map((ab) => (
              <label key={ab.name} className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-secondary/30 cursor-pointer">
                <input
                  type="radio"
                  name="antibiotic"
                  value={ab.name}
                  onChange={(e) => setSelectedAntibiotic(e.target.value)}
                  className="w-4 h-4 text-primary"
                />
                <div>
                  <span className="font-medium text-sm">{ab.name}</span>
                  <span className="text-xs text-muted-foreground ml-2">- {ab.indication}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={handleAlertDoctor}
          disabled={!selectedAntibiotic}
          className="w-full mt-4 px-4 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Alert Doctor for Antibiotic Approval
        </button>

        <p className="text-xs text-red-500 mt-3 text-center font-medium">
          Never administer antibiotics to a newborn without a doctors prescription.
        </p>
      </div>

      {/* Supportive Medications */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Supportive Medications (May be given alongside)</h3>
        <div className="grid grid-cols-2 gap-3">
          {supportiveMedications.map((med) => (
            <div key={med.name} className="p-3 border border-border rounded-lg bg-secondary/20">
              <p className="font-medium text-sm text-foreground">{med.name}</p>
              <p className="text-xs text-muted-foreground">{med.purpose}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
