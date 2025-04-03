import pandas as pd
from .finnhub_sp500 import FinnhubSP500

class FinnhubGatherData:
    """
    A class to gather and process data from the Finnhub API, specifically focusing on S&P 500 companies and US Big Tech.

    Attributes:
        finnhubSP500: An instance of the FinnhubSP500 class, used to interact with the Finnhub API.
        sp500_key_name: The key name used to identify S&P 500 companies within the Finnhub data.  Inherited from `FinnhubSP500`.
        us_big_tech_str_list: A list of strings used to identify US Big Tech companies. Inherited from `FinnhubSP500`.
    """

    def __init__(self):
        """
        Initializes the FinnhubGatherData object.  Creates an instance of FinnhubSP500 and
        inherits relevant attributes.
        """
        self.finnhubSP500 = FinnhubSP500()
        self.sp500_key_name = self.finnhubSP500.key_name
        self.us_big_tech_str_list = self.finnhubSP500.us_big_tech_str_list

    def get_company_profiles(self) -> pd.DataFrame:
        """
        Retrieves company profiles for all S&P 500 companies.

        Returns:
            A pandas DataFrame containing company profile data.  The columns of the DataFrame
            will depend on the data returned by the Finnhub API.

        Raises:
            Potentially any exceptions raised by the underlying `FinnhubSP500.sp500_company_profiles()` call.
            It's good practice to handle these exceptions where this method is called.
        """
        return self.finnhubSP500.sp500_company_profiles()

    def get_us_big_tech_tickers(self, sp500_company_profiles: pd.DataFrame) -> pd.Series:
        """
        Extracts the tickers of US Big Tech companies from a DataFrame of S&P 500 company profiles.

        Parameters:
            sp500_company_profiles: A pandas DataFrame containing company profile data, typically
                                    obtained from the `get_company_profiles()` method.  This DataFrame
                                    *must* contain a "Name" column.

        Returns:
            A pandas Series containing the tickers of the identified US Big Tech companies.

        Raises:
            TypeError: if `sp500_company_profiles` is not a Pandas DataFrame.
            KeyError: if the input DataFrame does not contain a "Name" column.

        """

        if not isinstance(sp500_company_profiles, pd.DataFrame):
            raise TypeError("sp500_company_profiles must be a pandas DataFrame")

        if "Name" not in sp500_company_profiles.columns:
            raise KeyError("sp500_company_profiles must contain a 'Name' column")


        us_big_tech_list = sp500_company_profiles[
            sp500_company_profiles["Name"].str.contains(self.us_big_tech_str_list, case=False, na=False)
        ]
        return us_big_tech_list["Ticker"]
