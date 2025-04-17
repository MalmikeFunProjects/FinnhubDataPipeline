
from app.cassandra_client.cassandra_client import CassandraConfig, CassandraClient
from cassandra.cqlengine.models import Model

from app.utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("setup_client", log_to_console=True)


class SetupClient:
    def __init__(self, config: CassandraConfig):
        self.config = config

    def setup_tables(self, CustomModels: dict[str, type[Model]]):
        config = self.config

        # Ensure the table schema is synchronized before writing data
        with CassandraClient(config) as setup_client:
            for name, custom_model in CustomModels.items():
                setup_client.sync_table(custom_model)
                logger.info(f"{name} table schema synchronized")

