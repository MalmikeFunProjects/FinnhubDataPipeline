"use client";
import React, { useState, useEffect, useCallback } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { useStockWebSocketContext } from "@/components/StockSummary/StockSummaryProvider";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface StackedBarChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string;
    borderColor: string;
    borderWidth: number;
  }[];
}

const StackedBarChartComponent: React.FC = () => {
  const { stockSummary } = useStockWebSocketContext();

  const [stackedBarChartData, setStackedBarChartData] =
    useState<StackedBarChartData>({
      labels: [],
      datasets: [],
    });
  const [currentTime, setCurrentTime] = useState<string | null>(null);
  const [currentDate, setCurrentDate] = useState<string | null>(null);
  const [totalPrice, setTotalPrice] = useState<string | null>(null);

  // Method to update stackedBar chart with buffered data
  const updateStackedBarChartWithBufferedData = useCallback(() => {
    if (!stockSummary) {
      setCurrentTime(null);
      setTotalPrice(null);
      setStackedBarChartData({
        labels: [],
        datasets: [],
      });
      return;
    } else {
      const latestData = stockSummary;

      const timestamp = new Date(
        latestData.payload.event_timestamp
      ).toLocaleTimeString();
      const date = new Date(latestData.payload.event_timestamp).toLocaleDateString();
      setCurrentDate(date);
      setCurrentTime(timestamp);
      setTotalPrice(latestData.payload.total_price.toFixed(2));

      // Create a dataset for each symbol
      const symbols = Object.keys(latestData.payload.symbol_prices);
      const colors = [
        "rgba(255, 99, 132, 0.6)",
        "rgba(54, 162, 235, 0.6)",
        "rgba(255, 206, 86, 0.6)",
        "rgba(75, 192, 192, 0.6)",
        "rgba(153, 102, 255, 0.6)",
        "rgba(255, 159, 64, 0.6)",
      ];

      const borderColors = [
        "rgba(255, 99, 132, 1)",
        "rgba(54, 162, 235, 1)",
        "rgba(255, 206, 86, 1)",
        "rgba(75, 192, 192, 1)",
        "rgba(153, 102, 255, 1)",
        "rgba(255, 159, 64, 1)",
      ];

      const datasets = symbols.map((symbol, index) => {
        return {
          label: symbol,
          data: [latestData.payload.symbol_prices[symbol]], // Array with single value for one timestamp
          backgroundColor: colors[index % colors.length],
          borderColor: borderColors[index % borderColors.length],
          borderWidth: 1,
        };
      });

      setStackedBarChartData({
        labels: [timestamp], // Using timestamp as the category
        datasets: datasets,
      });
    }
  }, [stockSummary]);

  // Periodic update to ensure stackedBar chart updates
  useEffect(() => {
    updateStackedBarChartWithBufferedData();
  }, [updateStackedBarChartWithBufferedData]);

  return (
    <div className="h-120">
      <div className="flex justify-around p-4">
        <p className="text-gray-600 text-l font-semibold mb-2">
          {currentDate ? (
            <>
              Date: <span className="text-blue-600">{currentDate}</span>
            </>
          ) : (
            ""
          )}
        </p>
        <p className="text-gray-600 text-l font-semibold mb-2">
          {currentTime ? (
            <>
              Time: <span className="text-blue-600">{currentTime}</span>
            </>
          ) : (
            ""
          )}
        </p>
        <p className="text-gray-600 text-l font-semibold mb-2">
          {totalPrice ? (
            <>
              Total Price: <span className="text-blue-600">{totalPrice}</span>
            </>
          ) : (
            ""
          )}
        </p>
      </div>
      <Bar
        data={stackedBarChartData}
        options={{
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              position: "right",
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const label = context.dataset.label || "";
                  const value = context.raw as number;
                  return `${label}: ${value.toFixed(2)}`;
                },
              },
            },
          },
          scales: {
            x: {
              stacked: true,
              title: {
                display: true,
                text: "Time",
              },
            },
            y: {
              stacked: true,
              title: {
                display: true,
                text: "Prices",
              },
            },
          },
        }}
      />
    </div>
  );
};

export default StackedBarChartComponent;
