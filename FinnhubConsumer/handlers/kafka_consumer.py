import os
from typing import Dict, Generator, List

from confluent_kafka import DeserializingConsumer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer


class KafkaConsumer:
    def __init__(self, props: Dict):
        schema_registry_props = {'url': props['schema_registry.url']}
        schema_registry_client = SchemaRegistryClient(schema_registry_props)
        avro_deserializer = AvroDeserializer(schema_registry_client=schema_registry_client)

        consumer_props = {
            'bootstrap.servers': props['bootstrap.servers'],
            'group.id': 'malmike.finnhub.avro.consumer.2',
            'key.deserializer': avro_deserializer,
            'value.deserializer': avro_deserializer,
            'auto.offset.reset': "earliest"
        }
        self.consumer = DeserializingConsumer(consumer_props)

    def consume_from_kafka(self, topics: List[str]) -> Generator[tuple, None, None]:
        self.consumer.subscribe(topics=topics)
        while True:
            try:
                # SIGINT can't be handled when polling, limit timeout to 1 second.
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print('End of partition reached')
                        continue
                    else:
                        print(f"Error: {msg.error()}")
                        break
                topic = msg.topic()
                key = msg.key()
                record = msg.value()
                if record is not None:
                    yield(topic, key, record)
                else:
                    yield(topic, key, None)
            except KeyboardInterrupt:
                break
        self.consumer.close()
