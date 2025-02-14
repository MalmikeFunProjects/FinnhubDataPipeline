from enum import Enum

class StorageType(Enum):
    """
    Enum representing different types of storage in KSQL.

    Attributes:
        STREAM: Represents KSQL streams.
        TABLE: Represents KSQL tables.
        TOPIC: Represents Kafka topics.
    """
    STREAM = "streams"
    TABLE = "tables"
    TOPIC = "topics"
