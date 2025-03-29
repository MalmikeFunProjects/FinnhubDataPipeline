"use client";
import React, { useState, useEffect, useCallback } from "react";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from "chart.js";
import { Pie } from "react-chartjs-2";
import { useStockWebSocketContext } from "@/components/StockSummary/StockSummaryProvider";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend
);

interface PieChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor: string[];
    borderWidth: number;
  }[];
}

const PieChartComponent: React.FC = () => {
  const {
    dataBufferRef,
    lastUpdateTimeRef,
    pauseChart,
    chartTimeWindow,
    chartUpdateInterval
  } = useStockWebSocketContext();

  const [pieChartData, setPieChartData] = useState<PieChartData>({
    labels: [],
    datasets: [
      {
        label: "Symbol Prices",
        data: [],
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "rgba(75, 192, 192, 0.6)",
          "rgba(153, 102, 255, 0.6)",
          "rgba(255, 159, 64, 0.6)",
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 206, 86, 1)",
          "rgba(75, 192, 192, 1)",
          "rgba(153, 102, 255, 1)",
          "rgba(255, 159, 64, 1)",
        ],
        borderWidth: 1,
      },
    ],
  });

  // Method to update pie chart with buffered data
  const updatePieChartWithBufferedData = useCallback(() => {
    if (pauseChart) {
      return;
    }

    const buffer = dataBufferRef.current;

    if (buffer.length > 0) {
      // Find the last update time if it exists, otherwise use the first message's timestamp
      const referenceTime =
        lastUpdateTimeRef.current || buffer[0].payload.event_timestamp;

      // Filter data within the time window
      const dataInTimeWindow = buffer.filter(
        (item) =>
          item.payload.event_timestamp >= referenceTime &&
          item.payload.event_timestamp <= referenceTime + chartTimeWindow
      );

      if (dataInTimeWindow.length > 0) {
        // Take the last data point in the time window
        const latestData = dataInTimeWindow[dataInTimeWindow.length - 1];

        setPieChartData((prevData) => {
          if (!latestData.payload.symbol_prices) {
            return {
              labels: [],
              datasets: [
                {
                  ...prevData.datasets[0],
                  data: [],
                },
              ],
            };
          }

          const symbols = Object.keys(latestData.payload.symbol_prices);
          const prices = Object.values(latestData.payload.symbol_prices);

          // Ensure we have enough colors for all symbols
          const backgroundColor = symbols.map((_, index) => {
            const baseColors = prevData.datasets[0].backgroundColor;
            return baseColors[index % baseColors.length];
          });

          const borderColor = symbols.map((_, index) => {
            const baseColors = prevData.datasets[0].borderColor;
            return baseColors[index % baseColors.length];
          });

          return {
            labels: symbols,
            datasets: [
              {
                ...prevData.datasets[0],
                data: prices,
                backgroundColor,
                borderColor,
              },
            ],
          };
        });
      }
    }
  }, [pauseChart, dataBufferRef, lastUpdateTimeRef, chartTimeWindow]);

  // Periodic update to ensure pie chart updates
  useEffect(() => {
    const intervalId = setInterval(() => {
      updatePieChartWithBufferedData();
    }, chartUpdateInterval);

    return () => clearInterval(intervalId);
  }, [updatePieChartWithBufferedData, chartUpdateInterval]);

  return (
    <div className="h-64">
      <Pie
        data={pieChartData}
        options={{
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              position: 'right',
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const label = context.label || '';
                  const value = context.raw as number;
                  return `${label}: ${value.toFixed(2)}`;
                }
              }
            }
          }
        }}
      />
    </div>
  );
};

export default PieChartComponent;
