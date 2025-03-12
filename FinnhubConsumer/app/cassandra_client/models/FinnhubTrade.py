from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class FinnhubTrade(Model):
    __keyspace__ = "market"
    __table_name__ = "finnhub_trades"
    event_timestamp = columns.BigInt(primary_key=True, partition_key=True)
    symbol = columns.Text(primary_key=True)
    price = columns.Double()
