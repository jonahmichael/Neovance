'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Clock, 
  FlaskConical, 
  Pill, 
  AlertCircle, 
  CheckCircle2, 
  Timer,
  ChevronRight,
  ClipboardList
} from 'lucide-react';

interface NurseActionFollowupProps {
  alert: any;
  onComplete?: () => void;
}

export default function NurseActionFollowup({ alert, onComplete }: NurseActionFollowupProps) {
  const [timeLeft, setTimeLeft] = useState<string>("");
  const [completedLabs, setCompletedLabs] = useState<string[]>([]);
  const [completedMeds, setCompletedMeds] = useState<string[]>([]);

  // Parse details from alert
  const details = typeof alert.action_taken === 'string' 
    ? { type: alert.action_taken, duration: alert.observation_duration, labs: alert.lab_tests, antibiotics: alert.antibiotics }
    : { type: 'OBSERVATION', duration: '6', labs: [], antibiotics: [] };

  useEffect(() => {
    if (details.type === 'OBSERVATION' || details.type === 'DISMISS') {
      const durationHours = parseInt(String(details.duration || alert.dismiss_duration || 0));
      if (!durationHours) return;

      const endTime = new Date(alert.updated_at || new Date()).getTime() + (durationHours * 60 * 60 * 1000);
      
      const timer = setInterval(() => {
        const now = new Date().getTime();
        const distance = endTime - now;

        if (distance < 0) {
          clearInterval(timer);
          setTimeLeft("EXPIRED");
        } else {
          const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((distance % (1000 * 60)) / 1000);
          setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
        }
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [alert, details]);

  const renderObservation = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between bg-blue-50 p-4 rounded-xl border border-blue-100">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg text-white">
            <Timer className="h-6 w-6 animate-pulse" />
          </div>
          <div>
            <p className="text-sm font-semibold text-blue-900 uppercase tracking-wider">Active Observation</p>
            <p className="text-2xl font-mono font-bold text-blue-700">{timeLeft || "--h --m --s"}</p>
          </div>
        </div>
        <Badge variant="outline" className="bg-white border-blue-200 text-blue-700 px-3 py-1">
          {details.duration} hour period
        </Badge>
      </div>
      <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
        <p className="text-xs font-bold text-slate-500 mb-2 flex items-center gap-1">
          <ClipboardList className="h-3 w-3" /> NURSING INSTRUCTIONS
        </p>
        <p className="text-sm text-slate-700 leading-relaxed">
          {alert.action_detail || "Perform regular vitals check every 15 minutes. Report any worsening respiratory effort or temperature instability immediately."}
        </p>
      </div>
    </div>
  );

  const renderLabs = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <FlaskConical className="h-5 w-5 text-amber-600" />
        <h3 className="font-bold text-slate-800">Pending Lab Collections</h3>
      </div>
      <div className="grid gap-2">
        {(alert.lab_tests || []).map((lab: string) => (
          <div 
            key={lab} 
            className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
              completedLabs.includes(lab) ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200'
            }`}
          >
            <div className="flex items-center gap-3">
              <Checkbox 
                id={lab} 
                checked={completedLabs.includes(lab)}
                onCheckedChange={(checked) => {
                  if (checked) setCompletedLabs([...completedLabs, lab]);
                  else setCompletedLabs(completedLabs.filter(l => l !== lab));
                }}
              />
              <label htmlFor={lab} className={`text-sm font-medium ${completedLabs.includes(lab) ? 'text-green-700 line-through' : 'text-slate-700'}`}>
                {lab}
              </label>
            </div>
            {completedLabs.includes(lab) && <CheckCircle2 className="h-4 w-4 text-green-500" />}
          </div>
        ))}
      </div>
    </div>
  );

  const renderAntibiotics = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Pill className="h-5 w-5 text-green-600" />
        <h3 className="font-bold text-slate-800">Antibiotic Administration</h3>
      </div>
      <div className="grid gap-2">
        {(alert.antibiotics || []).map((med: string) => (
          <div 
            key={med} 
            className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
              completedMeds.includes(med) ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200 font-bold border-l-4 border-l-green-500'
            }`}
          >
            <div className="flex items-center gap-3">
              <Checkbox 
                id={med} 
                checked={completedMeds.includes(med)}
                onCheckedChange={(checked) => {
                  if (checked) setCompletedMeds([...completedMeds, med]);
                  else setCompletedMeds(completedMeds.filter(a => a !== med));
                }}
              />
              <label htmlFor={med} className={`text-sm font-medium ${completedMeds.includes(med) ? 'text-green-700 line-through' : 'text-slate-700'}`}>
                {med} (Stat Dose)
              </label>
            </div>
            {completedMeds.includes(med) ? (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : (
              <Badge className="bg-green-100 text-green-700 hover:bg-green-100">DUE NOW</Badge>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <Card className="w-full border-2 border-slate-200 shadow-lg overflow-hidden max-w-2xl mx-auto">
      <CardHeader className="bg-slate-900 text-white py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-amber-500 p-1.5 rounded-full">
              <AlertCircle className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold">Doctor's Clinical Decision</CardTitle>
              <p className="text-xs text-slate-400">Alert ID: #{alert.alert_id} • Decided at {new Date(alert.updated_at).toLocaleTimeString()}</p>
            </div>
          </div>
          <Badge className="bg-blue-600 text-white border-none uppercase text-[10px] tracking-widest px-2">
            Nurse Task
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-start gap-4">
          <div className="mt-1">
            {details.type === 'OBSERVATION' && <Clock className="h-6 w-6 text-blue-600" />}
            {details.type === 'LAB_TESTS' && <FlaskConical className="h-6 w-6 text-amber-600" />}
            {details.type === 'ANTIBIOTICS' && <Pill className="h-6 w-6 text-green-600" />}
            {details.type === 'DISMISS' && <CheckCircle2 className="h-6 w-6 text-slate-400" />}
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900 uppercase">Decision: {details.type.replace('_', ' ')}</h4>
            <p className="text-sm text-slate-600 italic">"{alert.action_detail || "Follow standard protocols for this action."}"</p>
          </div>
        </div>

        <div className="space-y-8">
          {(details.type === 'OBSERVATION' || details.type === 'DISMISS') && renderObservation()}
          {details.type === 'LAB_TESTS' && renderLabs()}
          {details.type === 'ANTIBIOTICS' && renderAntibiotics()}
          
          {(alert.lab_tests && alert.lab_tests.length > 0 && details.type !== 'LAB_TESTS') && renderLabs()}
          {(alert.antibiotics && alert.antibiotics.length > 0 && details.type !== 'ANTIBIOTICS') && renderAntibiotics()}
        </div>

        <div className="mt-8 pt-6 border-t border-slate-100 flex justify-end">
          <Button 
            className="bg-slate-900 hover:bg-slate-800 text-white px-8 h-12 rounded-xl group"
            onClick={onComplete}
          >
            Acknowledge & Sync to Chart
            <ChevronRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
