import pandas as pd
from .finnhub_sp500 import FinnhubSP500

class FinnhubGatherData:
  def __init__(self):
    self.finnhubSP500 = FinnhubSP500()
    self.sp500_key_name = self.finnhubSP500.key_name
    self.us_big_tech_str_list = self.finnhubSP500.us_big_tech_str_list

  def get_company_profiles(self) -> pd.DataFrame:
    return self.finnhubSP500.sp500_company_profiles()

  def get_us_big_tech_tickers(self, sp500_company_profiles: pd.DataFrame) -> pd.Series:
    us_big_tech_list = sp500_company_profiles[sp500_company_profiles["Name"].str.contains(self.us_big_tech_str_list, case=False, na=False)]
    return us_big_tech_list["Ticker"]
