from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class StockSummary(Model):
    __keyspace__ = "market"
    __table_name__ = "stock_summary"
    event_timestamp = columns.BigInt(primary_key=True)
    total_price = columns.Double()
    symbols = columns.List(columns.Text())
