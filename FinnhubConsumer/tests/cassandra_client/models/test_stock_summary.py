import pytest
import datetime
import time
import uuid
from unittest.mock import patch

from app.cassandra_client.models.StockSummary import StockSummary

# Freeze time for consistent testing of insertion_timestamp default
FROZEN_TIME_SECS = 1678886400  # Example: March 15, 2023 12:00:00 PM UTC
FROZEN_TIME_MS = int(FROZEN_TIME_SECS * 1000)

class TestStockSummary:
    """Test class for StockSummary model."""
    def test_class_attributes(self):
        """Tests if the class has the expected attributes."""
        assert hasattr(StockSummary, '__keyspace__')
        assert hasattr(StockSummary, '__table_name__')
        assert hasattr(StockSummary, 'partition_date')
        assert hasattr(StockSummary, 'event_timestamp')
        assert hasattr(StockSummary, 'insertion_timestamp')
        assert hasattr(StockSummary, 'processing_id')
        assert hasattr(StockSummary, 'total_price')
        assert hasattr(StockSummary, 'symbol_prices')
        assert hasattr(StockSummary, 'is_processed')

    @pytest.fixture
    def sample_data(self):
        """Provides basic data for creating a StockSummary instance."""
        return {
            "event_timestamp": 1678886400000,  # March 15, 2023 12:00:00 PM UTC in ms
            "total_price": 1500.75,
            "symbol_prices": {"AAPL": 150.75, "MSFT": 280.50},
        }

    @patch('time.time', return_value=FROZEN_TIME_SECS)
    def test_init_calculates_partition_date(self, mock_time, sample_data):
        """
        Tests if partition_date is correctly calculated from event_timestamp
        when partition_date is not provided.
        """
        instance = StockSummary(**sample_data)
        expected_date = datetime.date.fromtimestamp(sample_data["event_timestamp"] / 1000)
        assert instance.partition_date == expected_date
        # Also check that insertion_timestamp was set correctly in this case
        assert instance.insertion_timestamp == FROZEN_TIME_MS

    @patch('time.time', return_value=FROZEN_TIME_SECS)
    def test_init_sets_default_insertion_timestamp(self, mock_time, sample_data):
        """
        Tests if insertion_timestamp defaults to the current time (mocked)
        when not provided.
        """
        # Provide partition_date so insertion_timestamp logic is isolated
        sample_data["partition_date"] = datetime.date(2023, 3, 15)
        instance = StockSummary(**sample_data)
        assert instance.insertion_timestamp == FROZEN_TIME_MS

    def test_init_uses_provided_partition_date(self, sample_data):
        """
        Tests if a provided partition_date is used correctly.
        """
        provided_date = datetime.date(2023, 1, 1)
        sample_data["partition_date"] = provided_date
        instance = StockSummary(**sample_data)
        assert instance.partition_date == provided_date

    def test_init_uses_provided_insertion_timestamp(self, sample_data):
        """
        Tests if a provided insertion_timestamp is used correctly.
        """
        provided_timestamp = 1670000000000  # Some specific timestamp
        sample_data["insertion_timestamp"] = provided_timestamp
        instance = StockSummary(**sample_data)
        assert instance.insertion_timestamp == provided_timestamp

    def test_init_uses_provided_timestamps_and_date(self, sample_data):
        """
        Tests if provided partition_date and insertion_timestamp override defaults.
        """
        provided_date = datetime.date(2023, 1, 1)
        provided_ins_ts = 1670000000000
        sample_data["partition_date"] = provided_date
        sample_data["insertion_timestamp"] = provided_ins_ts

        # Mock time just to ensure it's not used
        with patch('time.time', return_value=FROZEN_TIME_SECS) as mock_time:
            instance = StockSummary(**sample_data)
            assert instance.partition_date == provided_date
            assert instance.insertion_timestamp == provided_ins_ts
            mock_time.assert_not_called() # Verify time.time() wasn't called

    def test_default_processing_id(self, sample_data):
        """Tests if processing_id gets a default UUID."""
        instance1 = StockSummary(**sample_data)
        instance2 = StockSummary(**sample_data)
        assert isinstance(instance1.processing_id, uuid.UUID)
        assert instance1.processing_id != instance2.processing_id # Should be unique

    def test_default_is_processed(self, sample_data):
        """Tests if is_processed defaults to False."""
        instance = StockSummary(**sample_data)
        assert instance.is_processed is False

    def test_instantiation_with_all_fields(self, sample_data):
        """Tests basic object creation with all required fields."""
        processing_id = uuid.uuid4()
        partition_date = datetime.date.fromtimestamp(sample_data["event_timestamp"] / 1000)
        insertion_timestamp = int(time.time() * 1000)

        instance = StockSummary(
            partition_date=partition_date,
            event_timestamp=sample_data["event_timestamp"],
            insertion_timestamp=insertion_timestamp,
            processing_id=processing_id,
            total_price=sample_data["total_price"],
            symbol_prices=sample_data["symbol_prices"],
            is_processed=True # Explicitly set to non-default
        )

        assert instance.partition_date == partition_date
        assert instance.event_timestamp == sample_data["event_timestamp"]
        assert instance.insertion_timestamp == insertion_timestamp
        assert instance.processing_id == processing_id
        assert instance.total_price == sample_data["total_price"]
        assert instance.symbol_prices == sample_data["symbol_prices"]
        assert instance.is_processed is True
