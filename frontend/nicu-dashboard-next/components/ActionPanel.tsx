"use client";

import { useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function ActionPanel() {
  const [patientId, setPatientId] = useState("Baby_A");
  const [action, setAction] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatus(null);

    try {
      const response = await axios.post("http://localhost:8000/action", {
        patient_id: patientId,
        action: action,
        notes: notes || null,
        timestamp: new Date().toISOString(),
      });

      if (response.data.success) {
        setStatus({
          type: "success",
          message: `Action logged successfully (ID: ${response.data.action_id})`,
        });
        setAction("");
        setNotes("");
      }
    } catch (error) {
      setStatus({
        type: "error",
        message: "Failed to log action. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">Clinical Action Log</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="patientId" className="text-sm font-medium text-muted-foreground block mb-2">
              Patient ID
            </label>
            <Input
              id="patientId"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="action" className="text-sm font-medium text-muted-foreground block mb-2">
              Action Taken
            </label>
            <Input
              id="action"
              placeholder="e.g., Oxygen adjusted to 30%"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="notes" className="text-sm font-medium text-muted-foreground block mb-2">
              Additional Notes
            </label>
            <Textarea
              id="notes"
              placeholder="Enter any additional observations..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isSubmitting}
              rows={4}
            />
          </div>

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Log Action"}
          </Button>

          {status && (
            <div
              className={`p-3 rounded-md text-sm ${
                status.type === "success"
                  ? "bg-green-900/30 text-green-400 border border-green-900"
                  : "bg-red-900/30 text-red-400 border border-red-900"
              }`}
            >
              {status.message}
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
