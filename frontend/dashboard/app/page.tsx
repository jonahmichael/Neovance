"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import RealTimeChart from "@/components/RealTimeChart";
import ActionPanel from "@/components/ActionPanel";
import PatientHistory from "@/components/PatientHistory";
import ActionLog from "@/components/ActionLog";
import StatisticsCards from "@/components/StatisticsCards";

export default function Home() {
  const [activeView, setActiveView] = useState("monitor");

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold mb-2">
              {activeView === "monitor" && "Real-Time Patient Monitor"}
              {activeView === "history" && "Patient Historical Data"}
              {activeView === "actions" && "Clinical Action Log"}
            </h2>
            <p className="text-muted-foreground">
              {activeView === "monitor" && "Live vital signs monitoring with real-time risk assessment"}
              {activeView === "history" && "Review historical patient data and trends"}
              {activeView === "actions" && "View all clinical actions and interventions"}
            </p>
          </div>

          {activeView === "monitor" && (
            <div className="space-y-6">
              <StatisticsCards />
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div className="xl:col-span-2">
                  <RealTimeChart />
                </div>
                <div>
                  <ActionPanel />
                </div>
              </div>
            </div>
          )}

          {activeView === "history" && (
            <div className="space-y-6">
              <PatientHistory />
            </div>
          )}

          {activeView === "actions" && (
            <div className="space-y-6">
              <ActionLog />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
