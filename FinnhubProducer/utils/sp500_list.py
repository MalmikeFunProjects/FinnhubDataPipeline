import pandas as pd

from utils.settings import SP500_COMPANIES_URL, US_BIG_TECH_URL

# Class for handling operations related to the S&P 500 list and US big tech companies
class SP500_list:

    @staticmethod
    def get_sp500_list() -> pd.DataFrame:
        """
        Fetches and returns the list of S&P 500 companies from the specified URL.

        The data is fetched as an HTML table and returned as a pandas DataFrame
        containing the symbols and company names.

        Returns:
            pd.DataFrame: DataFrame containing the "Symbol" and "Security" (company name) columns.
        """
        # Fetch the table of S&P 500 companies from the given URL
        tables = pd.read_html(SP500_COMPANIES_URL)
        sp500_table = tables[0]  # The first table contains the list of companies

        # Return the symbol and the company name as a DataFrame
        return sp500_table[["Symbol", "Security"]]

    @staticmethod
    def get_us_big_tech() -> str:
        """
        Fetches and returns the list of US-based big tech companies from the specified URL.

        This function retrieves the data, filters for US companies, and returns a
        pipe-separated list of big tech company names (replacing "Inc." suffix with "Inc").

        Returns:
            str: A pipe-separated string of US big tech companies.
        """
        # Fetch the table of big tech companies from the given URL
        tables = pd.read_html(US_BIG_TECH_URL)
        big_tech = tables[1]

        # Filter for companies based in the US
        us_big_tech = big_tech[big_tech["Country (origin)"] == "US"]

        # Return a pipe-separated string of company names (with "Inc." suffix formatted)
        return "|".join(us_big_tech["Company"]).replace("Inc.", "Inc")
