import os
import re

class Utilities:
    """
    A utility class providing methods for cleaning strings by removing
    non-printable characters.
    """

    @staticmethod
    def remove_no_printable_characters(input_str: str) -> str:
        """
        Removes non-printable ASCII characters (control characters) from a string.

        Parameters:
            input_str (str): The input string to clean.

        Returns:
            str: The cleaned string with non-printable characters removed.
        """
        return re.sub(r'[\x00-\x1F]', "", input_str)
