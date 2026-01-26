'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AlertCircle, Stethoscope, TestTube, Eye, XCircle } from 'lucide-react';

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
}

export default function CriticalActionPanel({ alert, doctorId, onActionTaken }: CriticalActionPanelProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [actionDetail, setActionDetail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!alert || alert.alert_status !== 'PENDING_DOCTOR_ACTION') {
    return null;
  }

  const handleAction = async (actionType: string) => {
    setSelectedAction(actionType);
  };

  const handleSubmit = async () => {
    if (!selectedAction || !actionDetail.trim()) {
      window.alert('Please provide action details');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/log_doctor_action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          alert_id: alert.alert_id,
          doctor_id: doctorId,
          action_type: selectedAction,
          action_detail: actionDetail,
        }),
      });

      if (response.ok) {
        setSelectedAction(null);
        setActionDetail('');
        onActionTaken();
      } else {
        console.error('Failed to log action');
      }
    } catch (error) {
      console.error('Error logging action:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const actions = [
    {
      type: 'OBSERVE',
      label: 'Close Monitoring',
      icon: Eye,
      color: 'bg-blue-900/30 hover:bg-blue-900/50 border-blue-500',
      description: 'Monitor vitals closely without immediate intervention',
    },
    {
      type: 'TREAT',
      label: 'Start Treatment',
      icon: Stethoscope,
      color: 'bg-green-900/30 hover:bg-green-900/50 border-green-500',
      description: 'Initiate antibiotic therapy or other treatment',
    },
    {
      type: 'LAB_TEST',
      label: 'Order Labs',
      icon: TestTube,
      color: 'bg-yellow-900/30 hover:bg-yellow-900/50 border-yellow-500',
      description: 'Order blood culture, CBC, CRP tests',
    },
    {
      type: 'DISMISS',
      label: 'Dismiss Alert',
      icon: XCircle,
      color: 'bg-red-900/30 hover:bg-red-900/50 border-red-500',
      description: 'Consider this a false positive',
    },
  ];

  return (
    <Card className="border-red-500 bg-red-950/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-400">
          <AlertCircle className="h-5 w-5 animate-pulse" />
          Critical Alert - Immediate Action Required
        </CardTitle>
        <div className="text-sm text-muted-foreground mt-2">
          <p>Patient: {alert.baby_id}</p>
          <p>Risk Score: {(alert.model_risk_score * 100).toFixed(1)}%</p>
          <p>Alert ID: #{alert.alert_id}</p>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!selectedAction ? (
          <div className="grid grid-cols-2 gap-3">
            {actions.map((action) => {
              const Icon = action.icon;
              return (
                <Button
                  key={action.type}
                  onClick={() => handleAction(action.type)}
                  className={`h-auto flex-col items-start p-4 border-2 ${action.color}`}
                  variant="outline"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-5 w-5" />
                    <span className="font-semibold">{action.label}</span>
                  </div>
                  <span className="text-xs text-muted-foreground text-left">
                    {action.description}
                  </span>
                </Button>
              );
            })}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="font-semibold mb-2">
                Selected Action: {actions.find(a => a.type === selectedAction)?.label}
              </p>
              <Textarea
                placeholder="Enter detailed action plan and reasoning..."
                value={actionDetail}
                onChange={(e) => setActionDetail(e.target.value)}
                rows={4}
                className="mt-2"
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting || !actionDetail.trim()}
                className="flex-1"
              >
                {isSubmitting ? 'Submitting...' : 'Confirm & Log Action'}
              </Button>
              <Button
                onClick={() => {
                  setSelectedAction(null);
                  setActionDetail('');
                }}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
