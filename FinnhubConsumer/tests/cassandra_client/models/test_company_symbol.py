import pytest
from cassandra.cqlengine.models import Model

from app.cassandra_client.models.CompanySymbol import CompanySymbol

class TestCompanySymbol:
    def test_company_symbol_instantiation(self):
        """Tests creating an instance of CompanySymbol with a symbol."""
        symbol_value = "AAPL"
        instance = CompanySymbol(symbol=symbol_value)
        assert instance.symbol == symbol_value

    def test_company_symbol_instantiation_no_symbol(self):
        """Tests creating an instance without providing a symbol (should be allowed by cqlengine)."""
        # cqlengine models allow instantiation without required fields initially
        instance = CompanySymbol()
        assert instance.symbol is None

    def test_company_symbol_set_symbol_after_init(self):
        """Tests setting the symbol attribute after instantiation."""
        instance = CompanySymbol()
        symbol_value = "GOOGL"
        instance.symbol = symbol_value
        assert instance.symbol == symbol_value

    def test_company_symbol_keyspace_attribute(self):
        """Tests if the __keyspace__ attribute is set correctly."""
        assert CompanySymbol.__keyspace__ == "market"

    def test_company_symbol_table_name_attribute(self):
        """Tests if the __table_name__ attribute is set correctly."""
        assert CompanySymbol.__table_name__ == "company_symbol"

    def test_company_symbol_is_model_subclass(self):
        """Tests if CompanySymbol is a subclass of the cqlengine Model."""
        assert issubclass(CompanySymbol, Model)
