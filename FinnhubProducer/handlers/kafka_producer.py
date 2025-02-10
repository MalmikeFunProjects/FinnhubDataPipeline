import time
from typing import Any
import pandas as pd
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry.avro import AvroSerializer

from utils.utilities import Utilities
import traceback


class KafkaProducer:
  def __init__(self, props: dict):
    schema = Utilities.load_schema(props['schema.source'])
    schema_registry_props = {'url': props['schema_registry.url']}
    schema_registry_client = SchemaRegistryClient(schema_registry_props)
    self.key_serializer = StringSerializer('utf-8')
    self.value_serializer = AvroSerializer(schema_registry_client, schema)

    producer_props = {'bootstrap.servers': props['bootstrap.servers']}
    self.producer = SerializingProducer(producer_props)

  def publishToKafka(self, topic: str, key: str, record: dict[Any, Any]):
    try:
      self.producer.produce(topic= topic,
        key=self.key_serializer(key),
        value=self.value_serializer(record, SerializationContext(topic=topic, field=MessageField.VALUE)),
        on_delivery=Utilities.delivery_report
        )
    except KeyboardInterrupt as err:
      raise err
    except Exception as err:
      raise err

  def publishUsingDataFrames(self, topic: str, df: pd.DataFrame|list[str], key: str):
    records = df.to_dict(orient="records")
    for single_record in records:
      try:
        self.publishToKafka(topic=topic, key=single_record[key], record=single_record)
      except KeyboardInterrupt:
        break
      except Exception as err:
        print(f"Exception while producing record - {single_record}: {err}")
    self.producer.flush()

  def publishUsingList(self, topic:str, items: list, key: str):
    timestamp = int(time.time())
    for item in items:
      record = {key: item, "Timestamp": int(time.time())}
      try:
        self.publishToKafka(topic=topic, key=key, record=record)
      except Exception as err:
        traceback.print_exc()
        print(f"Exception while producing record - {record}: {err}")
      self.producer.flush()
