"use client";

import { 
  User, 
  Activity, 
  FileText, 
  FlaskConical, 
  Pill, 
  Utensils, 
  Wind, 
  Shield, 
  ClipboardCheck 
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const navItems = [
    { id: "profile", label: "Patient Profile", icon: User },
    { id: "vitals", label: "Vitals & Trends", icon: Activity },
    { id: "notes", label: "Clinical Notes", icon: FileText },
    { id: "labs", label: "Lab Results", icon: FlaskConical },
    { id: "medication", label: "Medication", icon: Pill },
    { id: "feeding", label: "Feeding & Output", icon: Utensils },
    { id: "respiratory", label: "Respiratory Support", icon: Wind },
    { id: "screening", label: "Screening & Immunization", icon: Shield },
    { id: "discharge", label: "Discharge Planning", icon: ClipboardCheck },
  ];

  return (
    <div className="w-56 border-r border-border bg-background h-screen flex flex-col">
      <div className="p-5 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">
          NeoVance AI
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">NICU Monitoring System</p>
      </div>

      <nav className="flex-1 p-3 overflow-y-auto">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-2.5 rounded-lg transition-all text-sm",
                  "hover:bg-primary/10 group",
                  activeView === item.id
                    ? "bg-primary/20 text-primary font-semibold"
                    : "text-primary/80 hover:text-primary"
                )}
              >
                <Icon className={cn(
                  "h-4 w-4 transition-colors",
                  activeView === item.id ? "text-primary" : "text-primary/70"
                )} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <div className="p-3 border-t border-border">
        <div className="text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Status</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Online
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
