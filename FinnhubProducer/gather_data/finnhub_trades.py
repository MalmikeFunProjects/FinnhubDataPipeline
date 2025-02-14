import json
from numpy import ndarray
import pandas as pd
from handlers.kafka_producer import KafkaProducer
from utils.settings import FINNHUB_API_KEY, KAFKA_TOPIC_TRADES
import websocket
import traceback

from utils.utilities import Utilities

class FinnhubTrades:
    """
    A class to subscribe to real-time trade data from Finnhub's WebSocket API and publish the data to a Kafka topic.

    Attributes:
        tickers (ndarray): List of ticker symbols to subscribe to.
        producer (KafkaProducer): Kafka producer instance for publishing messages.
        max_messages (int, optional): Maximum number of messages to process before closing the WebSocket connection.
        ws (websocket.WebSocketApp): WebSocket client instance.
        message_count (int): Counter for the number of messages received.
        column_map (dict): Mapping of Finnhub response keys to desired column names.
        key_name (str): The key used for Kafka partitioning.
    """
    def __init__(self, tickers: ndarray, producer: KafkaProducer, max_messages: int = None):
        """
        Initializes the FinnhubTrades class.

        Parameters:
            tickers (ndarray): Array of stock symbols to subscribe to.
            producer (KafkaProducer): Kafka producer instance.
            max_messages (int, optional): Maximum messages before terminating connection.
        """
        self.tickers = tickers
        self.ws: websocket.WebSocketApp = None
        self.producer = producer
        self.message_count = 0
        self.max_messages = max_messages
        self.column_map = {
            "c": "TradeCondition",
            "p": "Price",
            "s": "Symbol",
            "t": "Timestamp",
            "v": "Volume"
        }
        self.key_name = "Symbol"

    def on_message(self, ws: websocket.WebSocketApp, message):
        """
        Callback function to handle incoming WebSocket messages.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection instance.
            message (str): The received message in JSON format.
        """
        try:
            data = dict(json.loads(message))
            if data["type"] == "ping":
                print(f"Connection failed. Returning {data['type']}.")
            else:
                df = pd.DataFrame(data["data"])
                Utilities.rename_df_columns(df, self.column_map)
                self.producer.publishUsingDataFrames(topic=KAFKA_TOPIC_TRADES,
                                                     df=df,
                                                     key=self.key_name)
                self.message_count += 1

            if self.max_messages and self.message_count >= self.max_messages:
                print(f"Received {self.max_messages} messages. Closing connection.")
                ws.close()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except KeyError as e:
            traceback.print_exc()
            print(f"Missing expected key: {e}")

    def on_error(self, ws, error):
        """
        Callback function to handle errors.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection instance.
            error (Exception): The error encountered.
        """
        traceback.print_exc()
        raise error

    def on_close(self, ws, close_status_code, close_msg):
        """
        Callback function executed when the WebSocket connection is closed.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection instance.
            close_status_code (int): WebSocket close status code.
            close_msg (str): WebSocket close message.
        """
        print(f"### WebSocket closed ### Code: {close_status_code}, Message: {close_msg}")

    def on_open(self, ws):
        """
        Callback function executed when the WebSocket connection is opened.
        Subscribes to trade data for the specified tickers.

        Parameters:
            ws (websocket.WebSocketApp): The WebSocket connection instance.
        """
        for ticker in self.tickers:
            ws.send(f'{{"type":"subscribe", "symbol":"{ticker}"}}')

    def start_websocket(self):
        """
        Initiates the WebSocket connection to Finnhub.

        Raises:
            ValueError: If no tickers are provided.
        """
        if self.tickers is None:
            raise ValueError("No tickers submitted")

        self.ws = websocket.WebSocketApp(
            f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        self.ws.run_forever()
