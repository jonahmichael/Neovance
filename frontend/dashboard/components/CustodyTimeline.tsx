"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileEdit, UserCheck, Lock, Clock } from "lucide-react";

interface CustodyChange {
  field: string;
  old_value: any;
  new_value: any;
}

interface CustodyEntry {
  block_index: number;
  timestamp: string;
  user_id: string;
  action: string;
  baby_mrn: string;
  changes: Record<string, CustodyChange>;
  previous_hash: string;
  current_hash: string;
}

export default function CustodyTimeline({ mrn = "B001" }: { mrn?: string }) {
  const [entries, setEntries] = useState<CustodyEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCustodyLog();
  }, [mrn]);

  const fetchCustodyLog = async () => {
    try {
      // For now, read from the file - we'll create an endpoint later
      const response = await axios.get(`http://localhost:8000/custody-log/${mrn}`);
      const data = response.data;
      setEntries(Array.isArray(data.entries) ? data.entries : Array.isArray(data) ? data : []);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching custody log:", error);
      // If endpoint doesn't exist, use empty array for now
      setEntries([]);
      setLoading(false);
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case "CREATE":
        return "text-blue-400 bg-blue-900/20 border-blue-900";
      case "UPDATE":
        return "text-green-400 bg-green-900/20 border-green-900";
      case "DELETE":
        return "text-red-400 bg-red-900/20 border-red-900";
      default:
        return "text-gray-400 bg-gray-900/20 border-gray-900";
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "CREATE":
        return <FileEdit className="h-4 w-4" />;
      case "UPDATE":
        return <FileEdit className="h-4 w-4" />;
      case "DELETE":
        return <FileEdit className="h-4 w-4" />;
      default:
        return <FileEdit className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-12 text-center">
          <div className="text-muted-foreground">Loading chain of custody...</div>
        </CardContent>
      </Card>
    );
  }

  if (entries.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Chain of Custody</CardTitle>
        </CardHeader>
        <CardContent className="p-12 text-center">
          <Lock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <div className="text-muted-foreground">No audit trail entries yet</div>
          <div className="text-xs text-muted-foreground mt-2">
            All changes to patient records will be logged here
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Chain of Custody</h2>
        <div className="text-sm text-muted-foreground">
          {entries.length} {entries.length === 1 ? "entry" : "entries"}
        </div>
      </div>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border" />

        <div className="space-y-6">
          {entries
            .sort((a, b) => b.block_index - a.block_index)
            .map((entry) => (
              <div key={entry.block_index} className="relative pl-16">
                {/* Timeline dot */}
                <div
                  className={`absolute left-4 top-3 w-4 h-4 rounded-full border-2 ${getActionColor(
                    entry.action
                  )}`}
                />

                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${getActionColor(entry.action)}`}>
                          {getActionIcon(entry.action)}
                        </div>
                        <div>
                          <div className="font-semibold">{entry.action}</div>
                          <div className="text-sm text-muted-foreground">
                            Block #{entry.block_index}
                          </div>
                        </div>
                      </div>
                      <div className={`text-xs px-2 py-1 rounded border ${getActionColor(entry.action)}`}>
                        {entry.action}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {/* Metadata */}
                      <div className="grid grid-cols-3 gap-4 text-sm pb-3 border-b border-border">
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-muted-foreground text-xs">Timestamp</div>
                            <div className="font-medium">
                              {new Date(entry.timestamp).toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <UserCheck className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-muted-foreground text-xs">User</div>
                            <div className="font-medium">{entry.user_id}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <FileEdit className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="text-muted-foreground text-xs">Patient MRN</div>
                            <div className="font-medium">{entry.baby_mrn}</div>
                          </div>
                        </div>
                      </div>

                      {/* Changes */}
                      {Object.keys(entry.changes).length > 0 && (
                        <div>
                          <div className="text-sm font-semibold mb-2">Changes Made:</div>
                          <div className="space-y-2">
                            {Object.entries(entry.changes).map(([field, change]) => (
                              <div
                                key={field}
                                className="text-sm bg-muted/30 rounded p-2 border border-border"
                              >
                                <div className="font-medium text-cyan-400">{field}</div>
                                <div className="mt-1 space-y-1">
                                  <div className="flex items-start gap-2">
                                    <span className="text-red-400 text-xs">Old:</span>
                                    <span className="text-muted-foreground text-xs">
                                      {change.old_value === null
                                        ? "—"
                                        : String(change.old_value)}
                                    </span>
                                  </div>
                                  <div className="flex items-start gap-2">
                                    <span className="text-green-400 text-xs">New:</span>
                                    <span className="text-xs">
                                      {change.new_value === null
                                        ? "—"
                                        : String(change.new_value)}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Hash verification */}
                      <div className="pt-3 border-t border-border">
                        <div className="flex items-center gap-2 mb-2">
                          <Lock className="h-4 w-4 text-muted-foreground" />
                          <div className="text-xs font-semibold">Cryptographic Verification</div>
                        </div>
                        <div className="space-y-1 text-xs font-mono">
                          <div className="flex gap-2">
                            <span className="text-muted-foreground">Prev:</span>
                            <span className="text-muted-foreground break-all">
                              {entry.previous_hash}
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-muted-foreground">Hash:</span>
                            <span className="text-cyan-400 break-all">{entry.current_hash}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
