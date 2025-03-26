import React from 'react';
import { WebSocketProvider } from '@/contexts/WebSocketContext';
import ChatContainer from '@/components/ChatContainer';
import StockSummaryComponent from '@/components/StockSummaryComponent'

export default function Home() {
  return (
    <App/>
  )
}

const App: React.FC = () => {
  // return (
  //   <WebSocketProvider url="ws://localhost:8000/stock_summary/ws">
  //     <ChatContainer />
  //   </WebSocketProvider>
  // );
  return (
    <StockSummaryComponent />
  );
};


