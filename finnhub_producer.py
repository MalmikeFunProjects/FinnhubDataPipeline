from finnhub_gather_data import FinnhubGatherData
from finnhub_trades import FinnhubTrades
from kafka_producer import KafkaProducer
from settings import BOOTSTRAP_SERVERS, KAFKA_TOPIC_COMPANY_PROFILES, SCHEMA_REGISTRY_URL, SCHEMA_SP500_COMPANY_PROFILES, SCHEMA_TRADES

class FinnhubProducer:
  def __init__(self):
    self.finnhub_gather_data = FinnhubGatherData()
    self.company_profiles = self.finnhub_gather_data.get_company_profiles()

  def publishSP500CompanyProfiles(self):
    config = {
      'bootstrap.servers': BOOTSTRAP_SERVERS,
      'schema_registry.url': SCHEMA_REGISTRY_URL,
      'schema.source': SCHEMA_SP500_COMPANY_PROFILES
    }
    producer = KafkaProducer(props=config)
    producer.publishToKafka(topic=KAFKA_TOPIC_COMPANY_PROFILES,
                            df=self.company_profiles,
                            key=self.finnhub_gather_data.sp500_key_name)

  def publishTrades(self):
    config = {
      'bootstrap.servers': BOOTSTRAP_SERVERS,
      'schema_registry.url': SCHEMA_REGISTRY_URL,
      'schema.source': SCHEMA_TRADES
    }
    producer = KafkaProducer(props=config)
    tickers = self.finnhub_gather_data.get_us_big_tech_tickers(self.company_profiles)
    trades = FinnhubTrades(tickers=tickers, producer=producer)
    trades.start_websocket()

if __name__ == "__main__":
  finnhubProducer = FinnhubProducer()
  finnhubProducer.publishSP500CompanyProfiles()
  finnhubProducer.publishTrades()
