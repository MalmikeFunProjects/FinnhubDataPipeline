// Enhanced hook with JSON support
import { useEffect, useRef, useState, useCallback } from 'react';

type WebSocketStatus = 'connecting' | 'open' | 'closing' | 'closed' | 'error';

interface UseWebSocketOptions<T> {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onMessage?: (data: T, event: MessageEvent) => void;
  onError?: (event: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  protocols?: string | string[];
}

export function useJsonWebSocket<T = any, U = any>(url: string, options: UseWebSocketOptions<T> = {}) {
  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const [messages, setMessages] = useState<T[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    onOpen,
    onClose,
    onMessage,
    onError,
    reconnectAttempts = 1,
    reconnectInterval = 300000,
    protocols,
  } = options;

  const connect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
    }

    socketRef.current = new WebSocket(url, protocols);
    setStatus('connecting');

    socketRef.current.onopen = (event) => {
      setStatus('open');
      reconnectCountRef.current = 0;
      if (onOpen) onOpen(event);
    };

    socketRef.current.onclose = (event) => {
      setStatus('closed');

      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectCountRef.current += 1;
          connect();
        }, reconnectInterval);
      }

      if (onClose) onClose(event);
    };

    socketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        console.log(data)
        setMessages((prevMessages) => [...prevMessages, data]);
        if (onMessage) onMessage(data, event);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socketRef.current.onerror = (event) => {
      setStatus('error');
      if (onError) onError(event);
    };
  }, [url, protocols, onOpen, onClose, onMessage, onError, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.close();
      setStatus('closing');
    }
  }, []);

  const sendMessage = useCallback((message: U) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      console.log(message)
      socketRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    messages,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}
