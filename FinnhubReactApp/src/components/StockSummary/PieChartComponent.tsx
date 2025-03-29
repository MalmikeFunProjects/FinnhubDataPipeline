"use client";
import React, { useState, useEffect, useCallback } from "react";
import { Chart as ChartJS, ArcElement, Tooltip, Legend, Title } from "chart.js";
import { Pie } from "react-chartjs-2";
import { useStockWebSocketContext } from "@/components/StockSummary/StockSummaryProvider";

ChartJS.register(ArcElement, Tooltip, Legend, Title);

interface PieChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor: string[];
    borderWidth: number;
    extraData: Object;
  }[];
}

const PieChartComponent: React.FC = () => {
  const { stockSummary } = useStockWebSocketContext();

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
        extraData: {},
      },
    ],
  });
  const [currentTime, setCurrentTime] = useState<string | null>(null);

  // Method to update pie chart with buffered data
  const updatePieChartWithBufferedData = useCallback(() => {
    if (!stockSummary) {
      setPieChartData((prevData) => {
        setCurrentTime(null);
        return {
          labels: [],
          datasets: [
            {
              ...prevData.datasets[0],
              data: [],
            },
          ],
        };
      });
    } else {
      const latestData = stockSummary;

      setPieChartData((prevData) => {
        const timestamp = new Date(
          latestData.payload.event_timestamp
        ).toLocaleTimeString();
        setCurrentTime(timestamp);

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
              extraData: {
                timestamp,
              },
            },
          ],
        };
      });
    }
  }, [stockSummary]);

  // Periodic update to ensure pie chart updates
  useEffect(() => {
    updatePieChartWithBufferedData();
  }, [updatePieChartWithBufferedData]);

  return (
    <div className="h-75">
      <h1>{currentTime ? `Stock Prices ${currentTime}` : ""}</h1>
      <Pie
        data={pieChartData}
        options={{
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              position: "bottom",
            },
            tooltip: {
              callbacks: {
                title: (context) => {
                  const dataset = context[0]?.dataset as any;
                  return dataset?.extraData?.timestamp || "";
                },
                label: (context) => {
                  const label = context.label || "";
                  const value = context.raw as number;
                  return `${label}: ${value.toFixed(2)}`;
                },
              },
            },
          },
          layout: {
            padding: { top: 0, right: 0, bottom: 0, left: 0 },
          },
        }}
      />
    </div>
  );
};

export default PieChartComponent;
