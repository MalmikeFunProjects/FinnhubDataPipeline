const mockGetElementsAtEventForMode = jest.fn();
module.exports = {
  Chart: {
    register: jest.fn(),
    getElementsAtEventForMode: mockGetElementsAtEventForMode,
    data:{ datasets: [] },
  },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  PointElement: jest.fn(),
  LineElement: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn(),
  Filler: jest.fn()
};
