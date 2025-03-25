from typing import Any, Dict, Optional
from pydantic import BaseModel
from database.cassandra_client import CassandraClient
from database.cassandra_config import get_cassandra_config
from database.models import LatestPrice as LatestPriceModel
from utils.CassandraMapper import CassandraMapper
from utils.utilities import Utilities, TimeReturnType
from utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("latest_price_service", log_to_console=True)


class LatestPriceService():
    def __init__(self, pydantic_model: type[BaseModel]):
        self.cassandra_config = get_cassandra_config()
        self.cassandra_mapper = CassandraMapper(pydantic_model)
        self._sync_latest_price_table()

    def _sync_latest_price_table(self):
        """Ensure the latest_price table is synced with Cassandra"""
        try:
            with CassandraClient(self.cassandra_config) as cassandra_client:
                cassandra_client.sync_table(LatestPriceModel)
                logger.info("Latest price table synced successfully")
        except Exception as e:
            logger.error(f"Failed to sync latest price table: {str(e)}")
            raise

    def get_latest_prices(
        self,
        symbol: Optional[str]=None,
        start_days_ago: Optional[int]=None,
        since_timestamp: Optional[int] = None,
        end_days_ago: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        batch_size: int=100
    ) -> list[type[BaseModel]] | None:
        """
        Get latest price data with various filtering options

        Args:
            symbol: Optional stock symbol to filter by
            start_days_ago: Days to look back from today (mutually exclusive with since_timestamp)
            since_timestamp: Only get prices after this timestamp (mutually exclusive with start_days_ago)
            batch_size: Maximum number of records to return

        Returns:
            List of latest price records as Pydantic models
        """
        try:
            with CassandraClient(self.cassandra_config) as cassandra_client:
                # Build query parameters
                filter_params = self._build_query_filters(
                    symbol=symbol,
                    start_days_ago=start_days_ago,
                    since_timestamp=since_timestamp,
                    end_days_ago=end_days_ago,
                    end_timestamp=end_timestamp
                )
                # Get data from Cassandra
                result = self._execute_price_query(
                    client=cassandra_client,
                    filter_params=filter_params,
                    batch_size=batch_size
                )

                if not result or not result.get("records"):
                    logger.info(f"No latest price data found for params: {filter_params}")
                    return []

                # Convert to Pydantic models
                return self.cassandra_mapper.to_pydantic_list(result["records"])

        except Exception as e:
            logger.exception(f"Error getting latest prices: {str(e)}")
            raise

    def _execute_price_query(
        self,
        client: CassandraClient,
        filter_params: Dict[str, Any],
        batch_size: int
    ) -> Dict[str, Any]:
        """
        Execute the actual database query based on filter parameters

        This method handles the different query strategies based on the filters
        """
        # Extract basic filters
        start_time_filter = filter_params.pop("start_timestamp_filter", None)
        end_time_filter = filter_params.pop("end_timestamp_filter", None)

        return client.query_time_partitioned_data(
            model_class=LatestPriceModel,
            partition_field="partition_date",
            timestamp_field="event_timestamp",
            start_date_time=start_time_filter,
            end_date_time=end_time_filter,
            page_size=batch_size,
            filters=filter_params,
            allow_filtering=True
        )

    def _build_query_filters(
        self,
        symbol: Optional[str] = None,
        start_days_ago: Optional[int] = None,
        end_days_ago: Optional[int] = None,
        since_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build filter parameters for database queries.

        Args:
            symbol (Optional[str]): The trading symbol to filter by.
            start_days_ago (Optional[int]): Number of days ago to start the query from.
            end_days_ago (Optional[int]): Number of days ago to end the query.
            since_timestamp (Optional[int]): Specific start timestamp for the query.
            end_timestamp (Optional[int]): Specific end timestamp for the query.

        Returns:
            Dict[str, Any]: A dictionary containing query filter parameters.
        """
        filters: Dict[str, Any] = {}

        # Symbol filter
        if symbol:
            filters["symbol"] = symbol

        # Start timestamp filter
        filters["start_timestamp_filter"] = (
            since_timestamp
            if since_timestamp is not None
            else Utilities.adjust_datetime(
                duration={"days": start_days_ago} if start_days_ago is not None else None,
                return_type=TimeReturnType.DATE
            )
        )
        # End timestamp filter
        filters["end_timestamp_filter"] = (
            end_timestamp
            if end_timestamp is not None
            else (
                Utilities.adjust_datetime(
                    duration={"days": end_days_ago},
                    return_type=TimeReturnType.DATE
                ) if end_days_ago is not None else None
            )
        )

        return filters
