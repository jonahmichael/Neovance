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
  ChevronRight,
  LogOut,
  Lock
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const { user, logout } = useAuth();
  
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
    { id: "custody", label: "Chain of Custody", icon: Lock },
  ];

  return (
    <div className="w-56 bg-white border-r border-gray-200 h-screen flex flex-col font-sans">
      {/* Logo Header */}
      <div className="px-4 py-5 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Activity className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-base font-bold text-gray-900 tracking-tight font-sans">NeoVance AI</h1>
            <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider font-sans">NICU Monitor</p>
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
                  "w-full flex items-center justify-between px-3 py-2 rounded-md transition-all duration-150 group font-sans",
                  isActive
                    ? "bg-blue-50 text-blue-700 font-semibold"
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={cn(
                    "h-4 w-4 transition-colors",
                    isActive ? "text-blue-600" : "text-gray-400"
                  )} />
                  <span className="text-[13px] font-sans">{item.label}</span>
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
      <div className="px-3 py-3 border-t border-gray-200 space-y-3">
        {/* User Info */}
        {user && (
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                user.role === 'DOCTOR' ? 'bg-blue-500' : 'bg-green-500'
              }`}></div>
              <span className="text-gray-700 font-sans">{user.name}</span>
            </div>
            <button
              onClick={() => {
                console.log('Logout button clicked');
                logout();
              }}
              className="flex items-center gap-1 px-2 py-1 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors text-xs"
              title="Logout"
            >
              <LogOut className="h-3 w-3" />
              <span className="font-sans">Logout</span>
            </button>
          </div>
        )}
        
        {/* System Status */}
        <div className="flex items-center justify-between text-[11px] text-gray-500">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-gray-600 font-sans">Online</span>
          </div>
          <span className="font-sans">v1.0</span>
        </div>
      </div>
    </div>
  );
}
