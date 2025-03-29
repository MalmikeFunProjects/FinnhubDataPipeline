import React from 'react';
import StockSummaryComponent from '@/components/StockSummary/StockSummary'

export default function Home() {
  return (
    <App/>
  )
}

const App: React.FC = () => {
  return (
    <StockSummaryComponent />
  );
};


