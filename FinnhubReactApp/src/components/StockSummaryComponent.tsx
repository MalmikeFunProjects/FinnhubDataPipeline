"use client";
import React, { useState, useEffect, useCallback, useRef } from "react";
import { useJsonWebSocket } from "@/hooks/useJsonWebSocket";
import { WebSocketStockSummary, WebSocketAction, StockSummary } from "@/types";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Line, Pie } from "react-chartjs-2";
import { msToDatetime } from "@/utils";
import Button from "@/components/UIComponents/Button";
import NumericInput from "@/components/UIComponents/NumericInput";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  // Pie chart elements
  ArcElement
  // Tooltip,
  // Legend
);

// Set the maximum number of data points to display
const MAX_DATA_POINTS = 50;
const TIME_WINDOW = 5000; // 5 seconds in milliseconds

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

interface PieChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
    borderColor: string[];
    borderWidth: number;
    dataMap: Map<string, number>;
  }[];
}

const StockSummaryComponent: React.FC = () => {
  const minValue = 0;
  const maxValue = 30;
  const [inputStartDate, setInputStartDate] = useState<number | undefined>();
  const [chartUpdateInterval, setChartUpdateInterval] = useState<number>(1000);
  const [chartTimeWindow, setChartTimeWindow] = useState<number>(5000);
  const [pauseChart, setPauseChart] = useState<boolean>(false);
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

  const [pieChartData, setPieChartData] = useState<PieChartData>({
    labels: [],
    datasets: [
      {
        label: "Price",
        data: [],
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "red",
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 206, 86, 1)",
          "red",
        ],
        borderWidth: 1,
        dataMap: new Map<string, number>(),
      },
    ],
  });

  // Ref to collect incoming data points
  const dataBufferRef = useRef<StockSummary[]>([]);
  const lastUpdateTimeRef = useRef<number>(0);

  const {
    status,
    messages,
    sendMessage,
    disconnect,
    reconnect,
    clearMessages,
    addConnectionQuery,
    clearConnectionQuery,
  } = useJsonWebSocket<WebSocketStockSummary, WebSocketAction>(
    "ws://localhost:8000/stock_summary/ws"
  );

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

      // Filter data within the 5-second time window
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

        setPieChartData((prevData) => {
          if (!latestData.payload.symbol_prices) {
            return {
              labels: [],
              datasets: [
                {
                  ...prevData.datasets[0],
                  data: [],
                  dataMap: new Map<string, number>(),
                },
              ],
            };
          }

          return {
            labels: Object.keys(latestData.payload.symbol_prices),
            datasets: [
              {
                ...prevData.datasets[0],
                data: Object.values(latestData.payload.symbol_prices),
              },
            ],
          };
        });

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
        return;
      }
    }
  }, [pauseChart, dataBufferRef, lastUpdateTimeRef, chartTimeWindow]);

  const clear_chart = useCallback(() => {
    dataBufferRef.current = [];
    lastUpdateTimeRef.current = 0;
    setChartData((prevData) => {
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
  }, []);

  // Use effect to process messages and buffer data points
  useEffect(() => {
    // Process only stock summary messages
    let unproccessed_message: StockSummary[] = [];
    messages.forEach((msg) => {
      if (
        msg.type === "stock_summary" &&
        msg.payload.event_timestamp >= lastUpdateTimeRef.current
      ) {
        unproccessed_message.push(msg as StockSummary);
      } else if (msg.type === "info") {
        console.log(msg);
      }
    });
    dataBufferRef.current = unproccessed_message;

    // Attempt to update chart
    updateChartWithBufferedData();
  }, [messages, updateChartWithBufferedData]);

  // Periodic update to ensure chart updates
  useEffect(() => {
    const intervalId = setInterval(() => {
      updateChartWithBufferedData();
    }, chartUpdateInterval); // Check every 1 seconds

    return () => clearInterval(intervalId);
  }, [updateChartWithBufferedData, chartUpdateInterval]);

  const handleStartDate = (event?: React.MouseEvent<HTMLButtonElement>) => {
    if (typeof inputStartDate === "number") {
      clear_chart();
      clearMessages();
      if (status === "open") {
        const message: WebSocketAction = {
          type: "websocket_action",
          action: "start",
          payload: {
            start_days_ago: inputStartDate,
          },
        };
        sendMessage(message);
      } else {
        addConnectionQuery(`start_days_ago=${inputStartDate}`);
      }
    }
    setInputStartDate(undefined);
    setPauseChart(false);
  };

  const pauseChartFunc = () => {
    setPauseChart(!pauseChart);
    if (pauseChart) {
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].type === "stock_summary") {
          const message = messages[i] as StockSummary;
          const latest_timestamp = message?.payload?.event_timestamp;
          if (latest_timestamp)
            addConnectionQuery(`since_timestamp=${latest_timestamp}`);
          break;
        }
      }
    } else {
      disconnect();
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl w-full">
        <div className="mb-4">
          <h2 className="text-xl font-semibold mb-4">Live Stock Data</h2>

          <div>
            <h1 className="text-xl font-bold text-blue-600 mb-4">
              Status: {status}
            </h1>
            <div className="flex space-x-3 mb-4">
              <Button
                variant={pauseChart || status !== "open" ? "success" : "danger"}
                onClick={pauseChartFunc}
              >
                {pauseChart || status !== "open" ? "Resume" : "Pause"}
              </Button>
            </div>
            <div className="flex mb-4">
              <NumericInput
                variant="primary"
                type="number"
                placeholder="Days ago to start (0 - 30 days ago)..."
                value={inputStartDate}
                onChange={(e) => setInputStartDate(Number(e.target.value))}
                className="flex-grow mr-2"
                min={minValue}
                max={maxValue}
              />
              <Button
                variant="success"
                onClick={handleStartDate}
                disabled={inputStartDate === undefined}
              >
                Start
              </Button>
            </div>
          </div>
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
          <div>
            <h1>Website Traffic</h1>
            <Pie data={pieChartData} />
          </div>
        </div>
      </div>
    </main>
  );
};

export default StockSummaryComponent;
