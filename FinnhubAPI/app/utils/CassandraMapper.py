from pydantic import BaseModel
from typing import Generic, List, TypeVar
from cassandra.cqlengine.models import Model

# Generic model mapper
T = TypeVar("T", bound= BaseModel)

class CassandraMapper(Generic[T]):
    """
    Utility class to map between Cassandra models and Pydantic models
    """
    def __init__(self, pydantic_model: type[T]):
        self.pydantic_model = pydantic_model

    def to_pydantic(self,cassandra_record: Model) -> T:
        """
        Convert a single Cassandra record to a Pydantic model

        Args:
            cassandra_record: The Cassandra model instance

        Returns:
            A Pydantic model instance with data from the Cassandra record
        """
        # Get the actual column names from the model class
        column_names = cassandra_record._columns.keys()
        # Create a dictionary with the actual values
        data = {key: getattr(cassandra_record, key) for key in column_names}
        # Create pydantic instance from dict
        return self.pydantic_model(**data)

    def to_pydantic_list(self, cassandra_records: List[Model]) -> List[T]:
        """
        Convert a list of Cassandra records to a list of Pydantic models

        Args:
            cassandra_records: List of Cassandra model instances

        Returns:
            List of Pydantic model instances
        """
        return [self.to_pydantic(record) for record in cassandra_records]

    def from_pydantic(self, pydantic_instance: T) -> Model:
        """
        Convert a Pydantic model instance to dict that can be used to create/ update a Cassandra model instance.
        """
        return pydantic_instance.model_dump()
