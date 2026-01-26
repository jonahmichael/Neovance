"use client";

import { useState } from "react";

interface FeedingEntry {
  id: number;
  date: string;
  time: string;
  type: string;
  amount: string;
  tolerance: string;
  notes: string;
  recordedBy: string;
}

interface OutputEntry {
  id: number;
  date: string;
  time: string;
  type: "Urine" | "Stool";
  description: string;
  recordedBy: string;
}

export default function FeedingOutput() {
  const [feedingEntries, setFeedingEntries] = useState<FeedingEntry[]>([
    {
      id: 1,
      date: "2026-01-26",
      time: "08:00 AM",
      type: "Expressed Breast Milk",
      amount: "30 mL",
      tolerance: "Good",
      notes: "Strong suck reflex, no regurgitation",
      recordedBy: "Anjali Patel",
    },
    {
      id: 2,
      date: "2026-01-26",
      time: "05:00 AM",
      type: "Expressed Breast Milk",
      amount: "25 mL",
      tolerance: "Good",
      notes: "Fed well, burped after feeding",
      recordedBy: "Anjali Patel",
    },
    {
      id: 3,
      date: "2026-01-26",
      time: "02:00 AM",
      type: "Expressed Breast Milk",
      amount: "28 mL",
      tolerance: "Fair",
      notes: "Slight fussiness, completed feeding",
      recordedBy: "Deepika Singh",
    },
  ]);

  const [outputEntries, setOutputEntries] = useState<OutputEntry[]>([
    {
      id: 1,
      date: "2026-01-26",
      time: "07:30 AM",
      type: "Urine",
      description: "Adequate output, clear yellow",
      recordedBy: "Anjali Patel",
    },
    {
      id: 2,
      date: "2026-01-26",
      time: "06:00 AM",
      type: "Stool",
      description: "Transitional stool, greenish-brown",
      recordedBy: "Anjali Patel",
    },
    {
      id: 3,
      date: "2026-01-26",
      time: "03:00 AM",
      type: "Urine",
      description: "Normal output",
      recordedBy: "Deepika Singh",
    },
  ]);

  const [newFeeding, setNewFeeding] = useState({
    type: "Expressed Breast Milk",
    amount: "",
    tolerance: "Good",
    notes: "",
  });

  const [newOutput, setNewOutput] = useState({
    type: "Urine" as "Urine" | "Stool",
    description: "",
  });

  const handleAddFeeding = () => {
    if (!newFeeding.amount) return;
    const now = new Date();
    const entry: FeedingEntry = {
      id: feedingEntries.length + 1,
      date: now.toISOString().split("T")[0],
      time: now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      ...newFeeding,
      recordedBy: "Anjali Patel",
    };
    setFeedingEntries([entry, ...feedingEntries]);
    setNewFeeding({ type: "Expressed Breast Milk", amount: "", tolerance: "Good", notes: "" });
  };

  const handleAddOutput = () => {
    if (!newOutput.description) return;
    const now = new Date();
    const entry: OutputEntry = {
      id: outputEntries.length + 1,
      date: now.toISOString().split("T")[0],
      time: now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      ...newOutput,
      recordedBy: "Anjali Patel",
    };
    setOutputEntries([entry, ...outputEntries]);
    setNewOutput({ type: "Urine", description: "" });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Feeding Section */}
      <div className="space-y-4">
        <div className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4">Record Feeding</h3>
          <div className="space-y-3">
            <div>
              <label className="text-sm text-muted-foreground">Feeding Type</label>
              <select
                value={newFeeding.type}
                onChange={(e) => setNewFeeding({ ...newFeeding, type: e.target.value })}
                className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
              >
                <option>Expressed Breast Milk</option>
                <option>Direct Breastfeeding</option>
                <option>Formula</option>
                <option>IV Fluids</option>
                <option>NG Tube</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Amount</label>
              <input
                type="text"
                value={newFeeding.amount}
                onChange={(e) => setNewFeeding({ ...newFeeding, amount: e.target.value })}
                placeholder="e.g., 30 mL"
                className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Tolerance</label>
              <select
                value={newFeeding.tolerance}
                onChange={(e) => setNewFeeding({ ...newFeeding, tolerance: e.target.value })}
                className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
              >
                <option>Good</option>
                <option>Fair</option>
                <option>Poor</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Notes</label>
              <input
                type="text"
                value={newFeeding.notes}
                onChange={(e) => setNewFeeding({ ...newFeeding, notes: e.target.value })}
                placeholder="Any observations..."
                className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
              />
            </div>
            <button
              onClick={handleAddFeeding}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90"
            >
              Record Feeding
            </button>
          </div>
        </div>

        <div className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4">Feeding History</h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {feedingEntries.map((entry) => (
              <div key={entry.id} className="p-3 border border-border rounded-lg bg-secondary/20">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-sm">{entry.type}</span>
                  <span className="text-xs text-muted-foreground">{entry.time}</span>
                </div>
                <div className="text-sm">
                  <span className="text-primary font-semibold">{entry.amount}</span>
                  <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                    entry.tolerance === "Good" ? "bg-green-100 text-green-700" :
                    entry.tolerance === "Fair" ? "bg-yellow-100 text-yellow-700" :
                    "bg-red-100 text-red-700"
                  }`}>
                    {entry.tolerance}
                  </span>
                </div>
                {entry.notes && <p className="text-xs text-muted-foreground mt-1">{entry.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Output Section */}
      <div className="space-y-4">
        <div className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4">Record Output</h3>
          <div className="space-y-3">
            <div>
              <label className="text-sm text-muted-foreground">Type</label>
              <select
                value={newOutput.type}
                onChange={(e) => setNewOutput({ ...newOutput, type: e.target.value as "Urine" | "Stool" })}
                className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
              >
                <option>Urine</option>
                <option>Stool</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Description</label>
              <input
                type="text"
                value={newOutput.description}
                onChange={(e) => setNewOutput({ ...newOutput, description: e.target.value })}
                placeholder="e.g., Normal output, clear yellow"
                className="w-full mt-1 p-2 border border-border rounded-lg bg-input text-foreground"
              />
            </div>
            <button
              onClick={handleAddOutput}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90"
            >
              Record Output
            </button>
          </div>
        </div>

        <div className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4">Output History</h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {outputEntries.map((entry) => (
              <div key={entry.id} className="p-3 border border-border rounded-lg bg-secondary/20">
                <div className="flex justify-between items-start mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    entry.type === "Urine" ? "bg-blue-100 text-blue-700" : "bg-amber-100 text-amber-700"
                  }`}>
                    {entry.type}
                  </span>
                  <span className="text-xs text-muted-foreground">{entry.time}</span>
                </div>
                <p className="text-sm text-foreground">{entry.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
