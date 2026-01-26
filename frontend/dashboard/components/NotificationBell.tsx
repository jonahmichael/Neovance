'use client';

import React, { useState } from 'react';
import { Bell, X, CheckCircle, AlertTriangle, Info, Clock } from 'lucide-react';
import { useNotifications, Notification } from '@/contexts/NotificationContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function NotificationBell() {
  const { notifications, unreadCount, getUnreadCriticalCount, markAsRead, markAsAcknowledged } = useNotifications();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  // Only show for nurses
  if (user?.role !== 'NURSE') {
    return null;
  }

  const criticalCount = getUnreadCriticalCount();

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'CRITICAL_ACTION':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      case 'SUCCESS':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      default:
        return <Info className="h-4 w-4 text-blue-600" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.isRead) {
      markAsRead(notification.id);
    }
  };

  const handleAcknowledge = (notification: Notification, e: React.MouseEvent) => {
    e.stopPropagation();
    markAsAcknowledged(notification.id);
  };

  return (
    <div className="relative">
      {/* Bell Icon */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-gray-100"
      >
        <Bell className="h-5 w-5 text-gray-600" />
        {unreadCount > 0 && (
          <Badge className={`absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center text-xs font-bold p-0 rounded-full border-2 border-white ${
            criticalCount > 0 ? 'bg-red-500' : 'bg-blue-500'
          } text-white`}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
        {criticalCount > 0 && (
          <div className="absolute -top-1 -right-1 h-3 w-3">
            <div className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></div>
          </div>
        )}
      </Button>

      {/* Dropdown Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          ></div>

          {/* Notification Panel */}
          <Card 
            className="absolute top-full right-0 mt-2 w-96 max-h-96 overflow-hidden z-50 shadow-lg border border-gray-200 bg-white"
          >
            <CardHeader className="pb-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg text-gray-900 font-sans">
                  Notifications
                </CardTitle>
                <div className="flex items-center gap-2">
                  {criticalCount > 0 && (
                    <Badge className="bg-red-500 text-white text-xs font-sans">
                      {criticalCount} Critical
                    </Badge>
                  )}
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setIsOpen(false)}
                    className="p-1 text-gray-500 hover:text-gray-700"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm font-sans">No notifications</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        onClick={() => handleNotificationClick(notification)}
                        className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                          !notification.isRead ? 'font-medium bg-blue-50' : 'bg-white'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {getNotificationIcon(notification.type)}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-sm text-gray-900 font-sans">
                                {notification.message}
                              </p>
                              <Badge className={`text-xs font-sans px-1.5 py-0.5 border ${
                                getPriorityColor(notification.details.priority)
                              }`}>
                                {notification.details.priority}
                              </Badge>
                            </div>
                            
                            <div className="text-xs text-gray-600 font-sans space-y-1">
                              <div>Patient: {notification.details.patient} ({notification.details.mrn})</div>
                              <div>Action: {notification.details.action}</div>
                              <div className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatTime(notification.timestamp)}
                              </div>
                            </div>

                            {notification.details.requiresAcknowledgment && !notification.isAcknowledged && (
                              <Button
                                size="sm"
                                onClick={(e) => handleAcknowledge(notification, e)}
                                className="mt-2 text-xs bg-red-500 hover:bg-red-600 text-white font-sans"
                              >
                                Acknowledge
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}