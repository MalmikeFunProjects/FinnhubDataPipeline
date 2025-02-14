import os
import pandas as pd
from pathlib import Path

# Utility class that provides helper functions for working with data, files, and schema
class Utilities:
    """
    A utility class containing static methods for various common operations
    such as reading/writing data, handling schemas, and working with DataFrames.
    """

    @staticmethod
    def delivery_report(err, msg) -> None:
        """
        A callback function that logs the result of Kafka message delivery attempts.

        Parameters:
            err (KafkaError or None): Error object if the delivery failed, otherwise None.
            msg (Message): The Kafka message object containing the details of the sent message.

        Logs:
            Prints success or failure of the message delivery to the console.
        """
        if err:
            print(f"Delivery failed for record {msg.key()}: {err}")
            return
        print(f'Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    @staticmethod
    def rename_df_columns(df: pd.DataFrame, column_mapping: dict[str, str]) -> None:
        """
        Renames the columns of a pandas DataFrame based on the provided column mapping.

        Parameters:
            df (pd.DataFrame): The pandas DataFrame whose columns need to be renamed.
            column_mapping (dict): A dictionary mapping current column names to new column names.

        Modifies:
            The DataFrame in place by renaming the columns as per the provided mapping.
        """
        # Renaming columns based on the provided column mapping
        df.rename(columns=column_mapping, inplace=True)

    @staticmethod
    def from_df_to_csv(df: pd.DataFrame, file_path: str) -> None:
        """
        Writes the contents of a pandas DataFrame to a CSV file.

        Parameters:
            df (pd.DataFrame): The DataFrame to write to a CSV file.
            file_path (str): The file path where the CSV file will be saved.

        Logs:
            Prints errors if the directory does not exist, if there is a permission error,
            or if any other error occurs during the write operation.
        """
        try:
            file_path = Path(file_path)  # Ensure the file path is a Path object
            # Write DataFrame to CSV, with "N/A" for missing values
            df.to_csv(file_path, na_rep="N/A", index=False)
        except FileNotFoundError:
            print(f"Error: The directory {file_path} does not exist.")
        except PermissionError:
            print(f"Error: Permission denied when writing to {file_path}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def from_csv_to_df(file_path: str) -> pd.DataFrame:
        """
        Loads the contents of a CSV file into a pandas DataFrame.

        Parameters:
            file_path (str): The file path of the CSV file to load.

        Returns:
            pd.DataFrame: The DataFrame containing the data from the CSV file, or None if the file doesn't exist.

        Logs:
            Prints errors if the file does not exist, if there is a permission error,
            or if any other error occurs during the load operation.
        """
        try:
            file_path = Path(file_path)  # Ensure the file path is a Path object
            # Load the CSV file into a DataFrame if the file exists
            return pd.read_csv(file_path) if file_path.exists() else None
        except FileNotFoundError:
            print(f"Error: The directory {file_path} does not exist.")
        except PermissionError:
            print(f"Error: Permission denied when reading from {file_path}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def convert_nan_to_none(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts all NaN (Not a Number) values in a pandas DataFrame to None.

        Parameters:
            df (pd.DataFrame): The DataFrame where NaN values need to be replaced.

        Returns:
            pd.DataFrame: A new DataFrame with NaN values replaced by None.
        """
        # Replace NaN values with None
        return df.where(pd.notna(df), None)  # NaN values are replaced by None
