"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface HistoryRecord {
  timestamp: string;
  hr: number;
  spo2: number;
  rr: number;
  temp: number;
  map: number;
  risk_score: number;
  status: string;
}

export default function PatientHistory() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    try {
      const response = await axios.get("http://localhost:8000/history?minutes=30");
      setHistory(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching history:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    const colors = {
      OK: "bg-green-900/30 text-green-400 border-green-900",
      WARNING: "bg-yellow-900/30 text-yellow-400 border-yellow-900",
      CRITICAL: "bg-red-900/30 text-red-400 border-red-900",
    };
    return colors[status as keyof typeof colors] || "bg-gray-900/30 text-gray-400 border-gray-900";
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-12 text-center">
          <div className="text-muted-foreground">Loading patient history...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">Patient History - Last 30 Minutes</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-3 text-sm font-medium text-muted-foreground">Time</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">HR</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">SpO2</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">RR</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">Temp</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">MAP</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">Risk</th>
                <th className="text-center p-3 text-sm font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((record, index) => (
                <tr key={index} className="border-b border-border hover:bg-muted/50 transition-colors">
                  <td className="p-3 text-sm">
                    {new Date(record.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="p-3 text-sm text-center text-cyan-400 font-medium">{record.hr}</td>
                  <td className="p-3 text-sm text-center text-purple-400 font-medium">{record.spo2}</td>
                  <td className="p-3 text-sm text-center">{record.rr}</td>
                  <td className="p-3 text-sm text-center">{record.temp.toFixed(1)}</td>
                  <td className="p-3 text-sm text-center">{record.map}</td>
                  <td className="p-3 text-sm text-center font-medium">
                    {record.risk_score.toFixed(2)}
                  </td>
                  <td className="p-3 text-center">
                    <span className={`inline-block px-2 py-1 text-xs font-medium rounded border ${getStatusBadge(record.status)}`}>
                      {record.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {history.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              No data available for the last 30 minutes
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
