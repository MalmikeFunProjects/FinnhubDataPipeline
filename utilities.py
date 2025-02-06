import os
import pandas as pd
from pathlib import Path

class Utilities:
  @staticmethod
  def load_schema(schema_path:str) -> str:
    path = os.path.realpath(os.path.dirname(__file__))
    with open(f"{path}/{schema_path}") as file:
      schema_str = file.read()
    return schema_str

  @staticmethod
  def delivery_report(err, msg) -> None:
    if err:
        print(f"Delivery failed for record {msg.key()}: {err}")
        return
    print(f'Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

  @staticmethod
  def rename_df_columns(df: pd.DataFrame, column_mapping: dict[str, str]) -> None:
    df.rename(columns=column_mapping, inplace=True)

  @staticmethod
  def from_df_to_csv(df: pd.DataFrame, file_path: str) -> None:
    try:
      file_path = Path(file_path)
      df.to_csv(file_path, na_rep="N/A", index=False)
    except FileNotFoundError:
      print(f"Error: The directory {file_path} does not exist.")
    except PermissionError:
      print(f"Error: Permission denied when writing to {file_path}.")
    except Exception as e:
      print(f"An error occurred: {e}")

  @staticmethod
  def from_csv_to_df(file_path: str) -> pd.DataFrame:
    try:
      file_path = Path(file_path)
      return pd.read_csv(file_path) if file_path.exists() else None
    except FileNotFoundError:
      print(f"Error: The directory {file_path} does not exist.")
    except PermissionError:
      print(f"Error: Permission denied when writing to {file_path}.")
    except Exception as e:
      print(f"An error occurred: {e}")

  @staticmethod
  def convert_nan_to_none(df: pd.DataFrame) -> pd.DataFrame:
    return df.where(pd.notna(df), None)



