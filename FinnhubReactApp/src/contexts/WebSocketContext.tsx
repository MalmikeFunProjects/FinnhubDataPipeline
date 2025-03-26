"use client";
import React, { createContext, useContext, ReactNode } from 'react';
import { useJsonWebSocket } from '@/hooks/useJsonWebSocket';
import {Message, WebSocketContextType, WebSocketProviderProps} from '@/types'


const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ url, children }) => {
  const websocket = useJsonWebSocket<Message>(url);

  return (
    <WebSocketContext.Provider value={websocket}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};
