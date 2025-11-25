import pytest
from unittest.mock import Mock, MagicMock, patch
from pydantic import BaseModel
from typing import List, Optional
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

from app.utils.CassandraMapper import CassandraMapper  # Replace with your actual module import

# Define test models

class TestPydanticModel(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    tags: List[str] = []

# Mock Cassandra model for testing
class MockCassandraModel(Model):
    id = columns.Integer(primary_key=True)
    name = columns.Text()
    description = columns.Text()
    tags = columns.List(columns.Text)

    # Mock the _columns attribute that would normally be provided by the Model class
    _columns = {
        'id': Mock(),
        'name': Mock(),
        'description': Mock(),
        'tags': Mock()
    }

class TestCassandraMapper:

    def setup_method(self):
        self.mapper = CassandraMapper(TestPydanticModel)

    def test_init(self):
        """Test the initialization of the mapper"""
        assert self.mapper.pydantic_model == TestPydanticModel

    def test_to_pydantic_with_complete_data(self):
        """Test conversion from Cassandra model to Pydantic model with all fields"""
        # Create a mock Cassandra record
        cassandra_record = Mock(spec=MockCassandraModel)
        cassandra_record._columns = MockCassandraModel._columns
        cassandra_record.id = 1
        cassandra_record.name = "Test Name"
        cassandra_record.description = "Test Description"
        cassandra_record.tags = ["tag1", "tag2"]

        # Convert to Pydantic model
        pydantic_model = self.mapper.to_pydantic(cassandra_record)

        # Verify the conversion
        assert isinstance(pydantic_model, TestPydanticModel)
        assert pydantic_model.id == 1
        assert pydantic_model.name == "Test Name"
        assert pydantic_model.description == "Test Description"
        assert pydantic_model.tags == ["tag1", "tag2"]

    def test_to_pydantic_with_minimal_data(self):
        """Test conversion from Cassandra model to Pydantic model with minimal fields"""
        # Create a mock Cassandra record with just required fields
        cassandra_record = Mock(spec=MockCassandraModel)
        cassandra_record._columns = {'id': Mock(), 'name': Mock()}
        cassandra_record.id = 1
        cassandra_record.name = "Test Name"

        # Convert to Pydantic model
        pydantic_model = self.mapper.to_pydantic(cassandra_record)

        # Verify the conversion
        assert isinstance(pydantic_model, TestPydanticModel)
        assert pydantic_model.id == 1
        assert pydantic_model.name == "Test Name"
        assert pydantic_model.description is None
        assert pydantic_model.tags == []

    def test_to_pydantic_list(self):
        """Test conversion from a list of Cassandra models to a list of Pydantic models"""
        # Create mock Cassandra records
        cassandra_record1 = Mock(spec=MockCassandraModel)
        cassandra_record1._columns = MockCassandraModel._columns
        cassandra_record1.id = 1
        cassandra_record1.name = "Test Name 1"
        cassandra_record1.description = "Test Description 1"
        cassandra_record1.tags = ["tag1", "tag2"]

        cassandra_record2 = Mock(spec=MockCassandraModel)
        cassandra_record2._columns = MockCassandraModel._columns
        cassandra_record2.id = 2
        cassandra_record2.name = "Test Name 2"
        cassandra_record2.description = "Test Description 2"
        cassandra_record2.tags = ["tag3", "tag4"]

        cassandra_records = [cassandra_record1, cassandra_record2]

        # Convert to list of Pydantic models
        pydantic_models = self.mapper.to_pydantic_list(cassandra_records)

        # Verify the conversion
        assert len(pydantic_models) == 2
        assert all(isinstance(model, TestPydanticModel) for model in pydantic_models)

        assert pydantic_models[0].id == 1
        assert pydantic_models[0].name == "Test Name 1"
        assert pydantic_models[0].description == "Test Description 1"
        assert pydantic_models[0].tags == ["tag1", "tag2"]

        assert pydantic_models[1].id == 2
        assert pydantic_models[1].name == "Test Name 2"
        assert pydantic_models[1].description == "Test Description 2"
        assert pydantic_models[1].tags == ["tag3", "tag4"]

    def test_from_pydantic(self):
        """Test conversion from a Pydantic model to a dictionary for Cassandra model creation"""
        # Create a Pydantic model instance
        pydantic_instance = TestPydanticModel(
            id=1,
            name="Test Name",
            description="Test Description",
            tags=["tag1", "tag2"]
        )

        # Convert to dict for Cassandra
        result = self.mapper.from_pydantic(pydantic_instance)

        # Verify the conversion
        assert isinstance(result, dict)
        assert result == {
            'id': 1,
            'name': "Test Name",
            'description': "Test Description",
            'tags': ["tag1", "tag2"]
        }

    def test_to_pydantic_with_empty_list(self):
        """Test conversion from an empty list of Cassandra records"""
        result = self.mapper.to_pydantic_list([])
        assert result == []

    def test_to_pydantic_with_none_values(self):
        """Test conversion from Cassandra model with None values"""
        cassandra_record = Mock(spec=MockCassandraModel)
        cassandra_record._columns = MockCassandraModel._columns
        cassandra_record.id = 1
        cassandra_record.name = "Test Name"
        cassandra_record.description = None
        cassandra_record.tags = []

        pydantic_model = self.mapper.to_pydantic(cassandra_record)

        assert pydantic_model.id == 1
        assert pydantic_model.name == "Test Name"
        assert pydantic_model.description is None
        assert pydantic_model.tags == []

    @patch('app.utils.CassandraMapper.BaseModel.model_dump')
    def test_from_pydantic_calls_model_dump(self, mock_model_dump):
        """Test that from_pydantic correctly calls model_dump on the pydantic instance"""
        # Set up the mock to return a specific value
        mock_model_dump.return_value = {'id': 1, 'name': 'Test'}

        # Create a Pydantic model instance
        pydantic_instance = TestPydanticModel(id=1, name="Test")

        # Call the method
        result = self.mapper.from_pydantic(pydantic_instance)

        # Verify the model_dump method was called
        mock_model_dump.assert_called_once()
        assert result == {'id': 1, 'name': 'Test'}
