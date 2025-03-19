from pydantic import BaseModel
from utils.CassandraMapper import CassandraMapper
from database.cassandra_client import CassandraClient
from database.cassandra_config import get_cassandra_config
from database.models import CompanySymbol


class CompanySymbolService():
    def __init__(self, CustomModel: type[BaseModel]):
        self.cassandra_config = get_cassandra_config()
        self.cassandra_mapper = CassandraMapper(CustomModel)
        self.sync_company_symbols()
        self.data_filter_properties = {}

    def sync_company_symbols(self):
        with CassandraClient(self.cassandra_config) as cassandra_client:
            cassandra_client.sync_table(CompanySymbol)

    def get_company_symbols(self) -> list[type[BaseModel]] | None:
        with CassandraClient(self.cassandra_config) as cassandra_client:
            try:
                data = cassandra_client.get_all_items_by_model(CustomModel=CompanySymbol)
                if not data:
                    return None
                company_symbols = list(data)
                print(f"Size of records: {len(company_symbols)}")
                return self.cassandra_mapper.to_pydantic_list(company_symbols)
            except Exception as e:
                print(e)
