"use client";

interface LabTest {
  id: number;
  name: string;
  description: string;
  status: "Pending" | "In Progress" | "Completed";
  result?: string;
  normalRange?: string;
  date?: string;
  icon?: string;
}

export default function LabResults() {
  const labTests: LabTest[] = [
    {
      id: 1,
      name: "Blood Culture",
      description: "Detects bacteria or fungi in the blood. Confirms sepsis. Takes 24-72 hours for results.",
      status: "In Progress",
      date: "2026-01-26",
      icon: "LAB",
    },
    {
      id: 2,
      name: "Complete Blood Count (CBC) with Differential",
      description: "Checks for high/low WBC count, low platelet count, and increased immature neutrophils (I/T ratio).",
      status: "Completed",
      result: "WBC: 12,500/uL, Platelets: 180,000/uL, I/T ratio: 0.15",
      normalRange: "WBC: 9,000-30,000/uL, Platelets: 150,000-400,000/uL, I/T ratio: <0.2",
      date: "2026-01-26",
      icon: "CBC",
    },
    {
      id: 3,
      name: "C-Reactive Protein (CRP)",
      description: "Marker of inflammation/infection. High levels suggest infection. Often repeated after 24-48 hours.",
      status: "Completed",
      result: "8.5 mg/L",
      normalRange: "<10 mg/L",
      date: "2026-01-26",
      icon: "CRP",
    },
    {
      id: 4,
      name: "Procalcitonin (PCT)",
      description: "More specific marker for bacterial infection. Rises earlier than CRP in sepsis.",
      status: "Pending",
      icon: "PCT",
    },
    {
      id: 5,
      name: "Blood Gas & Lactate",
      description: "Checks for acidosis and poor oxygen delivery. High lactate indicates possible shock/severe sepsis.",
      status: "Completed",
      result: "pH: 7.38, pCO2: 38, Lactate: 1.8 mmol/L",
      normalRange: "pH: 7.35-7.45, pCO2: 35-45, Lactate: <2 mmol/L",
      date: "2026-01-25",
      icon: "GAS",
    },
    {
      id: 6,
      name: "Lumbar Puncture (CSF Analysis)",
      description: "Tests spinal fluid for meningitis - CSF culture, cell count, protein & glucose.",
      status: "Pending",
      icon: "CSF",
    },
    {
      id: 7,
      name: "Urine Culture",
      description: "Tests for urinary tract infection.",
      status: "Pending",
    },
    {
      id: 8,
      name: "Bilirubin Level",
      description: "Total and direct bilirubin for jaundice monitoring.",
      status: "Completed",
      result: "Total: 8.5 mg/dL, Direct: 0.3 mg/dL",
      normalRange: "Total: <12 mg/dL (term), Direct: <0.5 mg/dL",
      date: "2026-01-26",
    },
    {
      id: 9,
      name: "Blood Glucose",
      description: "Monitors for hypoglycemia or hyperglycemia.",
      status: "Completed",
      result: "75 mg/dL",
      normalRange: "45-125 mg/dL",
      date: "2026-01-26",
    },
    {
      id: 10,
      name: "Coagulation Profile (PT, aPTT)",
      description: "Checks blood clotting function.",
      status: "Pending",
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed":
        return "bg-green-100 text-green-700";
      case "In Progress":
        return "bg-yellow-100 text-yellow-700";
      case "Pending":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Laboratory Tests</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Standard neonatal sepsis screening panel and routine newborn tests
        </p>
        
        <div className="grid gap-4">
          {labTests.map((test) => (
            <div
              key={test.id}
              className="border border-border rounded-lg p-4 bg-secondary/20 hover:bg-secondary/40 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{test.icon}</span>
                  <div className="flex-1">
                    <h4 className="font-semibold text-foreground">{test.name}</h4>
                    <p className="text-xs text-muted-foreground mt-1">{test.description}</p>
                    
                    {test.result && (
                      <div className="mt-3 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-foreground">Result:</span>
                          <span className="text-xs text-primary font-semibold">{test.result}</span>
                        </div>
                        {test.normalRange && (
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">Normal:</span>
                            <span className="text-xs text-muted-foreground">{test.normalRange}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-2">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusColor(test.status)}`}>
                    {test.status}
                  </span>
                  {test.date && (
                    <span className="text-xs text-muted-foreground">{test.date}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
