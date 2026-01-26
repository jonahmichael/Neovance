"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock } from "lucide-react";

interface Alert {
  alert_id: number;
  baby_id: string;
  timestamp: string;
  model_risk_score: number;
  alert_status: string;
  doctor_action?: string;
}

interface DoctorInstructionsProps {
  alerts: Alert[];
}

export default function DoctorInstructions({ alerts }: DoctorInstructionsProps) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  const getActionColor = (action?: string) => {
    switch (action) {
      case "TREAT":
        return "bg-green-900/30 text-green-400";
      case "OBSERVE":
        return "bg-blue-900/30 text-blue-400";
      case "LAB_TEST":
        return "bg-yellow-900/30 text-yellow-400";
      case "DISMISS":
        return "bg-red-900/30 text-red-400";
      default:
        return "bg-gray-900/30 text-gray-400";
    }
  };

  const getActionLabel = (action?: string) => {
    switch (action) {
      case "TREAT":
        return "Start Treatment";
      case "OBSERVE":
        return "Close Monitoring";
      case "LAB_TEST":
        return "Order Labs";
      case "DISMISS":
        return "Alert Dismissed";
      default:
        return "Unknown Action";
    }
  };

  return (
    <Card className="border-blue-500 bg-blue-950/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-blue-400">
          <CheckCircle className="h-5 w-5" />
          Doctor's Instructions (Recent Actions)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.alert_id}
            className="p-4 bg-muted rounded-lg border-l-4 border-blue-500"
          >
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="font-semibold">Patient: {alert.baby_id}</p>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(alert.timestamp).toLocaleString()}
                </p>
              </div>
              <Badge className={getActionColor(alert.doctor_action)}>
                {getActionLabel(alert.doctor_action)}
              </Badge>
            </div>
            <div className="text-sm">
              <p className="text-muted-foreground">
                Risk Score: {(alert.model_risk_score * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
