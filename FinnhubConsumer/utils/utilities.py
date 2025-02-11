import os
import re

class Utilities:
  @staticmethod
  def load_schema(schema_path: str) -> str:
    path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{path}/{schema_path}") as file:
      schema_str = file.read()
    return schema_str

  @staticmethod
  def remove_no_printable_characters(input_str: str) -> str:
    return re.sub(r'[\x00-\x1F]', "", input_str)
