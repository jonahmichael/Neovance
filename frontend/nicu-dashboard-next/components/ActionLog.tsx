"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Eye, Stethoscope, FileText } from "lucide-react";

export default function ActionLog() {
  const actions = [
    {
      time: "14:23",
      type: "medication",
      action: "Ampicillin 50mg/kg IV administered",
      staff: "Dr. Sarah Chen",
      icon: Activity,
    },
    {
      time: "14:15",
      type: "observation",
      action: "Vital signs checked - all stable",
      staff: "Nurse Maria Rodriguez",
      icon: Eye,
    },
    {
      time: "14:05",
      type: "procedure",
      action: "Blood culture sample collected",
      staff: "Dr. James Wilson",
      icon: Stethoscope,
    },
    {
      time: "13:50",
      type: "note",
      action: "Parent consultation completed",
      staff: "Dr. Sarah Chen",
      icon: FileText,
    },
  ];

  const getTypeColor = (type: string) => {
    switch (type) {
      case "medication":
        return "text-cyan-400 bg-cyan-900/20";
      case "observation":
        return "text-purple-400 bg-purple-900/20";
      case "procedure":
        return "text-yellow-400 bg-yellow-900/20";
      case "note":
        return "text-blue-400 bg-blue-900/20";
      default:
        return "text-gray-400 bg-gray-900/20";
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">Clinical Action Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {actions.map((action, index) => {
            const Icon = action.icon;
            return (
              <div
                key={index}
                className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <div className={`p-2 rounded-lg ${getTypeColor(action.type)}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">{action.action}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{action.time}</span>
                    <span>•</span>
                    <span>{action.staff}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
