"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import PatientProfile from "@/components/PatientProfile";
import RealTimeChart from "@/components/RealTimeChart";
import StatisticsCards from "@/components/StatisticsCards";
import ClinicalNotes from "@/components/ClinicalNotes";
import LabResults from "@/components/LabResults";
import MedicationTab from "@/components/MedicationTab";
import FeedingOutput from "@/components/FeedingOutput";
import RespiratorySupport from "@/components/RespiratorySupport";
import ScreeningImmunization from "@/components/ScreeningImmunization";
import DischargePlanning from "@/components/DischargePlanning";

interface BabyInfo {
  mrn: string;
  full_name: string;
  sex: string;
  dob: string;
}

export default function Home() {
  const [activeView, setActiveView] = useState("vitals");
  const [baby, setBaby] = useState<BabyInfo | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/baby/B001")
      .then((res) => res.json())
      .then((data) => setBaby(data))
      .catch((err) => console.error("Failed to fetch baby:", err));
  }, []);

  const getViewTitle = () => {
    switch (activeView) {
      case "profile": return "Patient Profile";
      case "vitals": return "Vitals & Trends";
      case "notes": return "Clinical Notes";
      case "labs": return "Lab Results";
      case "medication": return "Medication";
      case "feeding": return "Feeding & Output";
      case "respiratory": return "Respiratory Support";
      case "screening": return "Screening & Immunization";
      case "discharge": return "Discharge Planning";
      default: return "";
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      
      <main className="flex-1 overflow-y-auto">
        {/* Header with Baby Info */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div>
                <span className="text-sm text-muted-foreground">Baby ID:</span>
                <span className="ml-2 text-lg font-bold text-foreground">{baby?.mrn || "Loading..."}</span>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Baby Name:</span>
                <span className="ml-2 text-lg font-bold text-foreground">{baby?.full_name || "Loading..."}</span>
              </div>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div>
                <span className="text-muted-foreground">Gender:</span>
                <span className="ml-2 font-medium">{baby?.sex || "-"}</span>
              </div>
              <div>
                <span className="text-muted-foreground">DOB:</span>
                <span className="ml-2 font-medium">{baby?.dob || "-"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 text-foreground">{getViewTitle()}</h2>

          {activeView === "profile" && <PatientProfile />}
          
          {activeView === "vitals" && (
            <div className="space-y-6">
              <StatisticsCards />
              <RealTimeChart />
            </div>
          )}
          
          {activeView === "notes" && <ClinicalNotes />}
          {activeView === "labs" && <LabResults />}
          {activeView === "medication" && <MedicationTab />}
          {activeView === "feeding" && <FeedingOutput />}
          {activeView === "respiratory" && <RespiratorySupport />}
          {activeView === "screening" && <ScreeningImmunization />}
          {activeView === "discharge" && <DischargePlanning />}
        </div>
      </main>
    </div>
  );
}
