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
  } from 'chart.js';
import { Bar } from "react-chartjs-2";
import { useStockWebSocketContext } from "@/components/StockSummary/StockSummaryProvider";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
  )

interface StackedBarChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor: string[];
    borderWidth: number;
  }[];
}

const StackedBarChartComponent: React.FC = () => {
  const {
    dataBufferRef,
    lastUpdateTimeRef,
    pauseChart,
    chartTimeWindow,
    chartUpdateInterval
  } = useStockWebSocketContext();

  const [stackedBarChartData, setStackedBarChartData] = useState<StackedBarChartData>({
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

  // Method to update stackedBar chart with buffered data
  const updateStackedBarChartWithBufferedData = useCallback(() => {
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

        setStackedBarChartData((prevData) => {
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

  // Periodic update to ensure stackedBar chart updates
  useEffect(() => {
    const intervalId = setInterval(() => {
      updateStackedBarChartWithBufferedData();
    }, chartUpdateInterval);

    return () => clearInterval(intervalId);
  }, [updateStackedBarChartWithBufferedData, chartUpdateInterval]);

  return (
    <div className="h-64">
      <Bar
        data={stackedBarChartData}
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
          },
          scales: {
            x: {
              stacked: true,
              title: {
                display: true,
                text: 'Symbols',
              },
            },
            y: {
              stacked: true,
              title: {
                display: true,
                text: 'Prices',
              },
            },
          },
        }}
      />
    </div>
  );
};

export default StackedBarChartComponent;
