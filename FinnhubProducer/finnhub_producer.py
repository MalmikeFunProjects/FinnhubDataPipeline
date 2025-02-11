import time
import numpy as np

from gather_data.finnhub_gather_data import FinnhubGatherData
from gather_data.finnhub_trades import FinnhubTrades
from handlers.kafka_producer import KafkaProducer
import utils.settings as UTILS


class FinnhubProducer:
  def __init__(self):
    self.finnhub_gather_data = FinnhubGatherData()
    self.company_profiles = self.finnhub_gather_data.get_company_profiles()
    # self.tickers = self.finnhub_gather_data.get_us_big_tech_tickers(self.company_profiles).unique()
    self.tickers = np.array(UTILS.TEST_TICKERS) # These symbols seem to work even when other symbols are failing

  def publishSP500CompanyProfiles(self):
    config = {
      'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,
      'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,
      'schema.source': UTILS.SCHEMA_SP500_COMPANY_PROFILES
    }
    producer = KafkaProducer(props=config)
    producer.publishUsingDataFrames(topic=UTILS.KAFKA_TOPIC_COMPANY_PROFILES,
                            df=self.company_profiles,
                            key=self.finnhub_gather_data.sp500_key_name)

  def publishStockSymbols(self):
    config = {
      'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,
      'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,
      'schema.source': UTILS.SCHEMA_STOCK_SYMBOLS
    }
    stock_symbols = self.tickers.tolist()
    key="Symbol"
    producer = KafkaProducer(props=config)
    producer.publishUsingList(topic=UTILS.KAFKA_TOPIC_SYMBOLS,
                            items=stock_symbols,
                            key=key)

  def publishTrades(self):
    config = {
      'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,
      'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,
      'schema.source': UTILS.SCHEMA_TRADES
    }
    producer = KafkaProducer(props=config)
    trades = FinnhubTrades(tickers=self.tickers, producer=producer)
    trades.start_websocket()

if __name__ == "__main__":
  finnhubProducer = FinnhubProducer()
  # finnhubProducer.publishSP500CompanyProfiles()
  finnhubProducer.publishStockSymbols()
  finnhubProducer.publishTrades()
