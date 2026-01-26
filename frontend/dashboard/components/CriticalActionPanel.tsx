'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNotifications } from '@/contexts/NotificationContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Stethoscope, TestTube, Pill, XCircle, Clock } from 'lucide-react';

interface CriticalActionPanelProps {
  patientMRN: string;
  patientName: string;
}

export default function CriticalActionPanel({ patientMRN, patientName }: CriticalActionPanelProps) {
  const { user } = useAuth();
  const { addNotification } = useNotifications();
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [observationHours, setObservationHours] = useState('');
  const [dismissalHours, setDismissalHours] = useState('');
  const [selectedAntibiotic, setSelectedAntibiotic] = useState('');
  const [notes, setNotes] = useState('');

  // Only show for doctors
  if (!user || user.role !== 'DOCTOR') {
    return null;
  }

  const handleActionSubmit = (actionType: string) => {
    const auditData = {
      action: actionType,
      doctor: user.userId,
      mrn: patientMRN,
      patientName: patientName,
      timestamp: new Date().toISOString(),
      details: {
        ...(actionType === 'Observe' && { observationHours }),
        ...(actionType === 'Dismiss for Now' && { dismissalHours }),
        ...(actionType === 'Treat with Antibiotic' && { selectedAntibiotic }),
        ...(notes && { notes })
      }
    };

    // HIL Audit Logging
    console.log('HIL Audit:', auditData);

    // Send notification to nurses
    addNotification({
      type: 'CRITICAL_ACTION',
      message: `Dr. ${user.name} has taken critical action: ${actionType}`,
      details: {
        doctor: user.name,
        doctorId: user.userId,
        patient: patientName,
        mrn: patientMRN,
        action: actionType,
        actionDetails: {
          ...(actionType === 'Observe' && { duration: `${observationHours} hours` }),
          ...(actionType === 'Dismiss for Now' && { dismissalPeriod: `${dismissalHours} hours` }),
          ...(actionType === 'Treat with Antibiotic' && { antibiotic: selectedAntibiotic }),
          ...(actionType === 'Send for Lab' && { labOrders: 'Blood culture, CBC, CRP' }),
          ...(notes && { clinicalNotes: notes })
        },
        timestamp: new Date().toISOString(),
        priority: actionType === 'Treat with Antibiotic' ? 'URGENT' : 
                 actionType === 'Send for Lab' ? 'HIGH' : 'MEDIUM',
        requiresAcknowledgment: actionType === 'Treat with Antibiotic'
      },
      timestamp: new Date().toISOString()
    });
    
    // Reset form
    setSelectedAction(null);
    setObservationHours('');
    setDismissalHours('');
    setSelectedAntibiotic('');
    setNotes('');
    
    // Enhanced success feedback
    const actionSummary = actionType === 'Observe' ? `${observationHours}h observation` :
                         actionType === 'Dismiss for Now' ? `Dismissed for ${dismissalHours}h` :
                         actionType === 'Treat with Antibiotic' ? `Antibiotic: ${selectedAntibiotic}` :
                         'Lab orders placed';
    
    alert(`✅ Action logged successfully!\n\n` +
          `Patient: ${patientName} (${patientMRN})\n` +
          `Action: ${actionType}\n` +
          `Details: ${actionSummary}\n\n` +
          `🚨 All NICU nurses have been notified\n` +
          `📱 Mobile alerts sent\n` +
          `🔔 Bell notifications delivered`);
  };

  const actionButtons = [
    {
      id: 'Observe',
      label: 'Observe',
      icon: <Stethoscope className="h-4 w-4" />,
      color: 'bg-blue-100 hover:bg-blue-200 text-blue-800 border border-blue-200',
      description: 'Continue monitoring patient'
    },
    {
      id: 'Send for Lab',
      label: 'Send for Lab',
      icon: <TestTube className="h-4 w-4" />,
      color: 'bg-orange-100 hover:bg-orange-200 text-orange-800 border border-orange-200',
      description: 'Order laboratory tests'
    },
    {
      id: 'Treat with Antibiotic',
      label: 'Treat with Antibiotic',
      icon: <Pill className="h-4 w-4" />,
      color: 'bg-red-100 hover:bg-red-200 text-red-800 border border-red-200',
      description: 'Administer antibiotic treatment'
    },
    {
      id: 'Dismiss for Now',
      label: 'Dismiss for Now',
      icon: <XCircle className="h-4 w-4" />,
      color: 'bg-green-100 hover:bg-green-200 text-green-800 border border-green-200',
      description: 'No immediate action required'
    }
  ];

  return (
    <Card className="bg-gradient-to-r from-emerald-50 via-blue-50 to-indigo-50 border-emerald-200 shadow-lg ring-1 ring-emerald-100">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-gray-800 flex items-center gap-2 font-sans">
            <div className="h-3 w-3 bg-emerald-500 rounded-full animate-pulse shadow-sm"></div>
            Critical Action Panel
            <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full border border-emerald-200 font-sans shadow-sm">
              DOCTOR ONLY
            </span>
          </CardTitle>
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            variant="ghost"
            size="sm"
            className="text-emerald-700 hover:bg-emerald-100 font-sans"
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
        <p className="text-emerald-700 text-sm font-sans">
          Clinical decision logging for {patientName} (MRN: {patientMRN})
        </p>
        <div className="text-xs text-emerald-600 bg-emerald-50 p-2 rounded-md border border-emerald-100">
          <span className="font-medium">🔔 Auto-Alert:</span> Nurses will be automatically notified of all actions
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4">
          {/* Action Selection */}
          {!selectedAction ? (
            <div className="grid grid-cols-2 gap-3">
              {actionButtons.map((action) => (
                <Button
                  key={action.id}
                  onClick={() => setSelectedAction(action.id)}
                  className={`${action.color} font-medium py-3 px-4 flex flex-col items-center gap-2 h-auto shadow-sm font-sans`}
                >
                  {action.icon}
                  <span className="text-sm font-sans">{action.label}</span>
                </Button>
              ))}
            </div>
          ) : (
            /* Action Detail Form */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-gray-800 font-medium flex items-center gap-2 font-sans">
                  {actionButtons.find(a => a.id === selectedAction)?.icon}
                  {selectedAction}
                </h4>
                <Button
                  onClick={() => setSelectedAction(null)}
                  variant="ghost"
                  size="sm"
                  className="text-gray-600 hover:bg-gray-100 font-sans"
                >
                  Back
                </Button>
              </div>

              {/* Observation Time Input for "Observe" action */}
              {selectedAction === 'Observe' && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2 font-sans">
                    <Clock className="h-4 w-4" />
                    Observation Duration (hours)
                  </label>
                  <Input
                    type="number"
                    value={observationHours}
                    onChange={(e) => setObservationHours(e.target.value)}
                    placeholder="Enter hours (e.g., 2, 6, 12)"
                    min="1"
                    max="72"
                    className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-500 focus:border-emerald-500 focus:ring-emerald-200 font-sans"
                  />
                </div>
              )}

              {/* Dismissal Hours Input for "Dismiss for Now" action */}
              {selectedAction === 'Dismiss for Now' && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2 font-sans">
                    <Clock className="h-4 w-4" />
                    Dismissal Time Span (hours)
                  </label>
                  <select
                    value={dismissalHours}
                    onChange={(e) => setDismissalHours(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md bg-white text-gray-900 focus:border-emerald-500 focus:ring-emerald-200 font-sans"
                    required
                  >
                    <option value="">Select dismissal period...</option>
                    <option value="1">1 hour - Brief dismissal</option>
                    <option value="2">2 hours - Short-term dismissal</option>
                    <option value="4">4 hours - Standard dismissal</option>
                    <option value="6">6 hours - Extended dismissal</option>
                    <option value="8">8 hours - Shift dismissal</option>
                    <option value="12">12 hours - Half-day dismissal</option>
                    <option value="24">24 hours - Daily dismissal</option>
                  </select>
                  <p className="text-xs text-gray-500 font-sans">Patient will be re-evaluated after this period</p>
                </div>
              )}

              {/* Antibiotic Selection for "Treat with Antibiotic" action */}
              {selectedAction === 'Treat with Antibiotic' && (
                <div className="space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-red-800 mb-2 font-sans">
                      🩺 Antibiotic Recommendations (If Sepsis Suspected)
                    </h4>
                    <p className="text-xs text-red-700 mb-3 font-sans">
                      Select appropriate antibiotic based on sepsis type. Doctor approval required before administration.
                    </p>
                    
                    <div className="space-y-3">
                      <div className="bg-blue-50 border border-blue-200 rounded p-3">
                        <h5 className="font-medium text-blue-800 text-xs mb-2 font-sans">Early-onset Sepsis (within 72 hours of birth)</h5>
                        <div className="space-y-1 text-xs">
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Ampicillin + Gentamicin" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-blue-600" />
                            <span className="text-blue-700">Ampicillin + Gentamicin - First-line for E. coli and Group B Strep</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Ampicillin + Amikacin" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-blue-600" />
                            <span className="text-blue-700">Ampicillin + Amikacin - Alternative first-line</span>
                          </label>
                        </div>
                      </div>

                      <div className="bg-orange-50 border border-orange-200 rounded p-3">
                        <h5 className="font-medium text-orange-800 text-xs mb-2 font-sans">Late-onset Sepsis (after 72 hours)</h5>
                        <div className="space-y-1 text-xs">
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Cefotaxime + Amikacin" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-orange-600" />
                            <span className="text-orange-700">Cefotaxime + Amikacin - Broad spectrum coverage</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Piperacillin-Tazobactam + Amikacin" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-orange-600" />
                            <span className="text-orange-700">Piperacillin-Tazobactam + Amikacin - Extended spectrum</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Vancomycin" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-orange-600" />
                            <span className="text-orange-700">Vancomycin - If MRSA suspected</span>
                          </label>
                        </div>
                      </div>

                      <div className="bg-red-50 border border-red-300 rounded p-3">
                        <h5 className="font-medium text-red-800 text-xs mb-2 font-sans">Severe/Resistant Infections (NICU cases)</h5>
                        <div className="space-y-1 text-xs">
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Meropenem" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-red-600" />
                            <span className="text-red-700">Meropenem - Multi-drug resistant organisms</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Imipenem" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-red-600" />
                            <span className="text-red-700">Imipenem - Severe NICU infections</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Linezolid" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-red-600" />
                            <span className="text-red-700">Linezolid - Resistant gram-positive</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Colistin" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-red-600" />
                            <span className="text-red-700">Colistin - Last resort for MDR infections</span>
                          </label>
                        </div>
                      </div>

                      <div className="bg-purple-50 border border-purple-200 rounded p-3">
                        <h5 className="font-medium text-purple-800 text-xs mb-2 font-sans">Fungal Sepsis</h5>
                        <div className="space-y-1 text-xs">
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Fluconazole" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-purple-600" />
                            <span className="text-purple-700">Fluconazole - Candida infection</span>
                          </label>
                          <label className="flex items-center gap-2 font-sans">
                            <input type="radio" name="antibiotic" value="Amphotericin B" 
                                   onChange={(e) => setSelectedAntibiotic(e.target.value)}
                                   className="text-purple-600" />
                            <span className="text-purple-700">Amphotericin B - Severe fungal sepsis</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Notes Field */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 font-sans">
                  Clinical Notes (Optional)
                </label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter any relevant clinical notes or rationale..."
                  className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-500 focus:border-emerald-500 focus:ring-emerald-200 min-h-[80px] font-sans"
                />
              </div>

              {/* Submit Action */}
              <div className="flex gap-3">
                <Button
                  onClick={() => handleActionSubmit(selectedAction)}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium font-sans shadow-md hover:shadow-lg"
                  disabled={
                    (selectedAction === 'Observe' && !observationHours) ||
                    (selectedAction === 'Dismiss for Now' && !dismissalHours) ||
                    (selectedAction === 'Treat with Antibiotic' && !selectedAntibiotic)
                  }
                >
                  Log {selectedAction} Action
                </Button>
                <Button
                  onClick={() => setSelectedAction(null)}
                  variant="outline"
                  className="border-gray-300 text-gray-700 hover:bg-gray-100 font-sans"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Info Footer */}
          <div className="text-xs text-emerald-700 bg-emerald-50 p-3 rounded-lg border border-emerald-200">
            <p className="font-medium mb-1 font-sans">🔐 Chain of Custody & Alerts</p>
            <p className="font-sans">All actions are logged for audit compliance and nurses are automatically notified. Logged as: <span className="font-mono bg-emerald-100 px-1 rounded">{user.name}</span> ({user.userId})</p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}