import finnhub
import pandas as pd
import time
import asyncio
from utils.settings import FINNHUB_API_KEY, SP500_COMPANY_PROFILES_FILE_PATH
from utils.sp500_list import SP500_list
from utils.utilities import Utilities

class FinnhubSP500:
    """
    A class to retrieve and manage S&P 500 company profiles using the Finnhub API.

    Attributes:
        finnhub_client: An instance of the Finnhub client.
        sp500_list: A DataFrame containing the list of S&P 500 companies.
        us_big_tech_str_list: A list of strings used to identify US Big Tech companies.
        sp500_company_profiles_csv: A DataFrame containing previously fetched company profiles (if available).
        dist_sp500_list: A dictionary containing new and existing S&P 500 company lists.
        key_name: The name of the key column (usually "Ticker").
        column_map: A dictionary mapping Finnhub API column names to desired names.
    """

    def __init__(self):
        """
        Initializes the FinnhubSP500 object.
        """
        self.finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
        self.sp500_list = SP500_list.get_sp500_list()
        self.us_big_tech_str_list = SP500_list.get_us_big_tech()
        self.sp500_company_profiles_csv = Utilities.from_csv_to_df(SP500_COMPANY_PROFILES_FILE_PATH)
        self.dist_sp500_list = self.__update_sp500_list()
        self.key_name = "Ticker"
        self.column_map = {
            "country": "Country",
            "currency": "Currency",
            "estimateCurrency": "EstimateCurrency",
            "exchange": "Exchange",
            "finnhubIndustry": "FinnhubIndustry",
            "ipo": "IPO",
            "logo": "Logo",
            "marketCapitalization": "MarketCapitalization",
            "name": "Name",
            "phone": "Phone",
            "shareOutstanding": "ShareOutstanding",
            "ticker": "Ticker",
            "weburl": "Weburl",
            "Symbol": "Symbol"
        }

    def __update_sp500_list(self) -> dict[str, pd.DataFrame]:
        """
        Updates the S&P 500 list, separating new companies from those with existing profiles.

        Returns:
            A dictionary containing two DataFrames: 'sp500_list' (new companies) and
            'sp500_company_profile' (existing profiles).
        """
        if self.sp500_company_profiles_csv is not None:
            company_symbols = self.sp500_company_profiles_csv["Symbol"]
            new_sp500_list = self.sp500_list[~self.sp500_list["Symbol"].isin(company_symbols)]
            existing_sp500_company_profile = self.sp500_company_profiles_csv[company_symbols.isin(self.sp500_list["Symbol"])]
            return {'sp500_list': new_sp500_list, 'sp500_company_profile': existing_sp500_company_profile}
        return {'sp500_list': self.sp500_list, 'sp500_company_profile': None}

    def __process_sp500_row(self, row: pd.Series, trail: int = 0):
        """
        Retrieves the company profile for a single S&P 500 company. Handles rate limiting and retries.

        Parameters:
            row: A pandas Series representing a single row from the S&P 500 list.
            trail: The number of retries already attempted.

        Returns:
            A dictionary containing the company profile data, or None if retrieval fails after retries.
        """
        try:
            company_profile_json = self.finnhub_client.company_profile2(symbol=row["Symbol"])
            company_profile_json["Symbol"] = row["Symbol"]
            print(f"{row['Security']}: success")

        except finnhub.FinnhubAPIException as e:
            if e.status_code == 429 and trail <= 4:  # Rate limit exceeded
                retry_after = 30 + (trail * 5)
                print(f"Rate limit exceeded. Retry after {retry_after} seconds")
                time.sleep(retry_after)
                company_profile_json = self.__process_sp500_row(row, trail + 1)  # Retry
                print(f"{row['Security']}: {trail}")
            else:
                print(f"Could not retrieve the company profile for {row['Security']} in {trail} trails")
                company_profile_json = None
        return company_profile_json

    async def __async_process_sp500_row(self, row: pd.Series, semaphore: asyncio.Semaphore):
        """
        Asynchronously processes a single S&P 500 company row.

        Parameters:
            row: Pandas Series containing company details.
            semaphore: Asyncio Semaphore to manage concurrent API requests.

        Returns:
            Dictionary containing company profile data.
        """
        async with semaphore:
            return self.__process_sp500_row(row)

    async def __async_process_sp500_company_profiles(self, sp500_list: pd.DataFrame, concurrency_limit: int = 3):
        """
        Asynchronously retrieves company profiles for a list of S&P 500 companies.

        Parameters:
            sp500_list: A DataFrame containing the list of S&P 500 companies.
            concurrency_limit: The maximum number of concurrent API calls.

        Returns:
            A list of dictionaries, where each dictionary contains the company profile data.
        """
        semaphore = asyncio.Semaphore(concurrency_limit)
        tasks = [self.__async_process_sp500_row(row, semaphore) for _, row in sp500_list.iterrows()]
        sp500_company_profiles = await asyncio.gather(*tasks)
        return sp500_company_profiles

    def sp500_company_profiles(self) -> pd.DataFrame:
        """
        Retrieves and saves S&P 500 company profiles, combining existing and newly fetched data.

        Returns:
            A pandas DataFrame containing all S&P 500 company profiles.
        """
        sp500_list, sp500_company_profiles = self.dist_sp500_list.values()
        sp500_company_profiles_json = asyncio.run(self.__async_process_sp500_company_profiles(sp500_list))
        fetched_sp500_company_profiles = pd.DataFrame(sp500_company_profiles_json)
        sp500_company_profiles = pd.concat([sp500_company_profiles, fetched_sp500_company_profiles], ignore_index=True)
        Utilities.from_df_to_csv(sp500_company_profiles, SP500_COMPANY_PROFILES_FILE_PATH)
        Utilities.rename_df_columns(sp500_company_profiles, column_mapping=self.column_map)
        return Utilities.convert_nan_to_none(sp500_company_profiles)
