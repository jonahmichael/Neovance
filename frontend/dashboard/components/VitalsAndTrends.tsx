"use client";

import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import CriticalActionPanel from "@/components/CriticalActionPanel";
import { Heart, Activity, Wind, Thermometer, Gauge, TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2, AlertCircle, Zap } from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface VitalData {
  timestamp: string;
  hr: number;
  spo2: number;
  rr: number;
  temp: number;
  map: number;
  risk_score: number;
  status: string;
}

type ChartType = "hr" | "spo2" | "rr" | "temp" | "map" | "all";

interface ClinicalRange {
  normal: string;
  abnormal: { label: string; value: string; severity: "warning" | "critical" }[];
}

interface ChartConfig {
  id: ChartType;
  name: string;
  description: string;
  category: "time-series";
  xLabel: string;
  yLabel: string;
  icon: React.ReactNode;
  color: string;
  ranges?: ClinicalRange;
}

const CHART_CONFIGS: ChartConfig[] = [
  // Time Series (Primary - 99% use)
  { 
    id: "hr", 
    name: "Heart Rate", 
    description: "Detects bradycardia, tachycardia, arrhythmias", 
    category: "time-series", 
    xLabel: "Time", 
    yLabel: "HR (bpm)", 
    icon: <Heart className="h-4 w-4" />, 
    color: "rgb(239, 68, 68)",
    ranges: {
      normal: "120-160 bpm",
      abnormal: [
        { label: "Bradycardia", value: "<100 bpm", severity: "warning" },
        { label: "Severe Brady", value: "<60 bpm", severity: "critical" },
        { label: "Tachycardia", value: ">180 bpm", severity: "warning" },
        { label: "Danger", value: ">200 bpm (SVT/sepsis)", severity: "critical" }
      ]
    }
  },
  { 
    id: "spo2", 
    name: "SpO2", 
    description: "Detects desaturation, guides oxygen therapy", 
    category: "time-series", 
    xLabel: "Time", 
    yLabel: "SpO2 (%)", 
    icon: <Activity className="h-4 w-4" />, 
    color: "rgb(168, 85, 247)",
    ranges: {
      normal: "90-95% (preterm target)",
      abnormal: [
        { label: "Hypoxia", value: "<88%", severity: "warning" },
        { label: "Severe Desat", value: "<80%", severity: "critical" },
        { label: "Hyperoxia (ROP risk)", value: ">95-97%", severity: "warning" }
      ]
    }
  },
  { 
    id: "rr", 
    name: "Respiratory Rate", 
    description: "Detects apnea, tachypnea, respiratory fatigue", 
    category: "time-series", 
    xLabel: "Time", 
    yLabel: "RR (breaths/min)", 
    icon: <Wind className="h-4 w-4" />, 
    color: "rgb(59, 130, 246)",
    ranges: {
      normal: "30-60 breaths/min",
      abnormal: [
        { label: "Bradypnea", value: "<30", severity: "warning" },
        { label: "Apnea", value: "Pause >=20 sec", severity: "critical" },
        { label: "Tachypnea", value: ">60-70", severity: "warning" },
        { label: "Severe Distress", value: ">80", severity: "critical" }
      ]
    }
  },
  { 
    id: "temp", 
    name: "Temperature", 
    description: "Detects fever, hypothermia, infection signs", 
    category: "time-series", 
    xLabel: "Time", 
    yLabel: "Temp (C)", 
    icon: <Thermometer className="h-4 w-4" />, 
    color: "rgb(249, 115, 22)",
    ranges: {
      normal: "36.5-37.5 C",
      abnormal: [
        { label: "Hypothermia", value: "<36.5 C", severity: "warning" },
        { label: "Hyperthermia", value: ">37.5 C", severity: "warning" },
        { label: "Sepsis Concern", value: ">38.0 C", severity: "critical" }
      ]
    }
  },
  { 
    id: "map", 
    name: "Mean Arterial Pressure", 
    description: "Shows perfusion status, detects shock", 
    category: "time-series", 
    xLabel: "Time", 
    yLabel: "MAP (mmHg)", 
    icon: <Gauge className="h-4 w-4" />, 
    color: "rgb(34, 197, 94)",
    ranges: {
      normal: "Preterm: 30-40 mmHg | Term: 45-65 mmHg",
      abnormal: [
        { label: "Hypotension", value: "<30 mmHg (preterm)", severity: "warning" },
        { label: "Shock", value: "Low MAP + High HR", severity: "critical" },
        { label: "Hypertension", value: ">70 mmHg", severity: "warning" }
      ]
    }
  },
  { id: "all", name: "All Vitals", description: "Combined view of all vital signs", category: "time-series", xLabel: "Time", yLabel: "Value", icon: <TrendingUp className="h-4 w-4" />, color: "rgb(99, 102, 241)" },
];

export default function VitalsAndTrends() {
  const [data, setData] = useState<VitalData[]>([]);
  const [latestData, setLatestData] = useState<VitalData | null>(null);
  const [wsStatus, setWsStatus] = useState<string>("Connecting...");
  const [selectedChart, setSelectedChart] = useState<ChartType>("all");
  const [showChartSelector, setShowChartSelector] = useState(false);
  const [viewMode, setViewMode] = useState<"simple" | "detailed">("simple");
  const [sepsisTriggered, setSepsisTriggered] = useState(false);
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    // Set initial time on client side to avoid hydration mismatch
    setCurrentTime(new Date().toLocaleTimeString());
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const triggerSepsis = async () => {
    try {
      setSepsisTriggered(true);
      const response = await fetch("http://localhost:8000/trigger-sepsis", {
        method: "POST",
      });
      if (response.ok) {
        console.log("Sepsis triggered successfully");
        setTimeout(() => setSepsisTriggered(false), 10000); // Reset after 10 seconds
      }
    } catch (error) {
      console.error("Failed to trigger sepsis:", error);
      setSepsisTriggered(false);
    }
  };

  // Helper functions for user-friendly status
  const getVitalStatus = (vital: string, value: number | undefined): { status: "stable" | "warning" | "critical"; label: string } => {
    if (!value) return { status: "stable", label: "No Data" };
    
    switch (vital) {
      case "hr":
        if (value < 60) return { status: "critical", label: "Severe Brady" };
        if (value < 100) return { status: "warning", label: "Low" };
        if (value > 200) return { status: "critical", label: "Danger" };
        if (value > 180) return { status: "warning", label: "High" };
        return { status: "stable", label: "Normal" };
      case "spo2":
        if (value < 80) return { status: "critical", label: "Severe Desat" };
        if (value < 88) return { status: "warning", label: "Low" };
        if (value > 97) return { status: "warning", label: "High (ROP)" };
        return { status: "stable", label: "Normal" };
      case "rr":
        if (value < 20) return { status: "critical", label: "Apnea Risk" };
        if (value < 30) return { status: "warning", label: "Low" };
        if (value > 80) return { status: "critical", label: "Severe" };
        if (value > 60) return { status: "warning", label: "High" };
        return { status: "stable", label: "Normal" };
      case "temp":
        if (value > 38) return { status: "critical", label: "Fever" };
        if (value < 36) return { status: "critical", label: "Cold" };
        if (value < 36.5 || value > 37.5) return { status: "warning", label: "Borderline" };
        return { status: "stable", label: "Normal" };
      case "map":
        if (value < 25) return { status: "critical", label: "Shock Risk" };
        if (value < 30) return { status: "warning", label: "Low" };
        if (value > 70) return { status: "warning", label: "High" };
        return { status: "stable", label: "Normal" };
      default:
        return { status: "stable", label: "Normal" };
    }
  };

  const getTrend = (vital: string): { direction: "up" | "down" | "stable"; label: string } => {
    if (data.length < 5) return { direction: "stable", label: "Stable" };
    
    const recent = data.slice(-5);
    const older = data.slice(-10, -5);
    if (older.length === 0) return { direction: "stable", label: "Stable" };
    
    const recentAvg = recent.reduce((sum, d) => sum + (d[vital as keyof VitalData] as number), 0) / recent.length;
    const olderAvg = older.reduce((sum, d) => sum + (d[vital as keyof VitalData] as number), 0) / older.length;
    
    const diff = recentAvg - olderAvg;
    const threshold = vital === "temp" ? 0.2 : 5;
    
    if (diff > threshold) return { direction: "up", label: "Rising" };
    if (diff < -threshold) return { direction: "down", label: "Falling" };
    return { direction: "stable", label: "Stable" };
  };

  const countDesatEvents = (): { count: number; severe: number } => {
    let count = 0;
    let severe = 0;
    data.forEach(d => {
      if (d.spo2 < 88) count++;
      if (d.spo2 < 80) severe++;
    });
    return { count, severe };
  };

  const getOverallStability = (): { status: "stable" | "caution" | "alert"; message: string } => {
    if (!latestData) return { status: "stable", message: "Awaiting data..." };
    
    const issues: string[] = [];
    if (latestData.hr < 100 || latestData.hr > 180) issues.push("Heart rate");
    if (latestData.spo2 < 88) issues.push("Oxygen");
    if (latestData.rr < 30 || latestData.rr > 70) issues.push("Breathing");
    if (latestData.temp < 36.5 || latestData.temp > 37.5) issues.push("Temperature");
    if (latestData.map < 30) issues.push("Blood pressure");
    
    if (issues.length === 0) return { status: "stable", message: "All vitals within normal range" };
    if (issues.length <= 2) return { status: "caution", message: `Monitor: ${issues.join(", ")}` };
    return { status: "alert", message: `Multiple concerns: ${issues.join(", ")}` };
  };

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket("ws://localhost:8000/ws/live");

      ws.onopen = () => {
        setWsStatus("Connected");
      };

      ws.onmessage = (event) => {
        const newData: VitalData = JSON.parse(event.data);
        setLatestData(newData);
        setData((prev) => {
          const updated = [...prev, newData];
          return updated.slice(-60); // Keep last 60 data points
        });
      };

      ws.onerror = () => {
        setWsStatus("Error");
      };

      ws.onclose = () => {
        setWsStatus("Reconnecting...");
        reconnectTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const getTimeLabels = () => data.map((d) => new Date(d.timestamp).toLocaleTimeString());

  const getChartOptions = (config: ChartConfig) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: { display: selectedChart === "all", position: "top" as const, labels: { color: "rgb(100, 116, 139)", usePointStyle: true } },
      title: { display: true, text: `${config.name} - ${config.description}`, color: "rgb(51, 65, 85)", font: { size: 14 } },
    },
    scales: {
      x: { title: { display: true, text: config.xLabel, color: "rgb(100, 116, 139)" }, ticks: { color: "rgb(100, 116, 139)" }, grid: { color: "rgba(100, 116, 139, 0.1)" } },
      y: { title: { display: true, text: config.yLabel, color: "rgb(100, 116, 139)" }, ticks: { color: "rgb(100, 116, 139)" }, grid: { color: "rgba(100, 116, 139, 0.1)" } },
    },
  });

  const renderChart = () => {
    const config = CHART_CONFIGS.find((c) => c.id === selectedChart)!;

    let datasets: { label: string; data: number[]; borderColor: string; backgroundColor: string; tension: number; fill: boolean; pointRadius: number }[] = [];

    switch (selectedChart) {
      case "hr":
        datasets = [{ label: "Heart Rate", data: data.map((d) => d.hr), borderColor: "rgb(239, 68, 68)", backgroundColor: "rgba(239, 68, 68, 0.1)", tension: 0.3, fill: true, pointRadius: 2 }];
        break;
      case "spo2":
        datasets = [{ label: "SpO2", data: data.map((d) => d.spo2), borderColor: "rgb(168, 85, 247)", backgroundColor: "rgba(168, 85, 247, 0.1)", tension: 0.3, fill: true, pointRadius: 2 }];
        break;
      case "rr":
        datasets = [{ label: "Respiratory Rate", data: data.map((d) => d.rr), borderColor: "rgb(59, 130, 246)", backgroundColor: "rgba(59, 130, 246, 0.1)", tension: 0.3, fill: true, pointRadius: 2 }];
        break;
      case "temp":
        datasets = [{ label: "Temperature", data: data.map((d) => d.temp), borderColor: "rgb(249, 115, 22)", backgroundColor: "rgba(249, 115, 22, 0.1)", tension: 0.3, fill: true, pointRadius: 2 }];
        break;
      case "map":
        datasets = [{ label: "MAP", data: data.map((d) => d.map), borderColor: "rgb(34, 197, 94)", backgroundColor: "rgba(34, 197, 94, 0.1)", tension: 0.3, fill: true, pointRadius: 2 }];
        break;
      case "all":
        datasets = [
          { label: "HR", data: data.map((d) => d.hr), borderColor: "rgb(239, 68, 68)", backgroundColor: "transparent", tension: 0.3, fill: false, pointRadius: 0 },
          { label: "SpO2", data: data.map((d) => d.spo2), borderColor: "rgb(168, 85, 247)", backgroundColor: "transparent", tension: 0.3, fill: false, pointRadius: 0 },
          { label: "RR", data: data.map((d) => d.rr), borderColor: "rgb(59, 130, 246)", backgroundColor: "transparent", tension: 0.3, fill: false, pointRadius: 0 },
          { label: "Temp x10", data: data.map((d) => d.temp * 2.5), borderColor: "rgb(249, 115, 22)", backgroundColor: "transparent", tension: 0.3, fill: false, pointRadius: 0 },
          { label: "MAP", data: data.map((d) => d.map), borderColor: "rgb(34, 197, 94)", backgroundColor: "transparent", tension: 0.3, fill: false, pointRadius: 0 },
        ];
        break;
    }

    return <Line data={{ labels: getTimeLabels(), datasets }} options={getChartOptions(config)} />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "OK": return "text-green-600 bg-green-100";
      case "WARNING": return "text-yellow-600 bg-yellow-100";
      case "CRITICAL": return "text-red-600 bg-red-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const currentConfig = CHART_CONFIGS.find((c) => c.id === selectedChart)!;

  return (
    <div className="space-y-6 font-sans">
      {/* Vital Signs Cards */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { key: "hr", label: "Heart Rate", value: latestData?.hr, unit: "bpm", icon: <Heart className="h-5 w-5" />, color: "text-red-500", bg: "bg-red-50" },
          { key: "spo2", label: "SpO2", value: latestData?.spo2, unit: "%", icon: <Activity className="h-5 w-5" />, color: "text-purple-500", bg: "bg-purple-50" },
          { key: "rr", label: "Resp Rate", value: latestData?.rr, unit: "/min", icon: <Wind className="h-5 w-5" />, color: "text-blue-500", bg: "bg-blue-50" },
          { key: "temp", label: "Temperature", value: latestData?.temp?.toFixed(1), unit: "C", icon: <Thermometer className="h-5 w-5" />, color: "text-orange-500", bg: "bg-orange-50" },
          { key: "map", label: "MAP", value: latestData?.map, unit: "mmHg", icon: <Gauge className="h-5 w-5" />, color: "text-green-500", bg: "bg-green-50" },
        ].map((vital) => (
          <Card key={vital.key} className={`${vital.bg} border-none shadow-sm`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className={vital.color}>{vital.icon}</span>
                <span className="text-xs text-muted-foreground">{vital.label}</span>
              </div>
              <div className="text-center">
                <span className={`text-3xl font-bold ${vital.color}`}>{vital.value ?? "--"}</span>
                <span className="text-sm text-muted-foreground ml-1">{vital.unit}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* View Mode Toggle and Baby Stability Dashboard */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode("simple")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              viewMode === "simple" 
                ? "bg-cyan-500 text-white" 
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            Simple View
          </button>
          <button
            onClick={() => setViewMode("detailed")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              viewMode === "detailed" 
                ? "bg-cyan-500 text-white" 
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            Detailed Charts
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm px-2 py-1 rounded ${wsStatus === "Connected" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
            {wsStatus}
          </span>
          <button
            onClick={triggerSepsis}
            disabled={sepsisTriggered}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              sepsisTriggered 
                ? "bg-red-600 text-white cursor-not-allowed animate-pulse" 
                : "bg-red-500 text-white hover:bg-red-600"
            }`}
          >
            <Zap className="h-4 w-4" />
            {sepsisTriggered ? "Sepsis Active..." : "Trigger Sepsis"}
          </button>
        </div>
      </div>

      {/* Simple View - Baby Stability Dashboard */}
      {viewMode === "simple" && (
        <div className="space-y-4">
          {/* Overall Status Banner */}
          {(() => {
            const overall = getOverallStability();
            return (
              <Card className={`shadow-sm border-2 ${
                overall.status === "stable" ? "border-green-300 bg-green-50" :
                overall.status === "caution" ? "border-amber-300 bg-amber-50" :
                "border-red-300 bg-red-50"
              }`}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {overall.status === "stable" ? (
                        <CheckCircle2 className="h-8 w-8 text-green-600" />
                      ) : overall.status === "caution" ? (
                        <AlertTriangle className="h-8 w-8 text-amber-600" />
                      ) : (
                        <AlertCircle className="h-8 w-8 text-red-600" />
                      )}
                      <div>
                        <h2 className={`text-lg font-bold ${
                          overall.status === "stable" ? "text-green-800" :
                          overall.status === "caution" ? "text-amber-800" :
                          "text-red-800"
                        }`}>
                          {overall.status === "stable" ? "Baby Stable" :
                           overall.status === "caution" ? "Monitor Closely" :
                           "Needs Attention"}
                        </h2>
                        <p className={`text-sm ${
                          overall.status === "stable" ? "text-green-700" :
                          overall.status === "caution" ? "text-amber-700" :
                          "text-red-700"
                        }`}>{overall.message}</p>
                      </div>
                    </div>
                    <div className="flex gap-6 text-right">
                      <div>
                        <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Current Clock</p>
                        <p className="text-sm font-bold text-blue-600">{currentTime || "--:--:--"}</p>
                      </div>
                      <div className="border-l border-slate-200 pl-6">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Last Updated</p>
                        <p className="text-sm font-medium text-slate-600">
                          {latestData ? new Date(latestData.timestamp).toLocaleTimeString() : "--:--:--"}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })()}

          {/* Stability Dashboard Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Heart - Stress Control */}
            {(() => {
              const status = getVitalStatus("hr", latestData?.hr);
              const trend = getTrend("hr");
              return (
                <Card className="shadow-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Heart className="h-5 w-5 text-red-500" />
                        <span className="font-semibold text-sm">Heart</span>
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        status.status === "stable" ? "bg-green-500" :
                        status.status === "warning" ? "bg-amber-500" : "bg-red-500"
                      }`} />
                    </div>
                    <div className={`text-center py-3 rounded-lg mb-2 ${
                      status.status === "stable" ? "bg-green-100" :
                      status.status === "warning" ? "bg-amber-100" : "bg-red-100"
                    }`}>
                      <p className={`text-xl font-bold ${
                        status.status === "stable" ? "text-green-700" :
                        status.status === "warning" ? "text-amber-700" : "text-red-700"
                      }`}>{status.label}</p>
                      <p className="text-xs text-muted-foreground">{latestData?.hr ?? "--"} bpm</p>
                    </div>
                    <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                      {trend.direction === "up" ? <TrendingUp className="h-3 w-3" /> :
                       trend.direction === "down" ? <TrendingDown className="h-3 w-3" /> :
                       <Minus className="h-3 w-3" />}
                      <span>{trend.label}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Oxygen Stability */}
            {(() => {
              const status = getVitalStatus("spo2", latestData?.spo2);
              const desats = countDesatEvents();
              return (
                <Card className="shadow-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-purple-500" />
                        <span className="font-semibold text-sm">Oxygen</span>
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        status.status === "stable" ? "bg-green-500" :
                        status.status === "warning" ? "bg-amber-500" : "bg-red-500"
                      }`} />
                    </div>
                    <div className={`text-center py-3 rounded-lg mb-2 ${
                      status.status === "stable" ? "bg-green-100" :
                      status.status === "warning" ? "bg-amber-100" : "bg-red-100"
                    }`}>
                      <p className={`text-xl font-bold ${
                        status.status === "stable" ? "text-green-700" :
                        status.status === "warning" ? "text-amber-700" : "text-red-700"
                      }`}>{status.label}</p>
                      <p className="text-xs text-muted-foreground">{latestData?.spo2 ?? "--"}%</p>
                    </div>
                    <div className="text-center text-xs">
                      <span className="text-muted-foreground">Drops: </span>
                      <span className={desats.count > 3 ? "text-red-600 font-medium" : "text-slate-600"}>
                        {desats.count} ({desats.severe} severe)
                      </span>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Breathing */}
            {(() => {
              const status = getVitalStatus("rr", latestData?.rr);
              const trend = getTrend("rr");
              return (
                <Card className="shadow-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Wind className="h-5 w-5 text-blue-500" />
                        <span className="font-semibold text-sm">Breathing</span>
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        status.status === "stable" ? "bg-green-500" :
                        status.status === "warning" ? "bg-amber-500" : "bg-red-500"
                      }`} />
                    </div>
                    <div className={`text-center py-3 rounded-lg mb-2 ${
                      status.status === "stable" ? "bg-green-100" :
                      status.status === "warning" ? "bg-amber-100" : "bg-red-100"
                    }`}>
                      <p className={`text-xl font-bold ${
                        status.status === "stable" ? "text-green-700" :
                        status.status === "warning" ? "text-amber-700" : "text-red-700"
                      }`}>{status.label}</p>
                      <p className="text-xs text-muted-foreground">{latestData?.rr ?? "--"}/min</p>
                    </div>
                    <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                      {trend.direction === "up" ? <TrendingUp className="h-3 w-3" /> :
                       trend.direction === "down" ? <TrendingDown className="h-3 w-3" /> :
                       <Minus className="h-3 w-3" />}
                      <span>{trend.label}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Temperature */}
            {(() => {
              const status = getVitalStatus("temp", latestData?.temp);
              const trend = getTrend("temp");
              return (
                <Card className="shadow-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Thermometer className="h-5 w-5 text-orange-500" />
                        <span className="font-semibold text-sm">Temperature</span>
                      </div>
                      <div className={`w-3 h-3 rounded-full ${
                        status.status === "stable" ? "bg-green-500" :
                        status.status === "warning" ? "bg-amber-500" : "bg-red-500"
                      }`} />
                    </div>
                    <div className={`text-center py-3 rounded-lg mb-2 ${
                      status.status === "stable" ? "bg-green-100" :
                      status.status === "warning" ? "bg-amber-100" : "bg-red-100"
                    }`}>
                      <p className={`text-xl font-bold ${
                        status.status === "stable" ? "text-green-700" :
                        status.status === "warning" ? "text-amber-700" : "text-red-700"
                      }`}>{status.label}</p>
                      <p className="text-xs text-muted-foreground">{latestData?.temp?.toFixed(1) ?? "--"} C</p>
                    </div>
                    <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                      {trend.direction === "up" ? <TrendingUp className="h-3 w-3" /> :
                       trend.direction === "down" ? <TrendingDown className="h-3 w-3" /> :
                       <Minus className="h-3 w-3" />}
                      <span>{trend.label}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}
          </div>

          {/* Circulation Status */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Gauge className="h-4 w-4 text-green-500" />
                Blood Flow Strength
              </CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                const status = getVitalStatus("map", latestData?.map);
                const trend = getTrend("map");
                return (
                  <div className="flex items-center gap-4">
                    {/* Gauge Visual */}
                    <div className="flex-1">
                      <div className="h-3 rounded-full bg-slate-200 overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-500 ${
                            status.status === "stable" ? "bg-green-500" :
                            status.status === "warning" ? "bg-amber-500" : "bg-red-500"
                          }`}
                          style={{ width: latestData?.map ? `${Math.min(latestData.map * 1.5, 100)}%` : "0%" }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>Poor</span>
                        <span>Good</span>
                        <span>High</span>
                      </div>
                    </div>
                    {/* Status */}
                    <div className="text-center min-w-[100px]">
                      <p className={`text-lg font-bold ${
                        status.status === "stable" ? "text-green-600" :
                        status.status === "warning" ? "text-amber-600" : "text-red-600"
                      }`}>{status.label}</p>
                      <p className="text-xs text-muted-foreground">{latestData?.map ?? "--"} mmHg</p>
                      <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground mt-1">
                        {trend.direction === "up" ? <TrendingUp className="h-3 w-3" /> :
                         trend.direction === "down" ? <TrendingDown className="h-3 w-3" /> :
                         <Minus className="h-3 w-3" />}
                        <span>{trend.label}</span>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed View - Charts */}
      {viewMode === "detailed" && (
        <>
      {/* EOS Risk Score and Clinical Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {latestData && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">EOS Risk Score:</span>
                <span className={`text-lg font-bold px-3 py-1 rounded ${getStatusColor(latestData.status)}`}>
                  {latestData.risk_score.toFixed(2)}/1000
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Clinical Status:</span>
                <span className={`text-sm font-semibold px-2 py-1 rounded text-white ${
                  latestData.status === "HIGH_RISK" ? "bg-red-600" :
                  latestData.status === "ENHANCED_MONITORING" ? "bg-orange-500" :
                  latestData.status === "ROUTINE_CARE" ? "bg-green-600" : "bg-gray-500"
                }`}>
                  {latestData.status.replace("_", " ")}
                </span>
              </div>
            </div>
          )}
        </div>
        <button
          onClick={() => setShowChartSelector(!showChartSelector)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Customize Chart
        </button>
      </div>

      {/* EOS Risk Information Panel */}
      {latestData && (
        <Card className="shadow-sm border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <span className="w-5 h-5 bg-blue-600 text-white rounded flex items-center justify-center text-xs">EOS</span>
              Puopolo/Kaiser Early-Onset Sepsis Risk Calculator
              <a 
                href="https://www.mdcalc.com/calc/10528/neonatal-early-onset-sepsis-calculator?uuid=e367f52f-d7c7-4373-8d37-026457008847&utm_source=mdcalc"
                target="_blank" 
                rel="noopener noreferrer"
                className="ml-auto text-blue-600 hover:text-blue-800 text-xs"
                title="View on MDCalc"
              >
                Reference
              </a>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="p-2 rounded-lg bg-green-50 border border-green-200">
                <p className="font-bold text-green-800 mb-1">Low Risk (&lt;1/1000)</p>
                <p className="text-green-700">Routine newborn care</p>
              </div>
              <div className="p-2 rounded-lg bg-orange-50 border border-orange-200">
                <p className="font-bold text-orange-800 mb-1">Moderate Risk (1-3/1000)</p>
                <p className="text-orange-700">Enhanced monitoring</p>
              </div>
              <div className="p-2 rounded-lg bg-red-50 border border-red-200">
                <p className="font-bold text-red-800 mb-1">High Risk (≥3/1000)</p>
                <p className="text-red-700">Consider antibiotics</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chart Selector */}
      {showChartSelector && (
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Select Chart Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground mb-2">Time Series (Primary)</h4>
                <div className="grid grid-cols-3 gap-2">
                  {CHART_CONFIGS.filter((c) => c.category === "time-series").map((config) => (
                    <button
                      key={config.id}
                      onClick={() => { setSelectedChart(config.id); setShowChartSelector(false); }}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        selectedChart === config.id
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50 hover:bg-muted/50"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span style={{ color: config.color }}>{config.icon}</span>
                        <span className="font-medium text-sm">{config.name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{config.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Chart */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span style={{ color: currentConfig.color }}>{currentConfig.icon}</span>
              <CardTitle className="text-lg">{currentConfig.name}</CardTitle>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{currentConfig.description}</p>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            {data.length > 0 ? (
              renderChart()
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Waiting for live data...</p>
                  <p className="text-sm">Connect to WebSocket to see real-time vitals</p>
                </div>
              </div>
            )}
          </div>
          
          {/* Clinical Reference Ranges - Shown for all charts */}
          {currentConfig.ranges && data.length > 0 && (
            <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-2 mb-3">
                <span style={{ color: currentConfig.color }}>{currentConfig.icon}</span>
                <h4 className="text-sm font-semibold">Clinical Reference Ranges</h4>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Normal Range */}
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <p className="font-semibold text-green-800 text-sm">Normal Range</p>
                  </div>
                  <p className="text-green-700 text-sm font-medium">{currentConfig.ranges.normal}</p>
                </div>
                {/* Abnormal Ranges */}
                <div className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <p className="font-semibold text-slate-800 text-sm">Abnormal Values</p>
                  </div>
                  <div className="space-y-1">
                    {currentConfig.ranges.abnormal.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className={item.severity === "critical" ? "text-red-700 font-medium" : "text-amber-700 font-medium"}>
                          {item.label}
                        </span>
                        <span className={`px-2 py-0.5 rounded ${item.severity === "critical" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                          {item.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Combined Diagnostic Patterns Reference */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <span className="w-5 h-5 bg-slate-800 text-white rounded flex items-center justify-center text-xs">Rx</span>
            Combined Diagnostic Patterns
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-red-50 border border-red-200">
              <p className="font-bold text-red-800 mb-1">Apnea</p>
              <p className="text-red-700">HR &lt;100, SpO2 &lt;85, RR = 0</p>
            </div>
            <div className="p-3 rounded-lg bg-orange-50 border border-orange-200">
              <p className="font-bold text-orange-800 mb-1">Sepsis</p>
              <p className="text-orange-700">HR &gt;180, Temp &gt;38 or &lt;36, MAP low</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-50 border border-purple-200">
              <p className="font-bold text-purple-800 mb-1">Shock</p>
              <p className="text-purple-700">MAP &lt;30, HR &gt;180, SpO2 low</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <p className="font-bold text-blue-800 mb-1">Resp Distress</p>
              <p className="text-blue-700">RR &gt;70, SpO2 &lt;90</p>
            </div>
            <div className="p-3 rounded-lg bg-yellow-50 border border-yellow-200">
              <p className="font-bold text-yellow-800 mb-1">Thermal Instability</p>
              <p className="text-yellow-700">Temp swings &gt;0.5C</p>
            </div>
          </div>
        </CardContent>
      </Card>
        </>
      )}
    </div>
  );
}
