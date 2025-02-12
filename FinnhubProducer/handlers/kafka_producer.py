import time
from typing import Any
import pandas as pd
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient, SchemaRegistryError
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry.avro import AvroSerializer

from utils.utilities import Utilities
import traceback


class KafkaProducer:
    def __init__(self, props: dict):
        schema_registry_props = {'url': props['schema_registry.url']}
        self.schema_registry_client = SchemaRegistryClient(
            schema_registry_props)

        producer_props = {'bootstrap.servers': props['bootstrap.servers']}
        self.producer = SerializingProducer(producer_props)

        self.schema_registry_client.get_subjects()

        self.key_serializer = StringSerializer('utf-8')
        schema = self._get_schema_from_registry(
            props['schema.name'], props.get('schema.subject'))
        self.value_serializer = AvroSerializer(
            schema_registry_client=self.schema_registry_client, schema_str=schema)

    def _get_schema_from_registry(self, schema_name: str, subject: str = None):
        """Retrieves the schema from the Schema Registry."""
        try:
            if subject is None:
                subject = f"{schema_name}-value"
            versions = self.schema_registry_client.get_latest_version(subject)
            return self.schema_registry_client.get_schema(
                schema_id=versions.schema_id, subject_name=subject).schema_str
        except SchemaRegistryError as e:
            print(f"Error retrieving schema from registry: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

    def publishToKafka(self, topic: str, key: str, record: dict[Any, Any]):
        try:
            self.producer.produce(topic=topic,
                                  key=self.key_serializer(key),
                                  value=self.value_serializer(record, SerializationContext(
                                      topic=topic, field=MessageField.VALUE)),
                                  on_delivery=Utilities.delivery_report
                                  )
        except KeyboardInterrupt as err:
            raise err
        except Exception as err:
            raise err

    def publishUsingDataFrames(self, topic: str, df: pd.DataFrame | list[str], key: str):
        records = df.to_dict(orient="records")
        for single_record in records:
            try:
                self.publishToKafka(
                    topic=topic, key=single_record[key], record=single_record)
            except KeyboardInterrupt:
                break
            except Exception as err:
                print(
                    f"Exception while producing record - {single_record}: {err}")
        self.producer.flush()

    def publishUsingList(self, topic: str, items: list, key: str):
        timestamp = int(time.time())
        for item in items:
            record = {key: item, "Timestamp": int(time.time())}
            try:
                self.publishToKafka(topic=topic, key=key, record=record)
            except Exception as err:
                traceback.print_exc()
                print(f"Exception while producing record - {record}: {err}")
            self.producer.flush()
