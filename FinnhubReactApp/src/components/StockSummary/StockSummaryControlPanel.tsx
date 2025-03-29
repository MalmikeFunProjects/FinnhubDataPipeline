import { useStockWebSocketContext } from "@/components/StockSummary/StockSummaryProvider";
import Button from "@/components/UIComponents/Button";
import NumericInput from "../UIComponents/NumericInput";

// Control panel component for managing the WebSocket connection
const StockSummaryControlPanel: React.FC = () => {
  const {
    status,
    pauseChart,
    inputStartDate,
    setInputStartDate,
    chartTimeWindow,
    chartUpdateInterval,
    setChartUpdateInterval,
    setChartTimeWindow,
    handleStartDate,
    togglePauseChart,
  } = useStockWebSocketContext();

  const minDaysAgo = 0;
  const maxDaysAgo = 30;
  const minChartUpdateInterval = 1;
  const maxChartUpdateInterval = 30;
  const minChartTimeWindow = 1;
  const maxChartTimeWindow = 30;

  return (
    <div className="mb-6">
      <h1 className="text-xl font-bold text-blue-600 mb-4">Status: {status}</h1>
      <div className="flex flex-row justify-between w-full">
        <div className="min-w-xs">
          <div className="flex space-x-3 mb-4">
            <Button
              variant={pauseChart || status !== "open" ? "success" : "danger"}
              onClick={togglePauseChart}
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
              min={minDaysAgo}
              max={maxDaysAgo}
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
        <div className="min-w-sm">
          <p className="text-gray-500 text-grey-dark text-xl font-semibold mb-1">
            Update Chart Refresh Cycle
          </p>
          <div className="flex flex-row mb-4 justify-between">
            <div className="flex flex-col mb-4">
              <p className="text-black">Chart Update Interval</p>
              <NumericInput
                variant="primary"
                type="number"
                placeholder="Set chart update interval (1 - 30 seconds)..."
                defaultValue={1}
                value={chartUpdateInterval / 1000}
                onChange={(e) =>
                  setChartUpdateInterval(Number(e.target.value) * 1000)
                }
                className="flex-grow mr-2"
                min={minChartUpdateInterval}
                max={maxChartUpdateInterval}
              />
            </div>
            <div className="flex flex-col mb-4 align-items-center justify-content-center">
              <p className="text-black">Chart Time Window</p>
              <NumericInput
                variant="primary"
                type="number"
                placeholder="Set chart update interval (1 - 30 seconds)..."
                defaultValue={5}
                value={chartTimeWindow / 1000}
                onChange={(e) =>
                  setChartTimeWindow(Number(e.target.value) * 1000)
                }
                className="flex-grow mr-2"
                min={minChartTimeWindow}
                max={maxChartTimeWindow}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockSummaryControlPanel;
