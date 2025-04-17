from pydantic import BaseModel
from app.utils.CassandraMapper import CassandraMapper
from app.database.cassandra_client import CassandraClient
from app.database.cassandra_config import get_cassandra_config
from app.database.models import CompanySymbol as CompanySymbolModel
from app.utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("company_symbol_service", log_to_console=True)


class CompanySymbolService():
    def __init__(self, pydantic_model: type[BaseModel]):
        self.cassandra_config = get_cassandra_config()
        self.cassandra_mapper = CassandraMapper(pydantic_model)
        self._sync_company_symbol_table()

    def _sync_company_symbol_table(self):
        """Ensure the company_symbol table is synced with Cassandra"""
        try:
            with CassandraClient(self.cassandra_config) as cassandra_client:
                cassandra_client.sync_table(CompanySymbolModel)
                logger.info("Latest price table synced successfully")
        except Exception as e:
            logger.error(f"Failed to sync latest price table: {str(e)}")
            raise

    def get_company_symbol(self) -> list[type[BaseModel]] | None:
        """
        Get company symbol data
        """
        try:
            with CassandraClient(self.cassandra_config) as cassandra_client:
                data = cassandra_client.get_all_items(model_class=CompanySymbolModel)
                if not data:
                    logger.info(f"No symbol data found")
                    return []
                company_symbols = list(data)
                logger.info(f"Size of company symbols records: {len(company_symbols)}")
                return self.cassandra_mapper.to_pydantic_list(company_symbols)
        except Exception as e:
            logger.exception(f"Error getting company symbols: {str(e)}")
            raise
