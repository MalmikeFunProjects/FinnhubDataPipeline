import { MutableRefObject, ReactNode } from 'react';
import {StockSummary} from "@/types"

export interface WebSocketAction {
  type: "websocket_action";
  action: "start" | "stop";
  payload?: Record<string, any>;
}

export interface Message {
  type: string;
  [key: string]: any;
}

export interface StockSummaryContextType {
  status: string;
  messages: any[];
  dataBufferRef: MutableRefObject<StockSummary[]>;
  lastUpdateTimeRef: MutableRefObject<number>;
  pauseChart: boolean;
  chartTimeWindow: number;
  chartUpdateInterval: number;
  MAX_DATA_POINTS: number;
  inputStartDate: number | undefined;
  setInputStartDate: (value: number | undefined) => void;
  handleStartDate: () => void;
  togglePauseChart: () => void;
  clearChart: () => void;
  clearMessages: () => void;
}

export interface WebSocketProviderProps {
  children: React.ReactNode;
  url: string;
}
