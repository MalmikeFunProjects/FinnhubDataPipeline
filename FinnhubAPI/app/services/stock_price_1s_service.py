from pydantic import BaseModel
from utils.CassandraMapper import CassandraMapper
from database.cassandra_client import CassandraClient
from database.cassandra_config import get_cassandra_config
from database.models import StockPrice1s

class StockPrice1sService():
    def __init__(self, CustomModel: type[BaseModel]):
        self.cassandra_config = get_cassandra_config()
        self.cassandra_mapper = CassandraMapper(CustomModel)
        self.sync_stock_price_1s()
        self.data_filter_properties = {"extra_filters": {}}

    def sync_stock_price_1s(self):
        with CassandraClient(self.cassandra_config) as cassandra_client:
            cassandra_client.sync_table(StockPrice1s)

    def get_stock_price_1s(self, batch_size: int=100, symbol: str=None, reset_start_date: int=None) -> list[type[BaseModel]] | None:
        with CassandraClient(self.cassandra_config) as cassandra_client:
            try:
                if symbol:
                    self.data_filter_properties["extra_filters"]["symbol"] = symbol
                data = cassandra_client.get_all_items_by_partition_date(
                    batch_size=batch_size,
                    CustomModel=StockPrice1s,
                    set_start_date=reset_start_date,
                    data_filter_properties=self.data_filter_properties
                )
                if "data_filter_properties" in data:
                    self.data_filter_properties = data["data_filter_properties"]
                if not data or not data["records_list"]:
                    return None
                print(f"Size of records: {len(data["records_list"])}")
                return self.cassandra_mapper.to_pydantic_list(data["records_list"])
            except Exception as e:
                print(e)
