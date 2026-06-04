/**
 * Offline queue — port from lib/offline-queue.ts
 *
 * Queues failed API requests in localStorage and retries them when
 * the connection is restored. Same parameters: 5s heartbeat, 3 retries.
 * Changed: heartbeat URL from /api/bootstrap to FastAPI /v1/health.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface QueuedRequest {
  id: string;
  url: string;
  options: RequestInit;
  timestamp: number;
  retries: number;
  localEventId?: string;
}

const MAX_RETRIES = 3;
const QUEUE_KEY = 'offline_queue';
const HEARTBEAT_INTERVAL = 5000;

class OfflineQueue {
  private queue: QueuedRequest[] = [];
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private isOnline = true;
  private processing = false;

  constructor() {
    if (typeof window === 'undefined') return;
    this.isOnline = navigator.onLine;
    this.loadQueue();
    this.setupListeners();
    this.startHeartbeat();
  }

  private loadQueue() {
    try {
      const stored = localStorage.getItem(QUEUE_KEY);
      if (stored) this.queue = JSON.parse(stored);
    } catch {
      this.queue = [];
    }
  }

  private saveQueue() {
    try {
      localStorage.setItem(QUEUE_KEY, JSON.stringify(this.queue));
    } catch {
      // Storage full or unavailable
    }
  }

  private setupListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processQueue();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });

    // Warn before unload if queue has items
    window.addEventListener('beforeunload', (e) => {
      if (this.queue.length > 0) {
        e.preventDefault();
        e.returnValue = 'Masz niesynchronizowane dane. Czy na pewno chcesz opuścić stronę?';
      }
    });

    // Listen for queue processed event to refresh UI
    window.addEventListener('queueProcessed', () => {
      // Components can listen for this to refresh data
    });
  }

  private startHeartbeat() {
    this.heartbeatTimer = setInterval(async () => {
      const wasOnline = this.isOnline;

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        await fetch(`${API_URL}/v1/health`, {
          method: 'HEAD',
          cache: 'no-store',
          signal: controller.signal,
        });

        clearTimeout(timeoutId);
        this.isOnline = true;

        if (this.isOnline && this.queue.length > 0) {
          this.processQueue();
        }
      } catch {
        this.isOnline = false;
      }
    }, HEARTBEAT_INTERVAL);
  }

  /**
   * Fetch wrapper — tries the request, queues it on failure.
   * Throws an error with `queued: true` if the request was queued.
   */
  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    const cacheBustUrl = `${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}`;

    try {
      const response = await fetch(cacheBustUrl, {
        ...options,
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
          ...options.headers,
        },
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      this.isOnline = true;
      if (this.queue.length > 0) this.processQueue();

      return response;
    } catch (error: any) {
      this.isOnline = false;

      const queuedRequest: QueuedRequest = {
        id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        url: cacheBustUrl,
        options,
        timestamp: Date.now(),
        retries: 0,
      };

      this.queue.push(queuedRequest);
      this.saveQueue();

      const enhancedError = error as Error & { queued: boolean };
      enhancedError.queued = true;
      throw enhancedError;
    }
  }

  /**
   * Add a request directly to the queue with a local event ID.
   * Used for offline event recording with immediate local feedback.
   */
  addToQueueWithLocalId(
    url: string,
    options: RequestInit,
    localEventId: string,
  ): string {
    const requestId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    this.queue.push({
      id: requestId,
      url,
      options,
      timestamp: Date.now(),
      retries: 0,
      localEventId,
    });
    this.saveQueue();
    return requestId;
  }

  /**
   * Remove queued requests containing a specific event ID.
   * Used when deleting an offline event before it syncs.
   */
  removeFromQueue(eventId: string) {
    const before = this.queue.length;
    this.queue = this.queue.filter((request) => {
      if (request.localEventId === eventId) return false;
      try {
        const body = JSON.parse((request.options.body as string) || '{}');
        return body.eventId !== eventId && body.events?.[0]?.id !== eventId;
      } catch {
        return true;
      }
    });
    if (this.queue.length < before) this.saveQueue();
  }

  private async processQueue() {
    if (!this.isOnline || this.queue.length === 0 || this.processing) return;
    this.processing = true;

    const processed: string[] = [];

    for (const request of this.queue) {
      try {
        const response = await fetch(request.url, {
          ...request.options,
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache',
            ...request.options.headers,
          },
        });

        if (response.ok) {
          processed.push(request.id);
        } else {
          request.retries++;
          if (request.retries >= MAX_RETRIES) processed.push(request.id);
        }
      } catch {
        request.retries++;
        if (request.retries >= MAX_RETRIES) processed.push(request.id);
      }
    }

    this.queue = this.queue.filter((req) => !processed.includes(req.id));
    this.saveQueue();
    this.processing = false;

    if (processed.length > 0) {
      window.dispatchEvent(
        new CustomEvent('queueProcessed', { detail: { count: processed.length } }),
      );
    }
  }

  getConnectionStatus(): 'online' | 'offline' {
    return this.isOnline ? 'online' : 'offline';
  }

  getQueueLength(): number {
    return this.queue.length;
  }

  clearQueue() {
    this.queue = [];
    this.saveQueue();
  }

  destroy() {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
  }
}

// Singleton
let instance: OfflineQueue | null = null;

export function getOfflineQueue(): OfflineQueue {
  if (!instance) {
    instance = new OfflineQueue();
  }
  return instance;
}
