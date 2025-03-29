"use client";
import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from "react";
import { useJsonWebSocket } from "@/hooks/useJsonWebSocket";
import { WebSocketStockSummary, WebSocketAction, StockSummary, StockSummaryContextType } from "@/types";

// Set the maximum number of data points to display
const MAX_DATA_POINTS = 50;

// Create the WebSocket context
const StockWebSocketContext = createContext<StockSummaryContextType | null>(null);

// Create a hook to use the WebSocket context
export const useStockWebSocketContext = () => {
  const context = useContext(StockWebSocketContext);
  if (!context) {
    throw new Error('useStockWebSocketContext must be used within a StockWebSocketProvider');
  }
  return context;
};

// Create the WebSocket provider component
export const StockWebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [chartUpdateInterval, setChartUpdateInterval] = useState<number>(1000);
  const [chartTimeWindow, setChartTimeWindow] = useState<number>(5000);
  const [pauseChart, setPauseChart] = useState<boolean>(false);
  const [inputStartDate, setInputStartDate] = useState<number | undefined>();

  // Refs to collect incoming data points
  const dataBufferRef = useRef<StockSummary[]>([]);
  const lastUpdateTimeRef = useRef<number>(0);

  const {
    status,
    messages,
    sendMessage,
    disconnect,
    reconnect,
    clearMessages,
    addConnectionQuery,
    clearConnectionQuery,
  } = useJsonWebSocket<WebSocketStockSummary, WebSocketAction>(
    "ws://localhost:8000/stock_summary/ws"
  );

  // Method to clear the chart data
  const clearChart = useCallback(() => {
    dataBufferRef.current = [];
    lastUpdateTimeRef.current = 0;
  }, []);

  // Handle start date submission
  const handleStartDate = useCallback(() => {
    if (typeof inputStartDate === "number") {
      clearChart();
      clearMessages();
      if (status === "open") {
        const message: WebSocketAction = {
          type: "websocket_action",
          action: "start",
          payload: {
            start_days_ago: inputStartDate,
          },
        };
        sendMessage(message);
      } else {
        addConnectionQuery(`start_days_ago=${inputStartDate}`);
      }
    }
    setInputStartDate(undefined);
    setPauseChart(false);
  }, [inputStartDate, status, clearChart, clearMessages, sendMessage, addConnectionQuery]);

  // Toggle pausing the chart updates
  const togglePauseChart = useCallback(() => {
    setPauseChart((prev) => !prev);
    if (pauseChart) {
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].type === "stock_summary") {
          const message = messages[i] as StockSummary;
          const latest_timestamp = message?.payload?.event_timestamp;
          if (latest_timestamp)
            addConnectionQuery(`since_timestamp=${latest_timestamp}`);
          break;
        }
      }
    } else {
      disconnect();
    }
  }, [pauseChart, messages, addConnectionQuery, disconnect]);

  // Process messages and buffer data points
  useEffect(() => {
    let unprocessed_messages: StockSummary[] = [];
    messages.forEach((msg) => {
      if (
        msg.type === "stock_summary" &&
        msg.payload.event_timestamp >= lastUpdateTimeRef.current
      ) {
        unprocessed_messages.push(msg as StockSummary);
      } else if (msg.type === "info") {
        console.log(msg);
      }
    });
    dataBufferRef.current = unprocessed_messages;
  }, [messages]);

  // Context value
  const contextValue: StockSummaryContextType = {
    status,
    messages,
    dataBufferRef,
    lastUpdateTimeRef,
    pauseChart,
    chartTimeWindow,
    chartUpdateInterval,
    MAX_DATA_POINTS,
    inputStartDate,
    setInputStartDate,
    handleStartDate,
    togglePauseChart,
    clearChart,
    clearMessages
  };

  return (
    <StockWebSocketContext.Provider value={contextValue}>
      {children}
    </StockWebSocketContext.Provider>
  );
};
