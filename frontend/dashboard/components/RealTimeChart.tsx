"use client";

import { useEffect, useState, useRef } from "react";
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
  TimeScale,
} from "chart.js";
import "chartjs-adapter-luxon";
import ChartStreaming from "chartjs-plugin-streaming";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale,
  ChartStreaming
);

interface VitalData {
  timestamp: string;
  hr: number;
  spo2: number;
  risk_score: number;
  status: string;
}

export default function RealTimeChart() {
  const [latestData, setLatestData] = useState<VitalData | null>(null);
  const [wsStatus, setWsStatus] = useState<string>("Connecting...");
  const chartRef = useRef<ChartJS<"line">>(null);

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

        if (chartRef.current) {
          chartRef.current.data.datasets[0].data.push({
            x: new Date(newData.timestamp).valueOf(),
            y: newData.hr,
          });
          chartRef.current.data.datasets[1].data.push({
            x: new Date(newData.timestamp).valueOf(),
            y: newData.spo2,
          });
          chartRef.current.update("quiet");
        }
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
    datasets: [
      {
        label: "Heart Rate",
        borderColor: "rgb(34, 211, 238)",
        backgroundColor: "rgba(34, 211, 238, 0.1)",
        tension: 0.4,
        fill: true,
        data: [],
        yAxisID: "y",
      },
      {
        label: "SpO2",
        borderColor: "rgb(167, 139, 250)",
        backgroundColor: "rgba(167, 139, 250, 0.1)",
        tension: 0.4,
        fill: true,
        data: [],
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
      streaming: {
        frameRate: 30,
      },
    },
    scales: {
      x: {
        type: "realtime" as const,
        realtime: {
          duration: 60000, // 60 seconds
          refresh: 1000, // 1 second
          delay: 2000, // 2 seconds
          onRefresh: (chart: ChartJS) => {
            // The chart will automatically scroll
          },
        },
        ticks: {
          color: "rgb(148, 163, 184)",
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
        min: 60,
        max: 220,
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
        min: 80,
        max: 100,
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
          <Line ref={chartRef} data={chartData} options={options as any} />
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
              <div className="text-2xl font-bold">
                {latestData?.hr ? Math.round(latestData.hr) : "--"}
              </div>
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
