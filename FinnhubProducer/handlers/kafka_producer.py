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
        """
        Initializes the KafkaProducer object.

        This constructor sets up the schema registry client, the Kafka producer,
        and the Avro serializer for the record values. It also ensures that the schema
        is fetched from the schema registry.

        Parameters:
            props (dict): A dictionary containing configuration properties for the producer and schema registry.
                          This includes 'bootstrap.servers', 'schema_registry.url', and 'schema.name'.
        """
        # Configure the schema registry client with the provided URL
        schema_registry_props = {'url': props['schema_registry.url']}
        self.schema_registry_client = SchemaRegistryClient(
            schema_registry_props)

        # Configure the producer with the provided bootstrap server
        producer_props = {'bootstrap.servers': props['bootstrap.servers']}
        self.producer = SerializingProducer(producer_props)

        # Retrieve the subjects (schemas) from the schema registry
        self.schema_registry_client.get_subjects()

        # Serializer for the key (string format)
        self.key_serializer = StringSerializer('utf-8')

        # Retrieve the Avro schema from the registry for the given schema name
        schema = self._get_schema_from_registry(
            props['schema.name'], props.get('schema.subject'))
        # Create an Avro serializer for the value using the retrieved schema
        self.value_serializer = AvroSerializer(
            schema_registry_client=self.schema_registry_client, schema_str=schema)

    def _get_schema_from_registry(self, schema_name: str, subject: str = None):
        """
        Retrieves the Avro schema from the Schema Registry.

        This method fetches the latest version of the schema for a given subject
        from the schema registry and returns it.

        Parameters:
            schema_name (str): The name of the schema to retrieve.
            subject (str, optional): The schema subject name (default is None, which uses the default naming convention).

        Returns:
            str: The Avro schema string retrieved from the registry.

        Raises:
            SchemaRegistryError: If there is an issue with the schema registry.
            Exception: If any unexpected error occurs during schema retrieval.
        """
        try:
            if subject is None:
                subject = f"{schema_name}-value"
            # Retrieve the latest version of the schema for the specified subject
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
        """
        Publishes a record to Kafka.

        This method serializes the key and value and sends the record to the specified Kafka topic.
        It also handles any exceptions and invokes a callback for delivery reports.

        Parameters:
            topic (str): The Kafka topic to send the record to.
            key (str): The key used to partition the Kafka messages.
            record (dict): The record (message) to be sent to Kafka, represented as a dictionary.

        Raises:
            Exception: If any exception occurs while producing the record to Kafka.
        """
        try:
            # Produce the message to Kafka
            self.producer.produce(topic=topic,
                                  key=self.key_serializer(key),
                                  value=self.value_serializer(record, SerializationContext(
                                      topic=topic, field=MessageField.VALUE)),
                                  on_delivery=Utilities.delivery_report  # Callback function for delivery report
                                  )
        except KeyboardInterrupt as err:
            raise err
        except Exception as err:
            raise err

    def publishUsingDataFrames(self, topic: str, df: pd.DataFrame | list[str], key: str):
        """
        Publishes records from a DataFrame to Kafka.

        This method converts the provided DataFrame into a list of records and sends
        each record to Kafka individually. It uses the specified key column for partitioning.

        Parameters:
            topic (str): The Kafka topic to publish the records to.
            df (pd.DataFrame or list): The DataFrame or list of data records to publish.
            key (str): The column name in the DataFrame to use as the key for Kafka messages.

        Raises:
            Exception: If any exception occurs while producing the records to Kafka.
        """
        # Convert the DataFrame into a list of dictionaries (records)
        records = df.to_dict(orient="records")
        for single_record in records:
            try:
                # Publish each record to Kafka
                self.publishToKafka(
                    topic=topic, key=single_record[key], record=single_record)
            except KeyboardInterrupt:
                break  # Exit the loop if interrupted
            except Exception as err:
                print(f"Exception while producing record - {single_record}: {err}")
        # Ensure that all messages are flushed (sent) before exiting
        self.producer.flush()

    def publishUsingList(self, topic: str, items: list, key: str):
        """
        Publishes records from a list of items to Kafka.

        This method generates a record for each item in the list, including a timestamp,
        and sends it to Kafka. It uses the provided key for partitioning the records.

        Parameters:
            topic (str): The Kafka topic to publish the records to.
            items (list): A list of items to be published as records to Kafka.
            key (str): The key to use for partitioning Kafka messages (each item is assigned this key).

        Raises:
            Exception: If any exception occurs while producing the records to Kafka.
        """
        timestamp = int(time.time())  # Generate a timestamp for each record
        for item in items:
            # Create a record for each item with a timestamp
            record = {key: item, "Timestamp": int(time.time())}
            try:
                # Publish the record to Kafka
                self.publishToKafka(topic=topic, key=key, record=record)
            except Exception as err:
                traceback.print_exc()  # Print the stack trace for debugging
                print(f"Exception while producing record - {record}: {err}")
            # Ensure that all messages are flushed (sent) before exiting
            self.producer.flush()
