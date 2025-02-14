from confluent_kafka import KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.error import SchemaRegistryError


class SetUpKafkaTopics:
    """
    A class that handles the setup of Kafka topics and schema registration for those topics in a Kafka cluster.

    Attributes:
        admin_client (AdminClient): Kafka admin client for managing topics.
        schema_registry_client (SchemaRegistryClient): Client for interacting with the schema registry.
        schema_registry_url (str): URL for connecting to the schema registry.
    """

    def __init__(self, schema_registry_url: str, bootstrap_servers: str):
        """
        Initializes the class with the Kafka bootstrap servers and schema registry URL.

        Parameters:
            schema_registry_url (str): The URL of the schema registry.
            bootstrap_servers (str): The Kafka bootstrap server addresses.
        """
        # Admin client for Topic Creation
        admin_client_config = {"bootstrap.servers": bootstrap_servers}
        self.admin_client = AdminClient(admin_client_config)

        # Schema registry client
        self.schema_registry_url = schema_registry_url
        schema_registry_config = {"url": schema_registry_url}
        self.schema_registry_client = SchemaRegistryClient(
            schema_registry_config)

    def check_topic_exists(self, topic_name: str):
        """
        Checks whether a Kafka topic exists.

        Parameters:
            topic_name (str): The name of the topic to check.

        Returns:
            bool: True if the topic does not exist, False otherwise.
        """
        topic_list = self.admin_client.list_topics().topics
        return topic_name not in topic_list

    def register_schema(self, avro_schema: str, topic_name: str):
        """
        Registers an Avro schema for a specific Kafka topic in the schema registry.

        Parameters:
            avro_schema (str): The Avro schema as a string.
            topic_name (str): The Kafka topic name to register the schema for.

        Raises:
            SchemaRegistryError: If there is an error while registering the schema in the schema registry.
            Exception: If any other error occurs.
        """
        try:
            schema = Schema(avro_schema, schema_type="AVRO")
            subject_name = f"{topic_name}-value"
            schema_id = self.schema_registry_client.register_schema(
                subject_name, schema=schema)
            print(f"Avro schema registered with ID: {schema_id} for subject {subject_name}")
        except SchemaRegistryError as e:
            raise e  # Raise the error if the schema is invalid
        except Exception as e:
            raise e  # Raise any other exceptions

    def register_topic(self,
                       topic_names: list[str],
                       partitions: int = 1,
                       replication_factor: int = 1):
        """
        Registers new Kafka topics in the Kafka cluster if they do not already exist.

        Parameters:
            topic_names (list[str]): A list of topic names to create.
            partitions (int, optional): The number of partitions for each topic. Defaults to 1.
            replication_factor (int, optional): The replication factor for each topic. Defaults to 1.

        Raises:
            Exception: If there is an error while creating the topics.
        """
        # Create topic definitions for topics that do not exist
        topic_definitions = [NewTopic(topic=topic_name,
                                      num_partitions=partitions,
                                      replication_factor=replication_factor)
                                      for topic_name in topic_names
                                      if self.check_topic_exists(topic_name=topic_name)]

        # If there are topics to create, proceed with creation
        if len(topic_definitions) > 0:
            try:
                topics = self.admin_client.create_topics(topic_definitions)
                for topic, future in topics.items():
                    try:
                        future.result()
                        print(f"Topic {topic} created successfully.")
                    except KafkaError as e:
                        print(f"Failed to create topic {topic}: {e}")
            except Exception as e:
                raise e  # Raise any errors encountered during topic creation

    def close_admin_client(self):
        """
        Closes the Kafka admin client to release resources.
        """
        self.admin_client.close()
