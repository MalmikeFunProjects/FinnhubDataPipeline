
from .cassandra_client import CassandraConfig, CassandraClient
from cassandra.cqlengine.models import Model


class SetupClient:
    def __init__(self, config: CassandraConfig):
        self.config = config

    def setup_tables(self, CustomModels: dict[str, type[Model]], logging):
        config = self.config

        # Ensure the table schema is synchronized before writing data
        with CassandraClient(config) as setup_client:
            for name, custom_model in CustomModels.items():
                setup_client.sync_table(custom_model)
                logging.info(f"{name} table schema synchronized")

