"use client";
import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
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

interface ExtraInfo {
  stockSummary: StockSummary;
  symbols: string[];
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    fill: boolean;
    borderColor: string;
    tension: number;
    extraInfo: ExtraInfo[];
  }[];
}

const LineChartComponent: React.FC = () => {
  const chartRef = useRef(null);
  const {
    dataBufferRef,
    lastUpdateTimeRef,
    pauseChart,
    chartTimeWindow,
    chartUpdateInterval,
    setStockSummary,
    clearChart,
    setClearChart,
    MAX_DATA_POINTS
  } = useStockWebSocketContext();
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

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
        setStockSummary(latestData);
        const date = msToDatetime(latestData.payload.event_timestamp);

        setChartData((prevData) => {
          // Create copies of the existing arrays
          const newLabels = [...prevData.labels];
          const newDataPoints = [...prevData.datasets[0].data];
          const newExtraInfo = [...prevData.datasets[0].extraInfo];

          // Add new data point
          newLabels.push(date);
          newDataPoints.push(latestData.payload.total_price);
          newExtraInfo.push({
            stockSummary: latestData,
            symbols: Object.keys(latestData.payload.symbol_prices)
          });

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

   // Effect to handle chart clearing
   useEffect(() => {
    if (clearChart) {
      // Reset chart data state
      setChartData({
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
      setClearChart(false);
    }
  }, [clearChart, setClearChart]);

  // Periodic update to ensure chart updates
  useEffect(() => {
    const currentIntervalId = setInterval(() => {
      updateChartWithBufferedData();
    }, chartUpdateInterval);
    setIntervalId(currentIntervalId);

    return () => clearInterval(currentIntervalId);
  }, [clearChart, updateChartWithBufferedData, chartUpdateInterval]);

  const handleClick = (event: any) => {
    if(!pauseChart){
      return;
    }
    const chart = chartRef.current as unknown as ChartJS;;
    if (!chart) {
      return;
    }

    const elements = chart.getElementsAtEventForMode(
      event,
      'point',
      { intersect: true },
      false
    );

    if (elements.length > 0) {
      const index = elements[0].index;
      const datasetIndex = elements[0].datasetIndex;
      const data = chart.data as any;
      setStockSummary(data?.datasets[datasetIndex]?.extraInfo[index]?.stockSummary || null);
    } else {
      console.log("Select a point on the chart.")
    }
  };

  return (
    <Line
      data={chartData}
      ref={chartRef}
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
                const symbols = dataset?.extraInfo[index]?.symbols;

                return `\nAssociated Symbols:\n${symbols.join("\n")}`;
              },
            },
          },
        },
        animation: {
          duration: 0, // Disable animation for better performance with real-time data
        },
      }}
      onClick={handleClick}
    />
  );
};

export default LineChartComponent;
