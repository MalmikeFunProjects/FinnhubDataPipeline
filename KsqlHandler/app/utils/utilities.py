import os

class Utilities:
    """
    A utility class containing static methods for various common operations.
    """

    @staticmethod
    def load_schema(schema_path: str) -> str:
        """
        Loads an Avro schema from a specified file path.

        This method reads the contents of the Avro schema file located at the specified path,
        and returns it as a string. The schema file should be located relative to the current
        script's directory.

        Parameters:
            schema_path (str): The relative file path to the Avro schema.

        Returns:
            str: The content of the Avro schema file as a string.

        Raises:
            FileNotFoundError: If the schema file cannot be found at the specified path.
            IOError: If there is an error reading the schema file.
        """
        # Get the real path to the current script directory
        path = os.path.realpath(os.path.dirname(__file__))

        # Open and read the schema file
        with open(f"{path}/{schema_path}") as file:
            schema_str = file.read()

        # Return the content of the schema file as a string
        return schema_str
