"use client";

import { useState, useEffect, useCallback } from 'react';

interface Alert {
  alert_id: number;
  baby_id: string;
  timestamp: string;
  model_risk_score: number;
  alert_status: string;
  doctor_action?: string;
}

export function useAlerts(role: 'doctor' | 'nurse', refreshInterval: number = 5000) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/alerts/pending?role=${role}`);
      
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
        setError(null);
      } else {
        setError('Failed to fetch alerts');
      }
    } catch (err) {
      setError('Error fetching alerts');
      console.error('Error fetching alerts:', err);
    } finally {
      setIsLoading(false);
    }
  }, [role]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchAlerts, refreshInterval]);

  return { alerts, isLoading, error, refetch: fetchAlerts };
}
