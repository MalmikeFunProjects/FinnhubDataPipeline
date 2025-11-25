from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
import uuid

class StockPrice1s(Model):
    __keyspace__ = "market"
    __table_name__ = "stock_price_1s"
    # Partition by day to allow efficient time-based retrieval
    partition_date = columns.Date(primary_key=True, partition_key=True)
    event_timestamp = columns.BigInt(primary_key=True, clustering_order="ASC")
    insertion_timestamp = columns.BigInt(index=True)
    # Unique ID for deduplication
    processing_id = columns.UUID(primary_key=True, clustering_order="ASC", default=uuid.uuid4)
    symbol = columns.Text(primary_key=True)
    count = columns.Integer()
    avg_price = columns.Double()
    is_processed = columns.Boolean(default=False)
