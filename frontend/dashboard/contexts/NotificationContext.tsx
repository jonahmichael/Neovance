'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface Notification {
  id: string;
  type: 'CRITICAL_ACTION' | 'INFO' | 'WARNING' | 'SUCCESS';
  message: string;
  details: {
    doctor: string;
    doctorId: string;
    patient: string;
    mrn: string;
    action: string;
    actionDetails?: any;
    timestamp: string;
    priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
    requiresAcknowledgment?: boolean;
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
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

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
      getUnreadCriticalCount
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