"use client";

import { useState } from "react";
import { Activity, History, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const navItems = [
    { id: "monitor", label: "Real-Time Monitor", icon: Activity },
    { id: "history", label: "Patient History", icon: History },
    { id: "actions", label: "Action Log", icon: FileText },
  ];

  return (
    <div className="w-64 border-r border-border bg-card h-screen flex flex-col">
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          Neovance AI
        </h1>
        <p className="text-sm text-muted-foreground mt-1">NICU Monitoring System</p>
      </div>

      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all",
                  "hover:bg-muted/80 group",
                  activeView === item.id
                    ? "bg-primary/10 text-primary border border-primary/20"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className={cn(
                  "h-5 w-5 transition-colors",
                  activeView === item.id ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                )} />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground">
          <div className="flex items-center justify-between mb-2">
            <span>Status</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              Online
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Version</span>
            <span>1.0.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
