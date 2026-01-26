'use client';

import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useAuth } from './AuthContext';

export interface Notification {
  id: string;
  type: 'CRITICAL_ACTION' | 'INFO' | 'WARNING' | 'SUCCESS' | 'SEPSIS_ALERT';
  message: string;
  details: {
    doctor?: string;
    doctorId?: string;
    patient?: string;
    mrn: string;
    action?: string;
    actionDetails?: any;
    timestamp: string;
    priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
    requiresAcknowledgment?: boolean;
    alertId?: number;
    riskScore?: number;
    doctorAction?: string;
    observationDuration?: string;
    labTests?: string[];
    antibiotics?: string[];
  };
  timestamp: string;
  isRead: boolean;
  isAcknowledged: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'isRead' | 'isAcknowledged'>) => void;
  markAsRead: (id: string) => void;
  markAsAcknowledged: (id: string) => void;
  clearAll: () => void;
  getUnreadCriticalCount: () => number;
  activeSepsisAlert: any | null;
  setActiveSepsisAlert: (alert: any | null) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [activeSepsisAlert, setActiveSepsisAlert] = useState<any | null>(null);
  const { user } = useAuth();
  const lastAlertIds = useRef<Set<number>>(new Set());

  // Polling for sepsis alerts
  useEffect(() => {
    if (!user || !user.isLoggedIn) return;

    const pollAlerts = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/alerts/pending?role=${user.role?.toLowerCase() || 'nurse'}`, {
          signal: AbortSignal.timeout(3000)
        });
        if (!response.ok) throw new Error('Backend unavailable');
        
        const pendingAlerts = await response.json();
        
        pendingAlerts.forEach((alert: any) => {
          // Only add if we haven't seen this specific alert ID recently
          if (!lastAlertIds.current.has(alert.alert_id)) {
            const isDoctor = user.role === 'DOCTOR';
            
            addNotification({
              type: isDoctor ? 'SEPSIS_ALERT' : 'CRITICAL_ACTION',
              message: isDoctor 
                ? `High Sepsis Risk Alert for MRN: ${alert.baby_id}` 
                : `Doctor Action Required for MRN: ${alert.baby_id}`,
              details: {
                mrn: alert.baby_id,
                alertId: alert.alert_id,
                priority: 'URGENT',
                riskScore: alert.model_risk_score,
                timestamp: alert.timestamp,
                doctorAction: alert.doctor_action,
                observationDuration: alert.observation_duration,
                labTests: alert.lab_tests,
                antibiotics: alert.antibiotics
              },
              timestamp: new Date().toISOString()
            });
            
            lastAlertIds.current.add(alert.alert_id);
          }
        });
      } catch (err) {
        // Continue silently without notifications when backend is unavailable
      }
    };

    const interval = setInterval(pollAlerts, 5000);
    pollAlerts(); // Initial call
    
    return () => clearInterval(interval);
  }, [user]);

  const addNotification = (notification: Omit<Notification, 'id' | 'isRead' | 'isAcknowledged'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      isRead: false,
      isAcknowledged: false
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    
    // Auto-remove non-critical notifications after 10 seconds
    if (notification.type !== 'CRITICAL_ACTION') {
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
      }, 10000);
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, isRead: true } : n)
    );
  };

  const markAsAcknowledged = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, isAcknowledged: true } : n)
    );
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.isRead).length;
  
  const getUnreadCriticalCount = () => {
    return notifications.filter(n => !n.isRead && n.type === 'CRITICAL_ACTION').length;
  };

  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      addNotification,
      markAsRead,
      markAsAcknowledged,
      clearAll,
      getUnreadCriticalCount,
      activeSepsisAlert,
      setActiveSepsisAlert
    }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}