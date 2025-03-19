from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
import uuid

class StockSummary(Model):
    __keyspace__ = "market"
    __table_name__ = "stock_summary"
    # Partition by day to allow efficient time-based retrieval
    partition_date = columns.Date(primary_key=True, partition_key=True)
    event_timestamp = columns.BigInt(primary_key=True, clustering_order="ASC")
    # Insertion timestamp to track when data was actually added
    insertion_timestamp = columns.BigInt(index=True)
    # Unique ID for deduplication
    processing_id = columns.UUID(primary_key=True, clustering_order="ASC", default=uuid.uuid4)
    total_price = columns.Double()
    symbols = columns.List(columns.Text())
    is_processed = columns.Boolean(default=False)
