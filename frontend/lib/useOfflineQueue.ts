import { useEffect, useState, useCallback } from 'react';
import { getOfflineQueue } from './offline-queue';

export function useOfflineQueue() {
  const [connectionStatus, setConnectionStatus] = useState<'online' | 'offline'>('online');
  const [queuedRequests, setQueuedRequests] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const queue = getOfflineQueue();

    const updateStatus = () => {
      setConnectionStatus(queue.getConnectionStatus());
      setQueuedRequests(queue.getQueueLength());
    };

    // Poll status every second (lightweight — just reads cached state)
    const interval = setInterval(updateStatus, 1000);

    // Listen for queue sync
    const handleSync = () => {
      updateStatus();
    };
    window.addEventListener('queueProcessed', handleSync);

    updateStatus();

    return () => {
      clearInterval(interval);
      window.removeEventListener('queueProcessed', handleSync);
    };
  }, []);

  const manualSync = useCallback(() => {
    const queue = getOfflineQueue();
    // Force process queue by triggering online event
    (queue as any).processQueue?.();
  }, []);

  return { connectionStatus, queuedRequests, manualSync };
}
