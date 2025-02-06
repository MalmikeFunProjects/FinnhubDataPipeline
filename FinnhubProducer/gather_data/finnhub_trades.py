import json
import pandas as pd
from handlers.kafka_producer import KafkaProducer
from utils.settings import FINNHUB_API_KEY, KAFKA_TOPIC_TRADES
import websocket
import traceback

from utils.utilities import Utilities


class FinnhubTrades:
  def __init__(self,
               tickers: pd.Series,
               producer: KafkaProducer,
               max_messages: int = None):
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
    try:
      data = json.loads(message)
      df = pd.DataFrame(data["data"])
      Utilities.rename_df_columns(df, self.column_map)
      self.producer.publishToKafka(topic=KAFKA_TOPIC_TRADES,
                            df=df,
                            key=self.key_name)
      self.message_count += 1
      if(self.max_messages and self.message_count >= self.max_messages):
        print(f"Recieved {self.max_messages} messages. Closing connection")
        ws.close()
    except json.JSONDecodeError as e:
      print(f"Error decoding JSON: {e}")
    except KeyError as e:
      print(f"Missing expected key: {e}")

  def on_error(self, ws, error):
    traceback.print_exc()
    raise error
    # print(f"Error: {error}")

  def on_close(self, ws, close_status_code, close_msg):
    print(f"### WebSocket closed ### Code: {close_status_code}, Message: {close_msg}")

  def on_open(self, ws):
    for ticker in self.tickers:
      ws.send(f'{{"type":"subscribe", "symbol":"{ticker}"}}')

  def start_websocket(self):
    if(self.tickers is None):
      raise ValueError(f"No tickers submitted")

    self.ws = websocket.WebSocketApp(
      f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}",
      on_message = self.on_message,
      on_error = self.on_error,
      on_close = self.on_close
    )
    self.ws.on_open = self.on_open
    self.ws.run_forever()

