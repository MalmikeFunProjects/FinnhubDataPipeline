from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class CompanySymbol(Model):
    __keyspace__ = "market"
    __table_name__ = "company_symbol"
    symbol = columns.Text(primary_key=True)
