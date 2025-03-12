from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class LatestPrice(Model):
    __keyspace__ = "market"
    __table_name__ = "latest_prices"
    event_timestamp = columns.BigInt(primary_key=True, partition_key=True)
    symbol = columns.Text(primary_key=True)
    last_price = columns.Double()
