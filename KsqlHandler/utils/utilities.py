import os

class Utilities:
  @staticmethod
  def load_schema(schema_path:str) -> str:
    path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{path}/{schema_path}") as file:
      schema_str = file.read()
    return schema_str
