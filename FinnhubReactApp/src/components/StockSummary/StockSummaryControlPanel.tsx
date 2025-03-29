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
      handleStartDate,
      togglePauseChart
    } = useStockWebSocketContext();

    const minValue = 0;
    const maxValue = 30;

    return (
      <div className="mb-6">
        <h1 className="text-xl font-bold text-blue-600 mb-4">
          Status: {status}
        </h1>
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
    );
  };

  export default StockSummaryControlPanel;

