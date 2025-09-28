import { useState, useEffect, useCallback } from 'react';
import { authService, apiService } from '../services';
import type { AuthState } from '../services/auth';

export interface SessionInfo {
  sessionId: string | null;
  isAuthenticated: boolean;
  lastActivity: Date | null;
  connectionStatus: 'connected' | 'disconnected' | 'checking';
}

export interface UseSessionOptions {
  checkInterval?: number;
  onSessionExpired?: () => void;
  onConnectionLost?: () => void;
  onConnectionRestored?: () => void;
}

export function useSession(options: UseSessionOptions = {}) {
  const {
    checkInterval = 60000, // Check every minute
    onSessionExpired,
    onConnectionLost,
    onConnectionRestored,
  } = options;

  const [sessionInfo, setSessionInfo] = useState<SessionInfo>({
    sessionId: null,
    isAuthenticated: false,
    lastActivity: null,
    connectionStatus: 'checking',
  });

  const [authState, setAuthState] = useState<AuthState>(authService.getAuthState());

  // Update session info when auth state changes
  useEffect(() => {
    const unsubscribe = authService.subscribe((newAuthState) => {
      setAuthState(newAuthState);
      setSessionInfo(prev => ({
        ...prev,
        sessionId: newAuthState.sessionId,
        isAuthenticated: newAuthState.isAuthenticated,
      }));
    });

    return unsubscribe;
  }, []);

  // Check session status
  const checkSession = useCallback(async () => {
    try {
      setSessionInfo(prev => ({ ...prev, connectionStatus: 'checking' }));
      
      const response = await apiService.getSessionInfo();
      
      if (response.success && response.data) {
        const wasConnected = sessionInfo.connectionStatus === 'connected';
        
        setSessionInfo(prev => ({
          ...prev,
          sessionId: response.data!.sessionId,
          isAuthenticated: response.data!.isAuthenticated,
          lastActivity: new Date(),
          connectionStatus: 'connected',
        }));

        // Notify if connection was restored
        if (!wasConnected && sessionInfo.connectionStatus !== 'checking') {
          onConnectionRestored?.();
        }

        return true;
      } else {
        throw new Error('Session check failed');
      }
    } catch (error) {
      console.error('Session check failed:', error);
      
      const wasConnected = sessionInfo.connectionStatus === 'connected';
      
      setSessionInfo(prev => ({
        ...prev,
        connectionStatus: 'disconnected',
      }));

      // Notify if connection was lost
      if (wasConnected) {
        onConnectionLost?.();
      }

      return false;
    }
  }, [sessionInfo.connectionStatus, onConnectionLost, onConnectionRestored]);

  // Refresh session
  const refreshSession = useCallback(async () => {
    try {
      const result = await authService.refreshToken();
      if (result.success) {
        await checkSession();
        return true;
      } else {
        onSessionExpired?.();
        return false;
      }
    } catch (error) {
      console.error('Session refresh failed:', error);
      onSessionExpired?.();
      return false;
    }
  }, [checkSession, onSessionExpired]);

  // Update last activity
  const updateActivity = useCallback(() => {
    setSessionInfo(prev => ({
      ...prev,
      lastActivity: new Date(),
    }));
  }, []);

  // Set up periodic session checks
  useEffect(() => {
    // Initial check
    checkSession();

    // Set up interval
    const interval = setInterval(checkSession, checkInterval);

    return () => clearInterval(interval);
  }, [checkSession, checkInterval]);

  // Set up activity tracking
  useEffect(() => {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    
    const handleActivity = () => {
      updateActivity();
    };

    events.forEach(event => {
      document.addEventListener(event, handleActivity, true);
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity, true);
      });
    };
  }, [updateActivity]);

  return {
    sessionInfo,
    authState,
    checkSession,
    refreshSession,
    updateActivity,
    isSessionValid: sessionInfo.isAuthenticated && sessionInfo.connectionStatus === 'connected',
  };
}