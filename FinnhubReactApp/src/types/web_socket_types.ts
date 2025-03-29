import { MutableRefObject } from 'react';
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
  setChartTimeWindow: (value: number) => void;
  chartUpdateInterval: number;
  setChartUpdateInterval: (value: number) => void;
  MAX_DATA_POINTS: number;
  stockSummary: StockSummary | null;
  setStockSummary: (value: StockSummary | null) => void;
  inputStartDate: number | undefined;
  setInputStartDate: (value: number | undefined) => void;
  handleStartDate: () => void;
  togglePauseChart: () => void;
  clearChart: boolean;
  setClearChart: (value: boolean) => void;
  clearChartData: () => void;
  clearMessages: () => void;
}

export interface WebSocketProviderProps {
  children: React.ReactNode;
  url: string;
}
