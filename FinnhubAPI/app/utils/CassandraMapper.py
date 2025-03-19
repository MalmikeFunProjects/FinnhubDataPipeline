from pydantic import BaseModel
from typing import Generic, TypeVar
from cassandra.cqlengine.models import Model


# Generic model mapper
T = TypeVar("T", bound= BaseModel)

class CassandraMapper(Generic[T]):
    def __init__(self, pydantic_model: type[T]):
        self.pydantic_model = pydantic_model

    def to_pydantic(self, cass_instance: Model) -> T:
        """
        Conver a Cassandra model instance to a Pydantic model instance.
        """
        # Get the actual column names from the model class
        column_names = cass_instance._columns.keys()
        # Create a dictionary with the actual values
        data = {key: getattr(cass_instance, key) for key in column_names}
        # Create pydantic instance from dict
        return self.pydantic_model(**data)

    def to_pydantic_list(self, cass_instances: list[Model]) -> list[T]:
        """
        Convert a list of Cassandra model instances to a list of Pydantic model instances.
        """
        return [self.to_pydantic(cass_instance) for cass_instance in cass_instances]

    def from_pydantic(self, pydantic_instance: T) -> Model:
        """
        Convert a Pydantic model instance to dict that can be used to create/ update a Cassandra model instance.
        """
        return pydantic_instance.model_dump()


