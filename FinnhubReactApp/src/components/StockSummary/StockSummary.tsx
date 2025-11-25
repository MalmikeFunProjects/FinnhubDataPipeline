"use client";
import LineChartComponent from "@/components/StockSummary/LineChartComponent";
import { StockWebSocketProvider } from "@/components/StockSummary/StockSummaryProvider";
import StockSummaryControlPanel from "@/components/StockSummary/StockSummaryControlPanel";
import StackedBarChartComponent from "./StackedBarChartComponent";

// Main component that uses the provider and renders the charts
const StockSummaryComponent: React.FC = () => {
    return (
      <StockWebSocketProvider>
        <main className="flex min-h-screen flex-col items-center justify-center p-24  w-full">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl w-full">
            <div className="mb-4">
              <div className="w-full">
                <p className="text-gray-500 text-3xl font-semibold">Live Crypto Prices</p>
                <StockSummaryControlPanel />
              </div>
              <div className="mb-6">
                <p className="text-gray-500 text-xl font-semibold mb-2">Total Crypto Prices</p>
                <LineChartComponent />
              </div>
              <div className="mb-6">
                <h1 className="text-gray-500 text-xl font-semibold mb-2">Crypto Price Distribution</h1>
                <StackedBarChartComponent />
              </div>
            </div>
          </div>
        </main>
      </StockWebSocketProvider>
    );
  };

  export default StockSummaryComponent;
