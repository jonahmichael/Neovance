"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Heart, Activity, Thermometer, Wind, Gauge, AlertTriangle, Clock, RefreshCw } from "lucide-react";

interface HistoryRecord {
  timestamp: string;
  mrn: string;
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
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchHistory = async () => {
    try {
      const response = await fetch("http://localhost:8000/history");
      if (!response.ok) throw new Error("Failed to fetch history");
      const data = await response.json();
      setHistory(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error("Error fetching history:", err);
      setError("Failed to load patient history. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusStyles = (status: string) => {
    switch (status) {
      case "OK":
        return "bg-green-100 text-green-700 border-green-200";
      case "WARNING":
        return "bg-yellow-100 text-yellow-700 border-yellow-200";
      case "CRITICAL":
        return "bg-red-100 text-red-700 border-red-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const getRiskColor = (score: number) => {
    if (score < 0.3) return "text-green-600";
    if (score < 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString("en-US", { 
        hour: "2-digit", 
        minute: "2-digit", 
        second: "2-digit",
        hour12: true 
      });
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <Card className="w-full shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl font-semibold flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Patient History
          </CardTitle>
          <CardDescription>Loading vitals from database...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full shadow-sm border-red-200">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl font-semibold flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Connection Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button 
            onClick={fetchHistory}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full shadow-sm">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-semibold flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Patient History
            </CardTitle>
            <CardDescription className="mt-1">
              Live vitals from database - Last 30 minutes ({history.length} records)
            </CardDescription>
          </div>
          {lastUpdated && (
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <RefreshCw className="h-3 w-3" />
              Updated {lastUpdated.toLocaleTimeString()}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {history.length === 0 ? (
          <div className="text-center py-12 border rounded-lg bg-muted/20">
            <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
            <p className="text-muted-foreground font-medium">No data available</p>
            <p className="text-sm text-muted-foreground mt-1">
              Start the Pathway simulator to stream vitals data
            </p>
          </div>
        ) : (
          <div className="rounded-lg border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="font-semibold">
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-4 w-4" />
                      Time
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    <div className="flex items-center justify-center gap-1.5">
                      <Heart className="h-4 w-4 text-red-500" />
                      HR
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    <div className="flex items-center justify-center gap-1.5">
                      <Activity className="h-4 w-4 text-purple-500" />
                      SpO2
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    <div className="flex items-center justify-center gap-1.5">
                      <Wind className="h-4 w-4 text-blue-500" />
                      RR
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    <div className="flex items-center justify-center gap-1.5">
                      <Thermometer className="h-4 w-4 text-orange-500" />
                      Temp
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    <div className="flex items-center justify-center gap-1.5">
                      <Gauge className="h-4 w-4 text-cyan-500" />
                      MAP
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    <div className="flex items-center justify-center gap-1.5">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      Risk
                    </div>
                  </TableHead>
                  <TableHead className="text-center font-semibold">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((record, index) => (
                  <TableRow 
                    key={index} 
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <TableCell className="font-medium text-sm">
                      {formatTime(record.timestamp)}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-semibold text-red-600">{record.hr.toFixed(0)}</span>
                      <span className="text-xs text-muted-foreground ml-1">bpm</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-semibold text-purple-600">{record.spo2.toFixed(1)}</span>
                      <span className="text-xs text-muted-foreground ml-1">%</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-semibold text-blue-600">{record.rr.toFixed(0)}</span>
                      <span className="text-xs text-muted-foreground ml-1">/min</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-semibold text-orange-600">{record.temp.toFixed(1)}</span>
                      <span className="text-xs text-muted-foreground ml-1">C</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-semibold text-cyan-600">{record.map.toFixed(0)}</span>
                      <span className="text-xs text-muted-foreground ml-1">mmHg</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className={`font-bold ${getRiskColor(record.risk_score)}`}>
                        {record.risk_score.toFixed(2)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span 
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusStyles(record.status)}`}
                      >
                        {record.status}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
