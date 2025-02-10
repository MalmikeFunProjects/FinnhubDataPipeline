from confluent_kafka import KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.error import SchemaParseException


class SetUpKafkaTopics:
    def __init__(self, schema_registry_url: str, bootstrap_servers: str):
        # Admin client for Topic Creation
        admin_client_config = {"bootstrap.servers": bootstrap_servers}
        self.admin_client = AdminClient(admin_client_config)

        # Schema registry client
        self.schema_registry_url = schema_registry_url
        schema_registry_config = {"url": schema_registry_url}
        self.schema_registry_client = SchemaRegistryClient(
            schema_registry_config)

    def check_topic_exists(self, topic_name: str):
        topic_list = self.admin_client.list_topics().topics
        return topic_name not in topic_list

    def register_schema(self, avro_schema: str, topic_name: str):
        try:
            schema = Schema(avro_schema, schema_type="AVRO")
            subject_name = f"{topic_name}-value"
            schema_id = self.schema_registry_client.register_schema(
                subject_name, schema=schema)
            print(f"Avro schema registered with ID: {
                  schema_id} for subject {subject_name}")
        except SchemaParseException as e:
            # print(f"Avro schema is invalid: {e}")
            raise e
        except Exception as e:
            # print(f"Error registering schema: {e}")
            raise e

    def register_topic(self,
                       topic_names: list[str],
                       partitions: int = 1,
                       replication_factor: int = 1):

        topic_definitions = [NewTopic(topic=topic_name,
                                      num_partitions=partitions,
                                      replication_factor=replication_factor)
                                      for topic_name in topic_names
                                      if self.check_topic_exists(topic_name=topic_name)]
        if(len(topic_definitions) > 0):
          try:
              topics = self.admin_client.create_topics(topic_definitions)
              for topic, future in topics.items():
                  try:
                      future.result()
                      print(f"Topic {topic} created successfully.")
                  except KafkaError as e:
                      print(f"Failed to create topic {topic}: {e}")
          except Exception as e:
              # print(f"An error occurred during topic creation: {e}")
              raise e

    def close_admin_client(self):
        self.admin_client.close()
