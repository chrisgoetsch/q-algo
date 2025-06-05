import { useEffect, useRef, useState } from 'react';

export interface WSMessage {
  data: string;
}

/**
 * Generic WebSocket hook with exponential-jitter back-off.
 * Automatically reconnects up to a 60-second delay and
 * cleans up listeners on unmount / hot reload.
 */
export default function useWebSocket(
  path: string,
  onMessage?: (event: MessageEvent) => void
) {
  const [ready, setReady] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!path) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${protocol}://${window.location.host}${path}`;

    const MAX_DELAY = 60_000; // cap back-off at 60 s

    const connect = (retry = 0) => {
      const delay = Math.min(2_500 * Math.max(retry, 1), MAX_DELAY);

      socket.current = new WebSocket(url);

      socket.current.onopen = () => {
        setReady(true);
        retry = 0; // reset counter on success
      };

      socket.current.onmessage = (e) => {
        setLastMessage({ data: e.data });
        onMessage?.(e);
      };

      socket.current.onerror = (err) => {
        // eslint-disable-next-line no-console
        console.error('[WebSocket error]', err);
      };

      socket.current.onclose = () => {
        setReady(false);
        socket.current = null;
        const nextRetry = retry + 1;
        // jitter 50–100 % to avoid thundering herd
        const jitter = delay * (0.5 + Math.random() * 0.5);
        setTimeout(() => connect(nextRetry), jitter);
      };
    };

    connect(); // initial connect

    // Cleanup on unmount / hot-reload
    return () => {
      socket.current?.close(1000, 'component unmount');
      socket.current = null;
    };
  }, [path, onMessage]);

  const sendMessage = (message: string) => {
    if (socket.current?.readyState === WebSocket.OPEN) {
      socket.current.send(message);
    }
  };

  return { ready, lastMessage, sendMessage };
}
