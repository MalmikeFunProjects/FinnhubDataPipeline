from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class StockPrice1s(Model):
    __keyspace__ = "market"
    __table_name__ = "stock_price_1s"
    event_timestamp = columns.BigInt(primary_key=True, partition_key=True)
    symbol = columns.Text(primary_key=True)
    count = columns.Integer()
    avg_price = columns.Double()
