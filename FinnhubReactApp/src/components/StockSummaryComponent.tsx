"use client";
import React, { useState, useEffect } from 'react';
import { useJsonWebSocket } from '@/hooks/useJsonWebSocket';
import { WebSocketStockSummary, WebSocketAction } from '@/types';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { msToDatetime } from '@/utils';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Set the maximum number of data points to display
const MAX_DATA_POINTS = 20;

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    fill: boolean;
    borderColor: string;
    tension: number;
  }[];
}

const StockSummaryComponent: React.FC = () => {
  const minValue = 0;
  const maxValue = 30;
  const [inputStartDate, setInputStartDate] = useState<number|undefined>();
  const [mIndex, setMIndex] = useState(0)
  const [chartData, setChartData] = useState<ChartData>({
    labels: [],
    datasets: [
      {
        label: 'Live Data',
        data: [],
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  });

  const { status, messages, sendMessage, disconnect, reconnect } = useJsonWebSocket<WebSocketStockSummary, WebSocketAction>('ws://localhost:8000/stock_summary/ws');

  useEffect(() => {
    // Process only the most recent message

    const recentMessages = messages.slice(mIndex);
    console.log(recentMessages.length);

    recentMessages.forEach((msg, index) => {
      if (msg.type === 'stock_summary') {
        const data = msg.payload;
        const date = msToDatetime(data.event_timestamp);

        setChartData((prevData) => {
          // Create copies of the existing arrays
          const newLabels = [...prevData.labels];
          const newData = [...prevData.datasets[0].data];

          // Add new data point
          newLabels.push(date);
          newData.push(data.total_price);

          // If we exceed our maximum, remove the oldest data points
          if (newLabels.length > MAX_DATA_POINTS) {
            newLabels.shift(); // Remove the first/oldest label
            newData.shift();   // Remove the first/oldest data point
          }

          return {
            labels: newLabels,
            datasets: [
              {
                ...prevData.datasets[0],
                data: newData
              }
            ]
          };
        });
      }
      setMIndex(index + 1);
    });
  }, [messages]);

  const handleStartDate = () => {
    if (inputStartDate && status === 'open') {
      // Prevent duplicate symbols
      const message: WebSocketAction = {
        type: "websocket_action",
        action: "start",
        payload: {
          start_days_ago: inputStartDate
        }
      };

      sendMessage(message);
    }
    setInputStartDate(undefined);
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log(`Reached here: ${event}`)
    const stringValue = event.target.value;
    const numericValue = parseInt(stringValue); // Or parseInt if you expect integers

    if (!isNaN(numericValue)) {
      setInputStartDate(numericValue < minValue ? minValue : numericValue > maxValue ? maxValue : numericValue);
    } else if (stringValue === "") {
      setInputStartDate(undefined); // Handle empty input as needed
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
        <div className="mb-4">
          <h2 className="text-xl font-semibold mb-2">Live Stock Data</h2>
          <Line
            data={chartData}
            options={{
              responsive: true,
              maintainAspectRatio: true,
              scales: {
                x: {
                  title: {
                    display: true,
                    text: 'Time'
                  }
                },
                y: {
                  title: {
                    display: true,
                    text: 'Price'
                  }
                }
              },
              animation: {
                duration: 0 // Disable animation for better performance with real-time data
              }
            }}
          />
        </div>

        <div>
          <h1 className="text-xl font-bold text-blue-600 mb-4">
            Status: {status}
          </h1>
          <div className="flex space-x-3 mb-4">
            <Button variant="primary" onClick={reconnect} disabled={status === 'open'}>Connect</Button>
            <Button variant="danger" onClick={disconnect} disabled={status !== 'open'}>Disconnect</Button>
          </div>
          <div className="flex mb-4">
            <Input
              variant="primary"
              type="number"
              placeholder="Data date origin (0 - 30 days ago)..."
              disabled={status !== 'open'}
              value={inputStartDate}
              onChange={(e) => handleChange(e)}
              className="flex-grow mr-2"
              min={minValue}
              max={maxValue}
            />
            <Button
              variant="success"
              onClick={handleStartDate}
              disabled={status !== 'open'}
            >
              Track
            </Button>
          </div>
          <div>
            <h3 className="text-lg font-bold text-blue-600 mb-2">
              Recent Updates:
            </h3>
            <div className="max-h-40 overflow-y-auto">
              {messages.slice(-5).map((msg, index) => {
                if (msg.type === 'stock_summary') {
                  return (
                    <div key={index} className="chat-message text-black mb-1">
                      <strong>{msToDatetime(msg.payload.event_timestamp)}:</strong> {msg.payload.total_price} {msg.payload.symbols}
                    </div>
                  );
                } else if (msg.type === 'status') {
                  return (
                    <div key={index} className="status-message mb-1">
                      {msg.message}
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default StockSummaryComponent;
