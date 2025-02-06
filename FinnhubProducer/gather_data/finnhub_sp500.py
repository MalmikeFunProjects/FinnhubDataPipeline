import finnhub
import pandas as pd
import time
import finnhub
import asyncio
from utils.settings import FINNHUB_API_KEY, SP500_COMPANY_PROFILES_FILE_PATH
from utils.sp500_list import SP500_list
from utils.utilities import Utilities

class FinnhubSP500:
  def __init__(self):
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
    if(self.sp500_company_profiles_csv is not None):
      company_symbols = self.sp500_company_profiles_csv["Symbol"]
      new_sp500_list = self.sp500_list[~self.sp500_list["Symbol"].isin(company_symbols)]
      existing_sp500_company_profile = self.sp500_company_profiles_csv[company_symbols.isin(self.sp500_list["Symbol"])]
      return {'sp500_list': new_sp500_list, 'sp500_company_profile': existing_sp500_company_profile}
    return {'sp500_list': self.sp500_list, 'sp500_company_profile': None}

  def __process_sp500_row(self, row: pd.Series, trail: int=0):
    try:
      company_profile_json = self.finnhub_client.company_profile2(symbol=row["Symbol"])
      company_profile_json["Symbol"] = row["Symbol"]
      print(f"{row["Security"]}: success")

    except finnhub.FinnhubAPIException as e:
      if e.status_code == 429 and trail <= 4:
        #Wait for the specified duration before retrying
        retry_after = 30+(trail*5)
        print(f"Rate limit exceeded. Retry after {retry_after} seconds")
        time.sleep(retry_after)
        company_profile_json = self.process_sp500_row(row, trail+1)
        print(f"{row['Security']}: {trail}")
      else:
        print(f"Could not retrieve the company profile for {row["Security"]} in {trail} trails")
        company_profile_json = None
    return company_profile_json

  async def __async_process_sp500_row(
    self,
    row: pd.Series,
    semaphore: asyncio.Semaphore):
    async with semaphore:
      return self.__process_sp500_row(row)

  async def __async_process_sp500_company_profiles(self, sp500_list: pd.DataFrame, concurrency_limit: int = 3):
    semaphore = asyncio.Semaphore(concurrency_limit)
    tasks = [self.__async_process_sp500_row(row, semaphore) for _, row in sp500_list.iterrows()]
    sp500_company_profiles = await asyncio.gather(*tasks)
    return sp500_company_profiles

  def sp500_company_profiles(self) -> pd.DataFrame:
    sp500_list, sp500_company_profiles = self.dist_sp500_list.values()
    sp500_company_profiles_json = asyncio.run(self.__async_process_sp500_company_profiles(sp500_list))
    fetched_sp500_company_profiles = pd.DataFrame(sp500_company_profiles_json)
    sp500_company_profiles = pd.concat([sp500_company_profiles, fetched_sp500_company_profiles], ignore_index=True)
    Utilities.from_df_to_csv(sp500_company_profiles, SP500_COMPANY_PROFILES_FILE_PATH)
    Utilities.rename_df_columns(sp500_company_profiles, column_mapping=self.column_map)
    return Utilities.convert_nan_to_none(sp500_company_profiles)

