import utils.settings as UTILS
from utils.utilities import Utilities
from set_kafka_topics.set_kafka_topics import SetUpKafkaTopics


class AddKafkaTopics:
    @staticmethod
    def add_kafka_topics(topics: dict[str, str]):
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
            raise e

        try:
            setUpKafkaTopics.register_topic(
                topic_names=topics.keys(),
                partitions=int(UTILS.KAFKA_PARTITIONS),
                replication_factor=int(UTILS.KAFKA_REPLICATION_FACTOR)
            )
        except Exception as e:
            raise e
