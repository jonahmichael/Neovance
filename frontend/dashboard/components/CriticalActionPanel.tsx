'use client';

import { useState } from "react";
import { AlertTriangle, Clock, Eye, TestTube, Pill, X, FileText, ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useNotifications } from "@/contexts/NotificationContext";
import { useAuth } from "@/contexts/AuthContext";

export default function CriticalActionPanel() {
  const { activeSepsisAlert, setActiveSepsisAlert, addNotification } = useNotifications();
  const { user } = useAuth();
  const [selectedAction, setSelectedAction] = useState<string>("");
  const [selectedLabs, setSelectedLabs] = useState<string[]>([]);
  const [selectedAntibiotics, setSelectedAntibiotics] = useState<string[]>([]);
  const [observationHours, setObservationHours] = useState<string>("2");
  const [customInstructions, setCustomInstructions] = useState<string>("");
  const [dismissReason, setDismissReason] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Show only if there's an active sepsis alert and user is doctor
  if (!activeSepsisAlert || activeSepsisAlert.alert_status !== "PENDING_DOCTOR_ACTION" || user?.role !== 'DOCTOR') {
    return null;
  }

  const actionTypes = [
    { id: "OBSERVE", label: "Observe Patient", icon: <Eye className="h-4 w-4" />, color: "bg-blue-400", description: "Monitor vitals for specified duration" },
    { id: "LAB_TESTS", label: "Send for Lab Tests", icon: <TestTube className="h-4 w-4" />, color: "bg-amber-400", description: "Order laboratory investigations" },
    { id: "ANTIBIOTICS", label: "Treat with Antibiotics", icon: <Pill className="h-4 w-4" />, color: "bg-emerald-400", description: "Start antibiotic therapy" },
    { id: "DISMISS", label: "Dismiss Alert", icon: <X className="h-4 w-4" />, color: "bg-slate-400", description: "Dismiss with specified reason" },
    { id: "CUSTOM", label: "Custom Instructions", icon: <FileText className="h-4 w-4" />, color: "bg-violet-400", description: "Set custom monitoring protocol" }
  ];

  const availableLabs = [
    "Complete Blood Count (CBC)",
    "C-Reactive Protein (CRP)", 
    "Blood Culture",
    "Lactate Level",
    "Procalcitonin",
    "Cerebrospinal Fluid Analysis",
    "Arterial Blood Gas (ABG)",
    "Urine Culture",
    "Chest X-Ray"
  ];

  const availableAntibiotics = [
    "Ampicillin",
    "Gentamicin", 
    "Cefotaxime",
    "Vancomycin",
    "Amikacin",
    "Meropenem",
    "Flucloxacillin",
    "Clindamycin"
  ];

  const handleActionSelect = (actionId: string) => {
    setSelectedAction(actionId);
    // Reset form data when switching actions
    setSelectedLabs([]);
    setSelectedAntibiotics([]);
    setObservationHours("2");
    setCustomInstructions("");
    setDismissReason("");
  };

  const handleLabToggle = (lab: string) => {
    setSelectedLabs(prev => 
      prev.includes(lab) 
        ? prev.filter(l => l !== lab)
        : [...prev, lab]
    );
  };

  const handleAntibioticToggle = (antibiotic: string) => {
    setSelectedAntibiotics(prev => 
      prev.includes(antibiotic) 
        ? prev.filter(a => a !== antibiotic)
        : [...prev, antibiotic]
    );
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);

    let actionDetails = "";
    const selectedActionInfo = actionTypes.find(a => a.id === selectedAction);
    const actionLabel = selectedActionInfo?.label || selectedAction;

    // Build detailed action description
    switch (selectedAction) {
      case "OBSERVE":
        actionDetails = `Monitor patient for ${observationHours} hours. Risk Score: ${(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%`;
        break;
      case "LAB_TESTS":
        actionDetails = `Ordered Labs: ${selectedLabs.join(", ")}. Risk Score: ${(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%`;
        break;
      case "ANTIBIOTICS":
        actionDetails = `Prescribed Antibiotics: ${selectedAntibiotics.join(", ")}. Risk Score: ${(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%`;
        break;
      case "DISMISS":
        actionDetails = `Alert dismissed. Reason: ${dismissReason}. Risk Score: ${(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%`;
        break;
      case "CUSTOM":
        actionDetails = `Custom Instructions: ${customInstructions}. Risk Score: ${(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%`;
        break;
      default:
        actionDetails = `Risk Score: ${(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%`;
    }

    console.log('Sending notification to nurse:', {
      actionLabel,
      actionDetails,
      selectedLabs,
      selectedAntibiotics,
      observationHours,
      dismissReason,
      customInstructions
    });

    // Notify the nurse with detailed information
    addNotification({
      type: 'CRITICAL_ACTION',
      message: `Dr. ${user?.displayName || 'Doctor'} decided: ${actionLabel}`,
      details: {
        doctor: user?.displayName || 'Dr. Unknown',
        doctorId: user?.userId || '',
        patient: 'Baby B001',
        mrn: 'B001',
        action: actionLabel,
        actionDetails: actionDetails,
        timestamp: new Date().toISOString(),
        priority: 'URGENT' as const,
        requiresAcknowledgment: true,
        alertId: activeSepsisAlert.alert_id,
        riskScore: activeSepsisAlert.model_risk_score,
        // Include specific details
        ...(selectedAction === "OBSERVE" && { observationDuration: `${observationHours} hours` }),
        ...(selectedAction === "LAB_TESTS" && { labTests: selectedLabs }),
        ...(selectedAction === "ANTIBIOTICS" && { antibiotics: selectedAntibiotics })
      },
      timestamp: new Date().toISOString()
    });

    console.log('Notification sent successfully');

    // Close the panel after notifying - doctor's job is done
    setTimeout(() => {
      setActiveSepsisAlert(null);
      setIsSubmitting(false);
    }, 1500);
  };

  return (
    <div className="fixed inset-0 bg-white/20 backdrop-blur-md flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-3xl bg-white/95 backdrop-blur-sm shadow-2xl border-0">
        <CardHeader className="bg-rose-50/80 backdrop-blur-sm border-b border-rose-200/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-rose-500" />
              <div>
                <CardTitle className="text-rose-700">Sepsis Alert - Doctor Action Required</CardTitle>
                <div className="flex items-center gap-4 text-sm text-rose-600 mt-1">
                  <span>Baby ID: {activeSepsisAlert.baby_id}</span>
                  <span>Risk Score: {(activeSepsisAlert.model_risk_score * 100).toFixed(1)}%</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {new Date(activeSepsisAlert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setActiveSepsisAlert(null)}
              className="text-rose-500 hover:text-rose-700 p-1"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <div className="space-y-6">
            {!selectedAction ? (
              <>
                <h3 className="text-lg font-semibold text-gray-900 text-center">Select Action</h3>
                
                <div className="grid grid-cols-2 gap-3">
                  {actionTypes.map((action) => (
                    <Card 
                      key={action.id} 
                      className="cursor-pointer transition-all duration-200 hover:shadow-md bg-white/90 backdrop-blur-sm hover:bg-gray-50/90"
                      onClick={() => handleActionSelect(action.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${action.color} text-white`}>
                            {action.icon}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-800">{action.label}</h3>
                            <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                
                <div className="text-center text-sm text-gray-600">
                  Click any action to specify details and notify the nurse
                </div>
              </>
            ) : (
              <>
                {/* Action Detail Form */}
                <div className="flex items-center gap-3 mb-4">
                  <button
                    onClick={() => setSelectedAction("")}
                    className="p-1 text-gray-500 hover:text-gray-700"
                  >
                    <ArrowLeft className="h-5 w-5" />
                  </button>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {actionTypes.find(a => a.id === selectedAction)?.label}
                  </h3>
                </div>

                {/* Observe Patient Form */}
                {selectedAction === "OBSERVE" && (
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Observation Duration</Label>
                      <select
                        value={observationHours}
                        onChange={(e) => setObservationHours(e.target.value)}
                        className="w-full mt-1 p-2 border border-gray-300 rounded-md"
                      >
                        <option value="1">1 hour</option>
                        <option value="2">2 hours</option>
                        <option value="4">4 hours</option>
                        <option value="6">6 hours</option>
                        <option value="12">12 hours</option>
                        <option value="24">24 hours</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Lab Tests Form */}
                {selectedAction === "LAB_TESTS" && (
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-700 mb-3 block">Select Lab Tests</Label>
                      <div className="grid grid-cols-1 gap-3 max-h-48 overflow-y-auto border rounded-md p-3">
                        {availableLabs.map((lab) => (
                          <div key={lab} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                            <input
                              type="checkbox"
                              id={lab}
                              checked={selectedLabs.includes(lab)}
                              onChange={() => handleLabToggle(lab)}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <Label htmlFor={lab} className="text-sm text-gray-700 cursor-pointer">{lab}</Label>
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        Selected: {selectedLabs.length} test(s)
                      </div>
                    </div>
                  </div>
                )}

                {/* Antibiotics Form */}
                {selectedAction === "ANTIBIOTICS" && (
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-700 mb-3 block">Select Antibiotics</Label>
                      <div className="grid grid-cols-2 gap-3 border rounded-md p-3">
                        {availableAntibiotics.map((antibiotic) => (
                          <div key={antibiotic} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                            <input
                              type="checkbox"
                              id={antibiotic}
                              checked={selectedAntibiotics.includes(antibiotic)}
                              onChange={() => handleAntibioticToggle(antibiotic)}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <Label htmlFor={antibiotic} className="text-sm text-gray-700 cursor-pointer">{antibiotic}</Label>
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        Selected: {selectedAntibiotics.length} antibiotic(s)
                      </div>
                    </div>
                  </div>
                )}

                {/* Dismiss Alert Form */}
                {selectedAction === "DISMISS" && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="dismissReason" className="text-sm font-medium text-gray-700">Reason for Dismissal</Label>
                      <textarea
                        id="dismissReason"
                        value={dismissReason}
                        onChange={(e) => setDismissReason(e.target.value)}
                        placeholder="Enter reason for dismissing this sepsis alert..."
                        className="w-full mt-1 p-3 border border-gray-300 rounded-md h-24 resize-none"
                      />
                    </div>
                  </div>
                )}

                {/* Custom Instructions Form */}
                {selectedAction === "CUSTOM" && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="customInstructions" className="text-sm font-medium text-gray-700">Custom Instructions</Label>
                      <textarea
                        id="customInstructions"
                        value={customInstructions}
                        onChange={(e) => setCustomInstructions(e.target.value)}
                        placeholder="Enter specific monitoring protocol or custom instructions..."
                        className="w-full mt-1 p-3 border border-gray-300 rounded-md h-32 resize-none"
                      />
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setSelectedAction("")}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || (selectedAction === "LAB_TESTS" && selectedLabs.length === 0) || 
                             (selectedAction === "ANTIBIOTICS" && selectedAntibiotics.length === 0) ||
                             (selectedAction === "DISMISS" && !dismissReason.trim()) ||
                             (selectedAction === "CUSTOM" && !customInstructions.trim())}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSubmitting ? "Sending..." : "Send to Nurse"}
                  </button>
                </div>
              </>
            )}

            {isSubmitting && (
              <div className="text-center py-4">
                <div className="text-emerald-600 font-medium flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-600"></div>
                  Sending decision to nurse...
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
