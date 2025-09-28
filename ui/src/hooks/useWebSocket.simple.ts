import { useState, useEffect, useCallback, useRef } from 'react';

export interface UseWebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
  lastMessage: any;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'failed';
}

export interface UseWebSocketOptions {
  onStatusUpdate?: (statusData: any) => void;
  onConnectionChange?: (isConnected: boolean) => void;
  onError?: (error: string) => void;
  onReconnectAttempt?: (attempt: number, maxAttempts: number) => void;
  onReconnectFailed?: () => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [state, setState] = useState<UseWebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
    lastMessage: null,
    connectionStatus: 'disconnected',
  });

  const connect = useCallback((jobId: string) => {
    console.log('WebSocket connect called with jobId:', jobId);
    // Simplified implementation - just log for now
    setState(prev => ({ ...prev, isConnecting: true, connectionStatus: 'connecting' }));
    
    // Simulate connection
    setTimeout(() => {
      setState(prev => ({ ...prev, isConnected: true, isConnecting: false, connectionStatus: 'connected' }));
      options.onConnectionChange?.(true);
    }, 1000);
  }, [options]);

  const disconnect = useCallback(() => {
    console.log('WebSocket disconnect called');
    setState(prev => ({ ...prev, isConnected: false, connectionStatus: 'disconnected' }));
    options.onConnectionChange?.(false);
  }, [options]);

  const sendMessage = useCallback((message: any) => {
    console.log('WebSocket sendMessage called:', message);
    return Promise.resolve(true);
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
  };
}

// Simplified research WebSocket hook
export function useResearchWebSocket(options: UseWebSocketOptions = {}) {
  const webSocket = useWebSocket(options);
  
  const connectToJob = useCallback((jobId: string) => {
    console.log('Connecting to research job WebSocket:', jobId);
    webSocket.connect(jobId);
  }, [webSocket]);

  const sendHeartbeat = useCallback(() => {
    return webSocket.sendMessage({ type: 'heartbeat', timestamp: Date.now() });
  }, [webSocket]);

  return {
    ...webSocket,
    connectToJob,
    sendHeartbeat,
  };
}