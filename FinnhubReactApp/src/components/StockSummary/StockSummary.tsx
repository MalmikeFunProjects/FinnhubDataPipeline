"use client";
import LineChartComponent from "@/components/StockSummary/LineChartComponent";
import PieChartComponent from "@/components/StockSummary/PieChartComponent";
import { StockWebSocketProvider } from "@/components/StockSummary/StockSummaryProvider";
import StockSummaryControlPanel from "@/components/StockSummary/StockSummaryControlPanel";
import StackedBarChartComponent from "./StackedBarChartComponent";

// Main component that uses the provider and renders the charts
const StockSummaryComponent: React.FC = () => {
    return (
      <StockWebSocketProvider>
        <main className="flex min-h-screen flex-col items-center justify-center p-24">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl w-full">
            <div className="mb-4">
              <h2 className="text-xl font-semibold mb-4">Live Stock Data</h2>
              <StockSummaryControlPanel />
              <div className="mb-6">
                <LineChartComponent />
              </div>
              <div className="mb-6">
                <h1 className="text-xl font-semibold mb-2">Symbol Distribution</h1>
                <PieChartComponent />
              </div>
              <div className="mb-6">
                <h1 className="text-xl font-semibold mb-2">Symbol Distribution</h1>
                <StackedBarChartComponent />
              </div>
            </div>
          </div>
        </main>
      </StockWebSocketProvider>
    );
  };

  export default StockSummaryComponent;
