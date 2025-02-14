import utils.settings as UTILS
from utils.utilities import Utilities
from set_kafka_topics.set_kafka_topics import SetUpKafkaTopics

class AddKafkaTopics:
    """
    A class for managing Kafka topics and schema registration.
    """

    @staticmethod
    def add_kafka_topics(topics: dict[str, str]):
        """
        Adds and registers Kafka topics with their respective schemas.

        :param topics: A dictionary where the keys are topic names and the values are schema file paths.
        :raises Exception: If there is an error in schema registration or topic creation.
        """
        bootstrap_servers = UTILS.BOOTSTRAP_SERVERS
        schema_registry_url = UTILS.SCHEMA_REGISTRY_URL
        setUpKafkaTopics = SetUpKafkaTopics(
            schema_registry_url=schema_registry_url, bootstrap_servers=bootstrap_servers)

        try:
            for topic_name, schema_path in topics.items():
                schema = Utilities.load_schema(schema_path)
                setUpKafkaTopics.register_schema(
                    avro_schema=schema, topic_name=topic_name)
        except Exception as e:
            raise Exception(f"Error registering schema: {e}")

        try:
            setUpKafkaTopics.register_topic(
                topic_names=topics.keys(),
                partitions=int(UTILS.KAFKA_PARTITIONS),
                replication_factor=int(UTILS.KAFKA_REPLICATION_FACTOR)
            )
        except Exception as e:
            raise Exception(f"Error registering topic: {e}")
