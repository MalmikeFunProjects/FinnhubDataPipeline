export interface StockSummary {
  type: "stock_summary";
  payload: {
    event_timestamp: number;
    total_price: number;
    symbol_prices: Record<string, number>;
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
  type: "info" | "error" | "warning";
  message: string;
}

export type WebSocketStockSummary = StockSummary | StatusMessage;
export type WebSocketStockPrice1s = StockPrice1s | StatusMessage;
export type WebSocketCompanySymbol = CompanySymbol | StatusMessage;
export type WebSocketLatestPrice = LatestPrice | StatusMessage;
