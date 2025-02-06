import pandas as pd
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry.avro import AvroSerializer

from utils.utilities import Utilities

class KafkaProducer:
  def __init__(self, props: dict):
    schema = Utilities.load_schema(props['schema.source'])
    schema_registry_props = {'url': props['schema_registry.url']}
    schema_registry_client = SchemaRegistryClient(schema_registry_props)
    self.key_serializer = StringSerializer('utf-8')
    self.value_serializer = AvroSerializer(schema_registry_client, schema)

    producer_props = {'bootstrap.servers': props['bootstrap.servers']}
    self.producer = SerializingProducer(producer_props)

  def publishToKafka(self, topic: str, df: pd.DataFrame, key: str):
    records = df.to_dict(orient="records")
    for single_record in records:
      try:
        self.producer.produce(topic= topic,
                              key=self.key_serializer(single_record[key]),
                              value=self.value_serializer(single_record, SerializationContext(topic=topic, field=MessageField.VALUE)),
                              on_delivery=Utilities.delivery_report
                              )
      except KeyboardInterrupt:
        break
      except Exception as err:
        print(f"Exception while producing record - {single_record}: {err}")

    self.producer.flush()
