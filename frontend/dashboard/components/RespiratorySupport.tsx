"use client";

import { useState } from "react";

interface RespiratoryEntry {
  id: number;
  date: string;
  time: string;
  supportType: string;
  settings: string;
  spo2: string;
  respiratoryRate: string;
  observations: string;
  recordedBy: string;
}

export default function RespiratorySupport() {
  const [entries, setEntries] = useState<RespiratoryEntry[]>([
    {
      id: 1,
      date: "2026-01-26",
      time: "08:00 AM",
      supportType: "Room Air",
      settings: "No supplemental oxygen",
      spo2: "98%",
      respiratoryRate: "42/min",
      observations: "Breathing comfortably, no retractions",
      recordedBy: "Anjali Patel",
    },
    {
      id: 2,
      date: "2026-01-26",
      time: "04:00 AM",
      supportType: "Room Air",
      settings: "No supplemental oxygen",
      spo2: "97%",
      respiratoryRate: "45/min",
      observations: "Mild nasal flaring resolved",
      recordedBy: "Deepika Singh",
    },
    {
      id: 3,
      date: "2026-01-25",
      time: "08:00 PM",
      supportType: "Nasal Cannula",
      settings: "0.5 L/min O2",
      spo2: "95%",
      respiratoryRate: "48/min",
      observations: "Started low flow oxygen for mild desaturation",
      recordedBy: "Anjali Patel",
    },
  ]);

  const [newEntry, setNewEntry] = useState({
    supportType: "Room Air",
    settings: "",
    spo2: "",
    respiratoryRate: "",
    observations: "",
  });

  const supportTypes = [
    "Room Air",
    "Nasal Cannula",
    "CPAP",
    "BiPAP",
    "High Flow Nasal Cannula",
    "Mechanical Ventilation",
    "Hood Oxygen",
  ];

  const handleAddEntry = () => {
    if (!newEntry.spo2 || !newEntry.respiratoryRate) return;
    const now = new Date();
    const entry: RespiratoryEntry = {
      id: entries.length + 1,
      date: now.toISOString().split("T")[0],
      time: now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      ...newEntry,
      recordedBy: "Anjali Patel",
    };
    setEntries([entry, ...entries]);
    setNewEntry({
      supportType: "Room Air",
      settings: "",
      spo2: "",
      respiratoryRate: "",
      observations: "",
    });
  };

  const currentSupport = entries[0];

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-card rounded-xl p-5 shadow-sm border-2 border-green-200">
        <h3 className="text-lg font-semibold text-primary mb-4">Current Respiratory Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-secondary/30 rounded-lg">
            <p className="text-xs text-muted-foreground uppercase">Support Type</p>
            <p className="text-lg font-bold text-foreground mt-1">{currentSupport?.supportType}</p>
          </div>
          <div className="text-center p-4 bg-secondary/30 rounded-lg">
            <p className="text-xs text-muted-foreground uppercase">SpO2</p>
            <p className="text-lg font-bold text-green-600 mt-1">{currentSupport?.spo2}</p>
          </div>
          <div className="text-center p-4 bg-secondary/30 rounded-lg">
            <p className="text-xs text-muted-foreground uppercase">Respiratory Rate</p>
            <p className="text-lg font-bold text-foreground mt-1">{currentSupport?.respiratoryRate}</p>
          </div>
          <div className="text-center p-4 bg-secondary/30 rounded-lg">
            <p className="text-xs text-muted-foreground uppercase">Settings</p>
            <p className="text-lg font-bold text-foreground mt-1">{currentSupport?.settings || "N/A"}</p>
          </div>
        </div>
      </div>

      {/* Add New Entry */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Record Respiratory Assessment</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-muted-foreground">Support Type</label>
            <select
              value={newEntry.supportType}
              onChange={(e) => setNewEntry({ ...newEntry, supportType: e.target.value })}
              className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
            >
              {supportTypes.map((type) => (
                <option key={type}>{type}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-muted-foreground">Settings (if applicable)</label>
            <input
              type="text"
              value={newEntry.settings}
              onChange={(e) => setNewEntry({ ...newEntry, settings: e.target.value })}
              placeholder="e.g., FiO2 30%, PEEP 5"
              className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground">SpO2 (%)</label>
            <input
              type="text"
              value={newEntry.spo2}
              onChange={(e) => setNewEntry({ ...newEntry, spo2: e.target.value })}
              placeholder="e.g., 98%"
              className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground">Respiratory Rate (/min)</label>
            <input
              type="text"
              value={newEntry.respiratoryRate}
              onChange={(e) => setNewEntry({ ...newEntry, respiratoryRate: e.target.value })}
              placeholder="e.g., 42/min"
              className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-sm text-muted-foreground">Observations</label>
            <input
              type="text"
              value={newEntry.observations}
              onChange={(e) => setNewEntry({ ...newEntry, observations: e.target.value })}
              placeholder="Any observations (retractions, grunting, nasal flaring, etc.)"
              className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
            />
          </div>
        </div>
        <button
          onClick={handleAddEntry}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90"
        >
          Record Assessment
        </button>
      </div>

      {/* History */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Respiratory Support History</h3>
        <div className="space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="p-4 border border-border rounded-lg bg-secondary/20">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                    {entry.supportType}
                  </span>
                  {entry.settings && (
                    <span className="text-xs text-muted-foreground">{entry.settings}</span>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">
                  {entry.date} at {entry.time}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                <p><span className="text-muted-foreground">SpO2:</span> <span className="font-medium text-green-600">{entry.spo2}</span></p>
                <p><span className="text-muted-foreground">RR:</span> <span className="font-medium">{entry.respiratoryRate}</span></p>
              </div>
              {entry.observations && (
                <p className="text-sm text-foreground">{entry.observations}</p>
              )}
              <p className="text-xs text-muted-foreground mt-2">Recorded by: {entry.recordedBy}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
