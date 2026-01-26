"use client";

import { 
  User, 
  Activity, 
  FileText, 
  TestTube, 
  Pill, 
  Utensils, 
  Wind, 
  Shield, 
  ClipboardCheck,
  Stethoscope,
  ChevronRight
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
    { id: "labs", label: "Lab Results", icon: TestTube },
    { id: "medication", label: "Medication", icon: Pill },
    { id: "feeding", label: "Feeding & Output", icon: Utensils },
    { id: "respiratory", label: "Respiratory", icon: Wind },
    { id: "screening", label: "Screening", icon: Shield },
    { id: "discharge", label: "Discharge", icon: ClipboardCheck },
  ];

  return (
    <div className="w-56 bg-slate-900 h-screen flex flex-col">
      {/* Logo Header */}
      <div className="px-4 py-5 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center">
            <Stethoscope className="h-4 w-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">NeoVance AI</h1>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">NICU Monitor</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 overflow-y-auto">
        <div className="space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 rounded-md transition-all duration-150 group",
                  isActive
                    ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={cn(
                    "h-4 w-4 transition-colors",
                    isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                  )} />
                  <span className={cn(
                    "text-[13px]",
                    isActive ? "font-semibold" : "font-medium"
                  )}>{item.label}</span>
                </div>
                {isActive && (
                  <ChevronRight className="h-3.5 w-3.5 text-cyan-400" />
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Status Footer */}
      <div className="px-3 py-3 border-t border-slate-700/50">
        <div className="flex items-center justify-between text-[11px] text-slate-500">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-slate-400">Online</span>
          </div>
          <span>v1.0</span>
        </div>
      </div>
    </div>
  );
}
