"use client";

import { useState } from "react";

interface ClinicalNote {
  id: number;
  date: string;
  time: string;
  author: string;
  role: string;
  note: string;
  category: string;
}

export default function ClinicalNotes() {
  const [newNote, setNewNote] = useState("");
  const [notes, setNotes] = useState<ClinicalNote[]>([
    {
      id: 1,
      date: "2026-01-26",
      time: "08:30 AM",
      author: "Dr. Rajesh Kumar",
      role: "Doctor",
      note: "Baby is responding well to phototherapy. Bilirubin levels showing improvement. Continue monitoring every 6 hours.",
      category: "Progress Note",
    },
    {
      id: 2,
      date: "2026-01-26",
      time: "06:00 AM",
      author: "Anjali Patel",
      role: "Nurse",
      note: "Vital signs stable. Baby fed 30ml expressed breast milk. Good suck reflex observed. Urine output normal.",
      category: "Nursing Note",
    },
    {
      id: 3,
      date: "2026-01-25",
      time: "10:00 PM",
      author: "Anjali Patel",
      role: "Nurse",
      note: "Administered Vitamin K injection as per protocol. No adverse reactions observed. Parents counseled about newborn care.",
      category: "Medication Note",
    },
  ]);

  const handleAddNote = () => {
    if (!newNote.trim()) return;
    
    const now = new Date();
    const newEntry: ClinicalNote = {
      id: notes.length + 1,
      date: now.toISOString().split("T")[0],
      time: now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      author: "Anjali Patel",
      role: "Nurse",
      note: newNote,
      category: "Nursing Note",
    };
    
    setNotes([newEntry, ...notes]);
    setNewNote("");
  };

  return (
    <div className="space-y-6">
      {/* Add New Note */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Add Clinical Note</h3>
        <div className="space-y-3">
          <textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Enter clinical observation or note..."
            className="w-full p-3 border border-border rounded-lg bg-input text-foreground resize-none h-24 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            onClick={handleAddNote}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            Add Note
          </button>
        </div>
      </div>

      {/* Notes Timeline */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Clinical Notes History</h3>
        <div className="space-y-4">
          {notes.map((note) => (
            <div
              key={note.id}
              className="border-l-4 border-primary/50 pl-4 py-2 bg-secondary/30 rounded-r-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 bg-primary/20 text-primary rounded-full font-medium">
                    {note.category}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {note.author} ({note.role})
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {note.date} at {note.time}
                </span>
              </div>
              <p className="text-sm text-foreground">{note.note}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
