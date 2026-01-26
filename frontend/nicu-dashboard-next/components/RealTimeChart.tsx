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
  risk_score: number;
  status: string;
}

export default function RealTimeChart() {
  const [data, setData] = useState<VitalData[]>([]);
  const [latestData, setLatestData] = useState<VitalData | null>(null);
  const [wsStatus, setWsStatus] = useState<string>("Connecting...");

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
          return updated.slice(-30);
        });
      };

      ws.onerror = () => {
        setWsStatus("Connection Error");
      };

      ws.onclose = () => {
        setWsStatus("Disconnected - Reconnecting...");
        reconnectTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const chartData = {
    labels: data.map((d) => {
      const time = new Date(d.timestamp);
      return time.toLocaleTimeString();
    }),
    datasets: [
      {
        label: "Heart Rate",
        data: data.map((d) => d.hr),
        borderColor: "rgb(34, 211, 238)",
        backgroundColor: "rgba(34, 211, 238, 0.1)",
        tension: 0.4,
        fill: true,
        yAxisID: "y",
      },
      {
        label: "SpO2",
        data: data.map((d) => d.spo2),
        borderColor: "rgb(167, 139, 250)",
        backgroundColor: "rgba(167, 139, 250, 0.1)",
        tension: 0.4,
        fill: true,
        yAxisID: "y1",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index" as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: "top" as const,
        labels: {
          color: "rgb(226, 232, 240)",
          font: {
            size: 12,
          },
          usePointStyle: true,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "rgb(148, 163, 184)",
          maxRotation: 45,
          minRotation: 0,
        },
        grid: {
          color: "rgba(148, 163, 184, 0.1)",
        },
      },
      y: {
        type: "linear" as const,
        display: true,
        position: "left" as const,
        title: {
          display: true,
          text: "Heart Rate (bpm)",
          color: "rgb(34, 211, 238)",
        },
        ticks: {
          color: "rgb(148, 163, 184)",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.1)",
        },
      },
      y1: {
        type: "linear" as const,
        display: true,
        position: "right" as const,
        title: {
          display: true,
          text: "SpO2 (%)",
          color: "rgb(167, 139, 250)",
        },
        ticks: {
          color: "rgb(148, 163, 184)",
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "OK":
        return "text-green-400";
      case "WARNING":
        return "text-yellow-400";
      case "CRITICAL":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">Live Vital Signs Monitor</CardTitle>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{wsStatus}</span>
            {latestData && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Risk Score:
                </span>
                <span className={`text-lg font-bold ${getStatusColor(latestData.status)}`}>
                  {latestData.risk_score.toFixed(2)}
                </span>
                <span className={`text-sm font-medium px-2 py-1 rounded ${
                  latestData.status === "OK" ? "bg-green-900/30" :
                  latestData.status === "WARNING" ? "bg-yellow-900/30" :
                  "bg-red-900/30"
                } ${getStatusColor(latestData.status)}`}>
                  {latestData.status}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[400px]">
          <Line data={chartData} options={options} />
        </div>
        {latestData && (
          <div className="mt-6 grid grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">Heart Rate</div>
              <div className="text-2xl font-bold text-cyan-400">{latestData.hr}</div>
              <div className="text-xs text-muted-foreground">bpm</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">SpO2</div>
              <div className="text-2xl font-bold text-purple-400">{latestData.spo2}</div>
              <div className="text-xs text-muted-foreground">%</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">Resp Rate</div>
              <div className="text-2xl font-bold">{data[data.length - 1]?.hr || "--"}</div>
              <div className="text-xs text-muted-foreground">breaths/min</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">Temperature</div>
              <div className="text-2xl font-bold">{"--"}</div>
              <div className="text-xs text-muted-foreground">°C</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">MAP</div>
              <div className="text-2xl font-bold">{"--"}</div>
              <div className="text-xs text-muted-foreground">mmHg</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
