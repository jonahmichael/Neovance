"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { NotificationProvider } from "@/contexts/NotificationContext";
import LoginPage from "@/components/LoginPage";
import Sidebar from "@/components/Sidebar";
import NotificationBell from "@/components/NotificationBell";
import PatientProfile from "@/components/PatientProfile";
import VitalsAndTrends from "@/components/VitalsAndTrends";
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
  const { user } = useAuth();
  const [activeView, setActiveView] = useState("vitals");
  const [baby, setBaby] = useState<BabyInfo | null>(null);

  useEffect(() => {
    fetch("/api/baby/B001")
      .then((res) => res.json())
      .then((data) => setBaby(data))
      .catch((err) => console.error("Failed to fetch baby:", err));
  }, []);

  // Show login page if not authenticated
  if (!user || !user.isLoggedIn) {
    return <LoginPage />;
  }

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
    <NotificationProvider>
      <div className="flex h-screen overflow-hidden font-sans bg-gray-50">
        <Sidebar activeView={activeView} onViewChange={setActiveView} />
        
        <main className="flex-1 overflow-y-auto">
          {/* Header with Baby Info and User Role */}
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <div>
                  <span className="text-sm text-gray-600 font-sans">Baby ID:</span>
                  <span className="ml-2 text-lg font-bold text-gray-900 font-sans">{baby?.mrn || "Loading..."}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600 font-sans">Baby Name:</span>
                <span className="ml-2 text-lg font-bold text-gray-900 font-sans">{baby?.full_name || "Loading..."}</span>
              </div>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div>
                <span className="text-gray-600 font-sans">Gender:</span>
                <span className="ml-2 font-medium text-gray-900 font-sans">{baby?.sex || "-"}</span>
              </div>
              <div>
                <span className="text-gray-600 font-sans">DOB:</span>
                <span className="ml-2 font-medium text-gray-900 font-sans">{baby?.dob || "-"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium font-sans border ${
                  user.role === 'DOCTOR' 
                    ? 'bg-blue-100 text-blue-800 border-blue-200' 
                    : 'bg-green-100 text-green-800 border-green-200'
                }`}>
                  {user.role === 'DOCTOR' ? 'Doctor' : 'Nurse'}
                </span>
                <span className="text-gray-400">|</span>
                <span className="font-medium text-gray-900 font-sans">{user.name}</span>
              </div>
              <NotificationBell />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6 text-gray-900 font-sans">{getViewTitle()}</h2>

          {activeView === "profile" && <PatientProfile />}
          
          {activeView === "vitals" && <VitalsAndTrends />}
          
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
    </NotificationProvider>
  );
}
