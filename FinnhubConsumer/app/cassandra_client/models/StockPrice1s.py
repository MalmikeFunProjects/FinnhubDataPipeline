import datetime
import time
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

    def __init__(self, *args, **kwargs):
        event_timestamp = kwargs.get('event_timestamp')
        partition_date = kwargs.get('partition_date')
        insertion_timestamp = kwargs.get('insertion_timestamp')
        if  not partition_date and event_timestamp is not None:
            partition_date = datetime.date.fromtimestamp(event_timestamp / 1000)
            kwargs['partition_date'] = partition_date
        if not insertion_timestamp:
            insertion_timestamp = int(time.time() * 1000)
            kwargs['insertion_timestamp'] = insertion_timestamp
        super().__init__(*args, **kwargs)

