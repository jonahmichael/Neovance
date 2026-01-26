"use client";

import { useState } from "react";

interface DischargeChecklist {
  id: number;
  item: string;
  completed: boolean;
  completedBy?: string;
  completedDate?: string;
  category: string;
}

export default function DischargePlanning() {
  const [checklist, setChecklist] = useState<DischargeChecklist[]>([
    // Medical Criteria
    { id: 1, item: "Stable vital signs for 24 hours", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-26", category: "Medical" },
    { id: 2, item: "Maintaining temperature in open crib", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-26", category: "Medical" },
    { id: 3, item: "Feeding well (breast/bottle)", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-26", category: "Medical" },
    { id: 4, item: "No oxygen requirement", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-26", category: "Medical" },
    { id: 5, item: "Weight gain or stable weight", completed: false, category: "Medical" },
    { id: 6, item: "Bilirubin within safe limits", completed: true, completedBy: "Dr. Rajesh Kumar", completedDate: "2026-01-26", category: "Medical" },
    
    // Screenings Complete
    { id: 7, item: "Hearing screening completed", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-25", category: "Screening" },
    { id: 8, item: "Metabolic screening completed", completed: true, completedBy: "Lab", completedDate: "2026-01-25", category: "Screening" },
    { id: 9, item: "CCHD screening completed", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-25", category: "Screening" },
    
    // Parent Education
    { id: 10, item: "Breastfeeding education provided", completed: true, completedBy: "Anjali Patel", completedDate: "2026-01-26", category: "Education" },
    { id: 11, item: "Safe sleep counseling", completed: false, category: "Education" },
    { id: 12, item: "Warning signs explained to parents", completed: false, category: "Education" },
    { id: 13, item: "Car seat safety discussed", completed: false, category: "Education" },
    { id: 14, item: "Immunization schedule explained", completed: true, completedBy: "Dr. Rajesh Kumar", completedDate: "2026-01-26", category: "Education" },
    
    // Documentation
    { id: 15, item: "Birth certificate documentation complete", completed: true, completedBy: "Admin", completedDate: "2026-01-21", category: "Documentation" },
    { id: 16, item: "Discharge summary prepared", completed: false, category: "Documentation" },
    { id: 17, item: "Follow-up appointments scheduled", completed: false, category: "Documentation" },
  ]);

  const [doctorNotes, setDoctorNotes] = useState("");
  const [nurseNotes, setNurseNotes] = useState("");

  const toggleItem = (id: number) => {
    setChecklist(checklist.map(item => {
      if (item.id === id) {
        return {
          ...item,
          completed: !item.completed,
          completedBy: !item.completed ? "Anjali Patel" : undefined,
          completedDate: !item.completed ? new Date().toISOString().split("T")[0] : undefined,
        };
      }
      return item;
    }));
  };

  const categories = ["Medical", "Screening", "Education", "Documentation"];
  
  const completedCount = checklist.filter(item => item.completed).length;
  const totalCount = checklist.length;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-primary mb-4">Discharge Readiness</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          <span className="text-lg font-bold text-foreground">{progressPercent}%</span>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          {completedCount} of {totalCount} criteria completed
        </p>
      </div>

      {/* Checklist by Category */}
      {categories.map((category) => {
        const categoryItems = checklist.filter(item => item.category === category);
        const categoryCompleted = categoryItems.filter(item => item.completed).length;
        
        return (
          <div key={category} className="bg-card rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-primary">{category} Criteria</h3>
              <span className="text-sm text-muted-foreground">
                {categoryCompleted}/{categoryItems.length}
              </span>
            </div>
            <div className="space-y-2">
              {categoryItems.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-colors ${
                    item.completed 
                      ? "bg-green-50 border-green-200" 
                      : "bg-secondary/20 border-border hover:bg-secondary/40"
                  }`}
                  onClick={() => toggleItem(item.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      item.completed 
                        ? "bg-green-500 border-green-500" 
                        : "border-gray-300"
                    }`}>
                      {item.completed && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    <span className={`text-sm ${item.completed ? "text-green-700" : "text-foreground"}`}>
                      {item.item}
                    </span>
                  </div>
                  {item.completed && item.completedBy && (
                    <span className="text-xs text-muted-foreground">
                      {item.completedBy} - {item.completedDate}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* Doctor and Nurse Notes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4">Doctor Discharge Notes</h3>
          <textarea
            value={doctorNotes}
            onChange={(e) => setDoctorNotes(e.target.value)}
            placeholder="Enter discharge recommendations, follow-up care instructions..."
            className="w-full p-3 border border-border rounded-lg bg-input text-foreground resize-none h-32 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <p className="text-xs text-muted-foreground mt-2">Dr. Rajesh Kumar</p>
        </div>
        
        <div className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4">Nurse Discharge Notes</h3>
          <textarea
            value={nurseNotes}
            onChange={(e) => setNurseNotes(e.target.value)}
            placeholder="Enter care instructions, feeding schedule, warning signs discussed..."
            className="w-full p-3 border border-border rounded-lg bg-input text-foreground resize-none h-32 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <p className="text-xs text-muted-foreground mt-2">Anjali Patel, RN</p>
        </div>
      </div>

      {/* Discharge Button */}
      <div className="bg-card rounded-xl p-5 shadow-sm">
        <button
          disabled={progressPercent < 100}
          className={`w-full py-3 rounded-lg font-semibold text-lg transition-colors ${
            progressPercent === 100
              ? "bg-green-500 text-white hover:bg-green-600"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {progressPercent === 100 ? "Ready for Discharge" : `Complete ${totalCount - completedCount} more items to discharge`}
        </button>
      </div>
    </div>
  );
}
