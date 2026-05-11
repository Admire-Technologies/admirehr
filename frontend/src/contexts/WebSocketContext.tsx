/**
 * WebSocket context for managing real-time connections across the application.
 */

'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import {
  WebSocketClient,
  WebSocketClients,
  createWebSocketClients,
  WebSocketEventType,
  AttendanceUpdateData,
  LeaveStatusChangeData,
  DashboardMetricsData,
  NotificationData,
} from '@/lib/websocket';

interface WebSocketContextValue {
  clients: WebSocketClients | null;
  isConnected: boolean;
  connect: (token: string) => void;
  disconnect: () => void;
  subscribe: <T = any>(
    endpoint: keyof WebSocketClients,
    eventType: WebSocketEventType,
    handler: (data: T) => void
  ) => () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | undefined>(undefined);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [clients, setClients] = useState<WebSocketClients | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const clientsRef = useRef<WebSocketClients | null>(null);
  const connectionStates = useRef<Record<string, boolean>>({});

  /**
   * Initialize WebSocket clients.
   */
  useEffect(() => {
    const wsClients = createWebSocketClients();
    setClients(wsClients);
    clientsRef.current = wsClients;

    // Subscribe to connection state changes for all clients
    const unsubscribers = Object.entries(wsClients).map(([key, client]) => {
      return client.onConnectionStateChange((connected) => {
        connectionStates.current[key] = connected;
        
        // Update overall connection state
        const anyConnected = Object.values(connectionStates.current).some(state => state);
        setIsConnected(anyConnected);
      });
    });

    return () => {
      // Cleanup: disconnect all clients and unsubscribe
      unsubscribers.forEach(unsub => unsub());
      Object.values(wsClients).forEach(client => client.disconnect());
    };
  }, []);

  /**
   * Connect all WebSocket clients with token.
   */
  const connect = useCallback((token: string) => {
    if (!clientsRef.current) return;

    Object.values(clientsRef.current).forEach(client => {
      client.connect(token);
    });
  }, []);

  /**
   * Disconnect all WebSocket clients.
   */
  const disconnect = useCallback(() => {
    if (!clientsRef.current) return;

    Object.values(clientsRef.current).forEach(client => {
      client.disconnect();
    });

    setIsConnected(false);
  }, []);

  /**
   * Subscribe to WebSocket events.
   */
  const subscribe = useCallback(
    <T = any>(
      endpoint: keyof WebSocketClients,
      eventType: WebSocketEventType,
      handler: (data: T) => void
    ) => {
      if (!clientsRef.current) {
        return () => {};
      }

      const client = clientsRef.current[endpoint];
      return client.on<T>(eventType, handler);
    },
    []
  );

  const value: WebSocketContextValue = {
    clients,
    isConnected,
    connect,
    disconnect,
    subscribe,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

/**
 * Hook to access WebSocket context.
 */
export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  
  return context;
};

/**
 * Hook to subscribe to specific WebSocket events.
 */
export const useWebSocketEvent = <T = any>(
  endpoint: keyof WebSocketClients,
  eventType: WebSocketEventType,
  handler: (data: T) => void,
  deps: React.DependencyList = []
) => {
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe<T>(endpoint, eventType, handler);
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, eventType, subscribe, ...deps]);
};

/**
 * Hook for attendance updates.
 */
export const useAttendanceUpdates = (handler: (data: AttendanceUpdateData) => void) => {
  useWebSocketEvent<AttendanceUpdateData>('attendance', 'attendance.update', handler);
};

/**
 * Hook for leave status changes.
 */
export const useLeaveStatusChanges = (handler: (data: LeaveStatusChangeData) => void) => {
  useWebSocketEvent<LeaveStatusChangeData>('leave', 'leave.status_change', handler);
};

/**
 * Hook for dashboard metrics updates.
 */
export const useDashboardMetrics = (handler: (data: DashboardMetricsData) => void) => {
  useWebSocketEvent<DashboardMetricsData>('dashboard', 'dashboard.metrics_update', handler);
};

/**
 * Hook for notifications.
 */
export const useNotifications = (handler: (data: NotificationData) => void) => {
  useWebSocketEvent<NotificationData>('notifications', 'notification', handler);
};
