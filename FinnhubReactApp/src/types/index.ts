// Common prop types
export interface ButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "success" | "danger";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
}

// Override the value type based on the 'type' prop
export type InputValueProp<T extends InputProps['type']> =
  T extends 'number' ? number | undefined : string | number | undefined;

export interface InputProps {
  children?: React.ReactNode;
  value?: InputValueProp<InputProps['type']>; // Dynamically set value type
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onKeyUp?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  placeholder?: string;
  variant?: "primary" | "secondary" | "success" | "danger";
  text_variant?: "primary" | "secondary" | "success" | "error";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  disabled?: boolean;
  type?:
    | "text"
    | "password"
    | "number"
    | "email"
    | "date"
    | "time"
    | "datetime-local";
  className?: string;
  error?: string;
  helperText?: string;
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
}

// Data models
export interface User {
  id: string;
  name: string;
  email: string;
  role: "user" | "admin";
}

// API responses
export interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

export interface ChatMessage {
  type: "chat";
  sender: string;
  content: string;
  timestamp: number;
}

export interface StockSummary {
  type: "stock_summary";
  payload: {
    event_timestamp: number;
    total_price: number;
    symbols: string[];
  };
}

export interface StockPrice1s {
  type: "stock_price_1s";
  payload: {
    event_timestamp: number;
    symbol: string;
    count: number;
    avg_price: number;
  };
}

export interface CompanySymbol {
  type: "company_symbol";
  payload: {
    symbol: string;
  };
}

export interface LatestPrice {
  type: "latest_price";
  payload: {
    event_timestamp: number;
    symbol: string;
    last_price: number;
  };
}

export interface StatusMessage {
  type: "status";
  message: string;
}

export interface WebSocketAction {
  type: "websocket_action";
  action: "start" | "stop";
  payload?: Record<string, any>;
}

export interface Message {
  type: string;
  [key: string]: any;
}

export interface WebSocketContextType {
  status: "connecting" | "open" | "closing" | "closed" | "error";
  messages: Message[];
  sendMessage: (message: Message) => boolean;
  reconnect: () => void;
  disconnect: () => void;
}

export interface WebSocketProviderProps {
  children: React.ReactNode;
  url: string;
}

export type WebSocketStockSummary = StockSummary | StatusMessage;
export type WebSocketStockPrice1s = StockPrice1s | StatusMessage;
export type WebSocketCompanySymbol = CompanySymbol | StatusMessage;
export type WebSocketLatestPrice = LatestPrice | StatusMessage;
export type WebSocketMessage = ChatMessage | StatusMessage;
