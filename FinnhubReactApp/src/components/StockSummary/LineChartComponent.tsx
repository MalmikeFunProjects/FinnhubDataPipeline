"use client";
import React, { useState, useEffect, useCallback } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { msToDatetime } from "@/utils";
import { useStockWebSocketContext } from "@/components/StockSummary/StockSummaryProvider";
import { StockSummary } from "@/types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    fill: boolean;
    borderColor: string;
    tension: number;
    extraInfo: string[][];
  }[];
}

const LineChartComponent: React.FC = () => {
  const {
    dataBufferRef,
    lastUpdateTimeRef,
    pauseChart,
    chartTimeWindow,
    chartUpdateInterval,
    MAX_DATA_POINTS
  } = useStockWebSocketContext();

  const [chartData, setChartData] = useState<ChartData>({
    labels: [],
    datasets: [
      {
        label: "Total Price",
        data: [],
        fill: false,
        borderColor: "rgb(75, 192, 192)",
        tension: 0.1,
        extraInfo: [],
      },
    ],
  });

  // Method to update chart with buffered data
  const updateChartWithBufferedData = useCallback(() => {
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
        // If we have data in the time window, update the chart
        // Take the last data point in the time window
        const latestData = dataInTimeWindow[dataInTimeWindow.length - 1];
        const date = msToDatetime(latestData.payload.event_timestamp);

        setChartData((prevData) => {
          // Create copies of the existing arrays
          const newLabels = [...prevData.labels];
          const newDataPoints = [...prevData.datasets[0].data];
          const newExtraInfo = [...prevData.datasets[0].extraInfo];

          // Add new data point
          newLabels.push(date);
          newDataPoints.push(latestData.payload.total_price);
          newExtraInfo.push(Object.keys(latestData.payload.symbol_prices));

          // Trim data to maintain maximum points
          const trimmedLabels = newLabels.slice(-MAX_DATA_POINTS);
          const trimmedDataPoints = newDataPoints.slice(-MAX_DATA_POINTS);
          const trimmedExtraInfo = newExtraInfo.slice(-MAX_DATA_POINTS);

          return {
            labels: trimmedLabels,
            datasets: [
              {
                ...prevData.datasets[0],
                data: trimmedDataPoints,
                extraInfo: trimmedExtraInfo,
              },
            ],
          };
        });

        // Update the last update time
        lastUpdateTimeRef.current = referenceTime + chartTimeWindow;

        // Remove processed data from the buffer
        dataBufferRef.current = buffer.filter(
          (item) => item.payload.event_timestamp > lastUpdateTimeRef.current
        );
      } else {
        for (let i = 0; i < buffer.length; i++) {
          if (buffer[i].payload.event_timestamp > lastUpdateTimeRef.current) {
            lastUpdateTimeRef.current = buffer[i].payload.event_timestamp;
            break;
          }
        }
      }
    }
  }, [pauseChart, dataBufferRef, lastUpdateTimeRef, chartTimeWindow, MAX_DATA_POINTS]);

  // Periodic update to ensure chart updates
  useEffect(() => {
    const intervalId = setInterval(() => {
      updateChartWithBufferedData();
    }, chartUpdateInterval);

    return () => clearInterval(intervalId);
  }, [updateChartWithBufferedData, chartUpdateInterval]);

  return (
    <Line
      data={chartData}
      options={{
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          x: {
            title: {
              display: true,
              text: "Time",
            },
          },
          y: {
            title: {
              display: true,
              text: "Total Price",
            },
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              footer: (context) => {
                const dataset = context[0].dataset as any;
                const index = context[0].dataIndex;
                const symbols = dataset?.extraInfo[index];

                return `\nAssociated Symbols:\n${symbols.join("\n")}`;
              },
            },
          },
        },
        animation: {
          duration: 0, // Disable animation for better performance with real-time data
        },
      }}
    />
  );
};

export default LineChartComponent;
