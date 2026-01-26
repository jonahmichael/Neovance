"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";

interface BabyProfile {
  vitamin_k_given: boolean;
  hep_b_vaccine: boolean;
  eye_prophylaxis: boolean;
  hearing_screening: string;
  vision_screening: string;
  metabolic_screening: string;
  pulse_oximetry: string;
}

export default function ScreeningImmunization() {
  const [baby, setBaby] = useState<BabyProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/baby/B001")
      .then((res) => res.json())
      .then((data) => {
        setBaby(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  const immunizations = [
    {
      name: "Vitamin K Injection",
      description: "Prevents Vitamin K Deficiency Bleeding (VKDB)",
      given: baby?.vitamin_k_given,
      dueDate: "At birth",
    },
    {
      name: "Hepatitis B Vaccine (1st dose)",
      description: "Protects against Hepatitis B virus",
      given: baby?.hep_b_vaccine,
      dueDate: "Within 24 hours of birth",
    },
    {
      name: "Eye Prophylaxis",
      description: "Erythromycin ointment to prevent ophthalmia neonatorum",
      given: baby?.eye_prophylaxis,
      dueDate: "Within 1 hour of birth",
    },
    {
      name: "BCG Vaccine",
      description: "Protects against tuberculosis",
      given: false,
      dueDate: "At birth or within first week",
    },
    {
      name: "OPV (Oral Polio Vaccine) - Zero dose",
      description: "Protects against poliomyelitis",
      given: false,
      dueDate: "At birth",
    },
  ];

  const screenings = [
    {
      name: "Newborn Hearing Screening (OAE/ABR)",
      description: "Detects hearing impairment early",
      result: baby?.hearing_screening || "-",
      status: baby?.hearing_screening === "Passed" ? "passed" : "pending",
    },
    {
      name: "Red Reflex Test (Vision Screening)",
      description: "Screens for cataracts, retinoblastoma, and other eye abnormalities",
      result: baby?.vision_screening || "-",
      status: baby?.vision_screening?.includes("present") ? "passed" : "pending",
    },
    {
      name: "Pulse Oximetry (CCHD Screening)",
      description: "Screens for Critical Congenital Heart Disease",
      result: baby?.pulse_oximetry || "-",
      status: baby?.pulse_oximetry?.includes("98%") || baby?.pulse_oximetry?.includes("room air") ? "passed" : "pending",
    },
    {
      name: "Newborn Metabolic Screening",
      description: "Tests for PKU, Hypothyroidism, Galactosemia, CAH, and other metabolic disorders",
      result: baby?.metabolic_screening || "-",
      status: baby?.metabolic_screening === "Normal panel" ? "passed" : "pending",
    },
    {
      name: "Jaundice Screening (TcB/TSB)",
      description: "Monitors bilirubin levels for hyperbilirubinemia",
      result: "8.5 mg/dL - Within normal limits",
      status: "passed",
    },
    {
      name: "Blood Glucose Monitoring",
      description: "Screens for hypoglycemia in at-risk newborns",
      result: "75 mg/dL - Normal",
      status: "passed",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Immunizations */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Immunizations</h3>
        <div className="space-y-3">
          {immunizations.map((imm) => (
            <div
              key={imm.name}
              className="flex items-center justify-between p-4 border border-border rounded-lg bg-secondary/20"
            >
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  imm.given ? "bg-green-100" : "bg-gray-100"
                }`}>
                  {imm.given ? (
                    <Check className="w-5 h-5 text-green-600" />
                  ) : (
                    <X className="w-5 h-5 text-gray-400" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-foreground">{imm.name}</p>
                  <p className="text-xs text-muted-foreground">{imm.description}</p>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  imm.given ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                }`}>
                  {imm.given ? "Administered" : "Pending"}
                </span>
                <p className="text-xs text-muted-foreground mt-1">Due: {imm.dueDate}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Screenings */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Newborn Screenings</h3>
        <div className="space-y-3">
          {screenings.map((screen) => (
            <div
              key={screen.name}
              className="p-4 border border-border rounded-lg bg-secondary/20"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-foreground">{screen.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{screen.description}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  screen.status === "passed" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                }`}>
                  {screen.status === "passed" ? "Passed" : "Pending"}
                </span>
              </div>
              <div className="mt-3 p-2 bg-background rounded border border-border">
                <p className="text-xs text-muted-foreground">Result:</p>
                <p className="text-sm font-medium text-foreground">{screen.result}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming Immunizations */}
      <div className="bg-card rounded-xl p-5 shadow-sm border border-orange-200">
        <h3 className="text-lg font-semibold text-orange-600 mb-4">Upcoming Immunizations (As per IAP Schedule)</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="p-3 bg-orange-50 rounded-lg">
            <p className="font-medium text-sm">6 Weeks</p>
            <p className="text-xs text-muted-foreground">DTwP/DTaP, IPV, Hib, Rotavirus, PCV</p>
          </div>
          <div className="p-3 bg-orange-50 rounded-lg">
            <p className="font-medium text-sm">10 Weeks</p>
            <p className="text-xs text-muted-foreground">DTwP/DTaP, IPV, Hib, Rotavirus, PCV</p>
          </div>
          <div className="p-3 bg-orange-50 rounded-lg">
            <p className="font-medium text-sm">14 Weeks</p>
            <p className="text-xs text-muted-foreground">DTwP/DTaP, IPV, Hib, Rotavirus, PCV</p>
          </div>
          <div className="p-3 bg-orange-50 rounded-lg">
            <p className="font-medium text-sm">6 Months</p>
            <p className="text-xs text-muted-foreground">Influenza (1st dose), Hepatitis B (if not given earlier)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
