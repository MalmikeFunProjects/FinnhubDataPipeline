from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
import uuid
import datetime

class StreamData(Model):
    __keyspace__ = "market"
    __table_name__ = "stream_data"

    timebucket = columns.Text(primary_key=True, partition_key=True)
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    last_updated = columns.DateTime(default=datetime.datetime.now)
    value = columns.Float()

    @classmethod
    def generate_timebucket(cls, dt=None):
        """Generate a timebucket from a datetime object for better data partitioning"""
        if dt is None:
            dt = datetime.datetime.now()
        return f"{dt.year}-{dt.month:02d}-{dt.day:02d}-hour-{dt.hour:02d}"
