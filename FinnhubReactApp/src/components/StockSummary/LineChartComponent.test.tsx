// import React from 'react';
// import { render, screen, act, fireEvent } from '@testing-library/react';
// import LineChartComponent from './LineChartComponent';
// import { useStockWebSocketContext } from '@/components/StockSummary/StockSummaryProvider';
// import { msToDatetime } from '@/utils';

// Mock the context
// jest.mock('@/components/StockSummary/StockSummaryProvider', () => ({
//   useStockWebSocketContext: jest.fn(),
// }));

// Mock utils
// jest.fn(msToDatetime).mockImplementation((ms) => new Date(ms).toISOString());
// (msToDatetime) = jest.mockImplementation((ms) => new Date(ms).toISOString());

// jest.mock('@/utils', () => ({
//   msToDatetime: jest.fn(),
// }));


// describe('LineChartComponent', () => {
//   Setup default mock values
//   const mockDataBufferRef = { current: [] as any[] };
//   const mockLastUpdateTimeRef = { current: null };
//   const mockSetStockSummary = jest.fn();
//   const mockSetClearChart = jest.fn();

//   beforeEach(() => {
//     jest.clearAllMocks();
//     jest.useFakeTimers();

//     Default context values
//     (useStockWebSocketContext as jest.Mock).mockReturnValue({
//       dataBufferRef: mockDataBufferRef,
//       lastUpdateTimeRef: mockLastUpdateTimeRef,
//       pauseChart: false,
//       chartTimeWindow: 60000, // 1 minute
//       chartUpdateInterval: 1000, // 1 second
//       setStockSummary: mockSetStockSummary,
//       clearChart: false,
//       setClearChart: mockSetClearChart,
//       MAX_DATA_POINTS: 100,
//     });

//     Default datetime formatter
//     (msToDatetime as jest.Mock).mockImplementation((ms) => new Date(ms).toISOString());
//   });

//   afterEach(() => {
//     jest.useRealTimers();
//   });

//   test('renders the chart component', () => {
//     render(<LineChartComponent />);
//     console.log(screen)
//     expect(screen.getByTestId('mock-line-chart')).toBeInTheDocument();
//   });

//   test('initializes with empty chart data', () => {
//     render(<LineChartComponent />);
//     const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');

//     expect(chartData.labels).toEqual([]);
//     expect(chartData.datasets[0].data).toEqual([]);
//     expect(chartData.datasets[0].label).toBe('Total Price');
//   });

//   test('updates chart when new data is available in buffer', () => {
//     Setup mock data
//     const mockTimestamp = 1617235200000; // April 1, 2021
//     const mockData = {
//       payload: {
//         event_timestamp: mockTimestamp,
//         total_price: 150.5,
//         symbol_prices: { AAPL: 120.5, MSFT: 30 }
//       }
//     };

//     mockDataBufferRef.current = [mockData];

//     render(<LineChartComponent />);

//     Trigger the interval
//     act(() => {
//       jest.advanceTimersByTime(1000);
//     });

//     Check if setStockSummary was called with the latest data
//     expect(mockSetStockSummary).toHaveBeenCalledWith(mockData);

//     Get and parse the chart data
//     const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');

//     Verify the chart data was updated
//     expect(chartData.datasets[0].data).toContain(150.5);
//     expect(chartData.labels.length).toBe(1);
//   });

//   test('clears chart data when clearChart is true', () => {
//     Setup initial data
//     const mockData = {
//       payload: {
//         event_timestamp: 1617235200000,
//         total_price: 150.5,
//         symbol_prices: { AAPL: 120.5, MSFT: 30 }
//       }
//     };

//     mockDataBufferRef.current = [mockData];

//     Render with data
//     const { rerender } = render(<LineChartComponent />);

//     Trigger the interval to update chart
//     act(() => {
//       jest.advanceTimersByTime(1000);
//     });

//     Update mock to trigger clearChart
//     (useStockWebSocketContext as jest.Mock).mockReturnValue({
//       dataBufferRef: mockDataBufferRef,
//       lastUpdateTimeRef: mockLastUpdateTimeRef,
//       pauseChart: false,
//       chartTimeWindow: 60000,
//       chartUpdateInterval: 1000,
//       setStockSummary: mockSetStockSummary,
//       clearChart: true,
//       setClearChart: mockSetClearChart,
//       MAX_DATA_POINTS: 100,
//     });

//     Re-render component with clearChart set to true
//     rerender(<LineChartComponent />);

//     Verify the chart data was cleared
//     const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
//     expect(chartData.labels).toEqual([]);
//     expect(chartData.datasets[0].data).toEqual([]);

//     Verify setClearChart was called to reset clearChart to false
//     expect(mockSetClearChart).toHaveBeenCalledWith(false);
//   });

//   test('does not update chart when paused', () => {
//     Setup mock to have pause enabled
//     (useStockWebSocketContext as jest.Mock).mockReturnValue({
//       dataBufferRef: mockDataBufferRef,
//       lastUpdateTimeRef: mockLastUpdateTimeRef,
//       pauseChart: true,
//       chartTimeWindow: 60000,
//       chartUpdateInterval: 1000,
//       setStockSummary: mockSetStockSummary,
//       clearChart: false,
//       setClearChart: mockSetClearChart,
//       MAX_DATA_POINTS: 100,
//     });

//     Add mock data to buffer
//     mockDataBufferRef.current = [{
//       payload: {
//         event_timestamp: 1617235200000,
//         total_price: 150.5,
//         symbol_prices: { AAPL: 120.5, MSFT: 30 }
//       }
//     }];

//     render(<LineChartComponent />);

//     Trigger the interval
//     act(() => {
//       jest.advanceTimersByTime(1000);
//     });

//     Verify setStockSummary was not called
//     expect(mockSetStockSummary).not.toHaveBeenCalled();

//     Verify chart data remains empty
//     const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
//     expect(chartData.datasets[0].data).toEqual([]);
//   });

//   test('updates selected data point when chart is paused and point is clicked', () => {
//     Setup mock to have pause enabled
//     (useStockWebSocketContext as jest.Mock).mockReturnValue({
//       dataBufferRef: mockDataBufferRef,
//       lastUpdateTimeRef: mockLastUpdateTimeRef,
//       pauseChart: true,
//       chartTimeWindow: 60000,
//       chartUpdateInterval: 1000,
//       setStockSummary: mockSetStockSummary,
//       clearChart: false,
//       setClearChart: mockSetClearChart,
//       MAX_DATA_POINTS: 100,
//     });

//     Mock getElementsAtEventForMode to return a clicked element
//     mockGetElementsAtEventForMode.mockReturnValue([{ index: 0, datasetIndex: 0 }]);

//     Mock stock summary data that would be in the chart
//     const mockStockSummary = {
//       payload: {
//         event_timestamp: 1617235200000,
//         total_price: 150.5,
//         symbol_prices: { AAPL: 120.5, MSFT: 30 }
//       }
//     };

//     Create a mock chart instance with the necessary data
//     const mockChartInstance = {
//       getElementsAtEventForMode: mockGetElementsAtEventForMode,
//       data: {
//         datasets: [{
//           extraInfo: [{ stockSummary: mockStockSummary }]
//         }]
//       }
//     };

//     Mock the useRef hook
//     const originalUseRef = React.useRef;
//     React.useRef = jest.fn().mockReturnValue({ current: mockChartInstance });

//     render(<LineChartComponent />);

//     Simulate click event
//     const chart = screen.getByTestId('mock-line-chart');
//     fireEvent.click(chart);

//     Verify setStockSummary was called with the correct data
//     expect(mockGetElementsAtEventForMode).toHaveBeenCalled();
//     expect(mockSetStockSummary).toHaveBeenCalledWith(mockStockSummary);

//     Restore original useRef
//     React.useRef = originalUseRef;
//   });

//   test('limits data points to MAX_DATA_POINTS', () => {
//     Create more data points than MAX_DATA_POINTS
//     const maxPoints = 3; // Use a small number for testing

//     Override MAX_DATA_POINTS in the context
//     (useStockWebSocketContext as jest.Mock).mockReturnValue({
//       dataBufferRef: mockDataBufferRef,
//       lastUpdateTimeRef: mockLastUpdateTimeRef,
//       pauseChart: false,
//       chartTimeWindow: 60000,
//       chartUpdateInterval: 1000,
//       setStockSummary: mockSetStockSummary,
//       clearChart: false,
//       setClearChart: mockSetClearChart,
//       MAX_DATA_POINTS: maxPoints,
//     });

//     Generate 5 data points (more than our maxPoints of 3)
//     const mockDataPoints = Array.from({ length: 5 }, (_, i) => ({
//       payload: {
//         event_timestamp: 1617235200000 + (i * 10000),
//         total_price: 100 + i * 10,
//         symbol_prices: { AAPL: 80 + i * 5, MSFT: 20 + i * 5 }
//       }
//     }));

//     mockDataBufferRef.current = mockDataPoints;

//     render(<LineChartComponent />);

//     Advance time to trigger multiple updates
//     act(() => {
//       jest.advanceTimersByTime(5000);
//     });

//     Get chart data
//     const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');

//     Verify the chart data is limited to maxPoints
//     expect(chartData.datasets[0].data.length).toBeLessThanOrEqual(maxPoints);
//     expect(chartData.labels.length).toBeLessThanOrEqual(maxPoints);

//     Verify we have the latest data points, not the oldest ones
//     expect(chartData.datasets[0].data).toContain(mockDataPoints[mockDataPoints.length - 1].payload.total_price);
//   });
// });
