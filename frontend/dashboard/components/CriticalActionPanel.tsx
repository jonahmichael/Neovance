'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { AlertCircle, Stethoscope, TestTube, Eye, XCircle, CheckCircle2, FlaskConical, Pill } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';

interface Alert {
  alert_id: number;
  baby_id: string;
  timestamp: string;
  model_risk_score: number;
  alert_status: string;
}

interface CriticalActionPanelProps {
  alert: Alert | null;
  doctorId: string;
  onActionTaken: () => void;
  onCancel?: () => void;
}

const PREDEFINED_LABS = [
  "Complete Blood Count (CBC)",
  "C-Reactive Protein (CRP)",
  "Blood Culture",
  "Lactate Level",
  "Procalcitonin",
  "Cerebrospinal Fluid (CSF) Analysis"
];

const PREDEFINED_ANTIBIOTICS = [
  "Ampicillin",
  "Gentamicin",
  "Cefotaxime",
  "Vancomycin",
  "Amikacin"
];

export default function CriticalActionPanel({ alert, doctorId, onActionTaken, onCancel }: CriticalActionPanelProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [actionDetail, setActionDetail] = useState('');
  const [observationDuration, setObservationDuration] = useState('6');
  const [dismissDuration, setDismissDuration] = useState('4');
  const [selectedLabs, setSelectedLabs] = useState<string[]>(PREDEFINED_LABS);
  const [selectedAntibiotics, setSelectedAntibiotics] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!alert || alert.alert_status !== 'PENDING_DOCTOR_ACTION') {
    return null;
  }

  const handleSubmit = async () => {
    if (!selectedAction) {
      window.alert('Please select an action');
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        alert_id: alert.alert_id,
        doctor_id: doctorId,
        action_type: selectedAction,
        action_detail: actionDetail,
        observation_duration: selectedAction === 'OBSERVATION' ? `${observationDuration} hours` : null,
        lab_tests: selectedAction === 'LAB_TESTS' ? selectedLabs : null,
        antibiotics: selectedAction === 'ANTIBIOTICS' ? selectedAntibiotics : null,
        dismiss_duration: selectedAction === 'DISMISS' ? parseInt(dismissDuration) : null,
      };

      const response = await fetch('http://localhost:8000/api/v1/log_doctor_action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        onActionTaken();
      }
    } catch (error) {
      console.error('Error logging action:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const actions = [
    {
      type: 'OBSERVATION',
      label: 'Observation',
      icon: Eye,
      color: 'border-blue-500 text-blue-700 bg-blue-50',
      description: 'Monitor closely for a specified period',
    },
    {
      type: 'LAB_TESTS',
      label: 'Lab Tests',
      icon: FlaskConical,
      color: 'border-amber-500 text-amber-700 bg-amber-50',
      description: 'Order specific laboratory diagnostics',
    },
    {
      type: 'ANTIBIOTICS',
      label: 'Antibiotics',
      icon: Pill,
      color: 'border-green-500 text-green-700 bg-green-50',
      description: 'Start medication treatment immediately',
    },
    {
      type: 'DISMISS',
      label: 'Dismiss',
      icon: XCircle,
      color: 'border-slate-500 text-slate-700 bg-slate-50',
      description: 'Dismiss alert for a specific duration',
    },
  ];

  return (
    <Card className="w-full border-2 border-red-500 shadow-xl overflow-hidden max-w-2xl mx-auto">
      <CardHeader className="bg-red-50 py-3 border-b border-red-100">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold text-red-700 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Sepsis Intervention Decision: Baby ID {alert.baby_id}
          </CardTitle>
          {onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel} className="h-8 w-8 p-0">
              <XCircle className="h-5 w-5 text-gray-400" />
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="p-6 space-y-6">
        {/* Step 1: Select Action */}
        <div className="grid grid-cols-2 gap-3">
          {actions.map((item) => {
            const Icon = item.icon;
            const isSelected = selectedAction === item.type;
            return (
              <button
                key={item.type}
                onClick={() => setSelectedAction(item.type)}
                className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all ${
                  isSelected 
                  ? `${item.color} ring-2 ring-offset-2 ring-opacity-50 ring-current`
                  : 'border-gray-100 hover:border-gray-200 bg-white'
                }`}
              >
                <Icon className={`h-8 w-8 mb-2 ${isSelected ? 'text-current' : 'text-gray-400'}`} />
                <span className="font-bold text-sm uppercase">{item.label}</span>
                <span className="text-[10px] text-gray-500 mt-1 text-center leading-tight">
                  {item.description}
                </span>
              </button>
            );
          })}
        </div>

        {/* Step 2: Configure Details */}
        {selectedAction && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 animate-in fade-in slide-in-from-top-2">
            {selectedAction === 'OBSERVATION' && (
              <div className="space-y-3">
                <label className="text-sm font-semibold flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-600" /> Observation Period (Hours)
                </label>
                <div className="flex gap-2">
                  {['3', '6', '12', '24'].map(h => (
                    <Button 
                      key={h}
                      variant={observationDuration === h ? "default" : "outline"}
                      size="sm"
                      onClick={() => setObservationDuration(h)}
                      className="flex-1"
                    >
                      {h}h
                    </Button>
                  ))}
                  <Input 
                    type="number" 
                    placeholder="Custom" 
                    className="w-20 h-9"
                    value={observationDuration}
                    onChange={(e) => setObservationDuration(e.target.value)}
                  />
                </div>
              </div>
            )}

            {selectedAction === 'LAB_TESTS' && (
              <div className="space-y-3">
                <label className="text-sm font-semibold flex items-center gap-2 text-amber-700">
                  <FlaskConical className="h-4 w-4" /> Select Laboratory Tests
                </label>
                <div className="grid grid-cols-2 gap-2 bg-white p-3 rounded-lg border border-slate-100">
                  {PREDEFINED_LABS.map(lab => (
                    <div key={lab} className="flex items-center space-x-2">
                      <Checkbox 
                        id={lab} 
                        checked={selectedLabs.includes(lab)}
                        onCheckedChange={(checked) => {
                          if (checked) setSelectedLabs([...selectedLabs, lab]);
                          else setSelectedLabs(selectedLabs.filter(l => l !== lab));
                        }}
                      />
                      <label htmlFor={lab} className="text-xs font-medium leading-none cursor-pointer">
                        {lab}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedAction === 'ANTIBIOTICS' && (
              <div className="space-y-3">
                <label className="text-sm font-semibold flex items-center gap-2 text-green-700">
                  <Pill className="h-4 w-4" /> Prescribe Antibiotics
                </label>
                <div className="flex flex-wrap gap-2">
                  {PREDEFINED_ANTIBIOTICS.map(ab => {
                    const active = selectedAntibiotics.includes(ab);
                    return (
                      <Button
                        key={ab}
                        size="sm"
                        variant={active ? "default" : "outline"}
                        className={active ? "bg-green-600 hover:bg-green-700" : ""}
                        onClick={() => {
                          if (active) setSelectedAntibiotics(selectedAntibiotics.filter(a => a !== ab));
                          else setSelectedAntibiotics([...selectedAntibiotics, ab]);
                        }}
                      >
                        {active && <CheckCircle2 className="h-3 w-3 mr-1" />}
                        {ab}
                      </Button>
                    );
                  })}
                </div>
              </div>
            )}

            {selectedAction === 'DISMISS' && (
              <div className="space-y-3">
                <label className="text-sm font-semibold flex items-center gap-2 text-slate-700">
                  <XCircle className="h-4 w-4" /> Silence Duration (Hours)
                </label>
                <p className="text-[10px] text-slate-500">The alert will not trigger again for this patient until the duration elapses unless another critical spike occurs.</p>
                <div className="flex gap-2">
                  {['2', '4', '8', '12'].map(h => (
                    <Button 
                      key={h}
                      variant={dismissDuration === h ? "default" : "outline"}
                      size="sm"
                      onClick={() => setDismissDuration(h)}
                      className="flex-1"
                    >
                      {h}h
                    </Button>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 space-y-2">
              <label className="text-xs font-medium text-slate-500">Additional Instructions (Optional)</label>
              <Textarea 
                placeholder="Type messages for the nursing staff..."
                value={actionDetail}
                onChange={(e) => setActionDetail(e.target.value)}
                className="bg-white text-sm"
              />
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-4">
          <Button 
            variant="outline" 
            className="flex-1 h-11"
            onClick={onCancel}
          >
            Cancel
          </Button>
          <Button 
            className="flex-1 h-11 bg-red-600 hover:bg-red-700 text-white font-bold text-lg"
            disabled={!selectedAction || isSubmitting}
            onClick={handleSubmit}
          >
            {isSubmitting ? "Submitting..." : "COMMIT DECISION"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
