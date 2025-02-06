from pathlib import Path
import pandas as pd

from settings import SP500_COMPANIES_URL, SP500_COMPANY_PROFILES_FILE_PATH, US_BIG_TECH_URL
sp500_company_profiles_file_path="resources/sp500_company_profiles.csv"

class SP500_list:
  @staticmethod
  def get_sp500_list() -> pd.DataFrame:
    # Fetch the table of S&P 500 companies
    tables = pd.read_html(SP500_COMPANIES_URL)
    sp500_table = tables[0]  # The first table contains the list of companies
    # Return the symbol and the comany name
    return sp500_table[["Symbol", "Security"]]

  @staticmethod
  def get_us_big_tech() -> str:
    tables = pd.read_html(US_BIG_TECH_URL)
    big_tech = tables[1]
    us_big_tech = big_tech[big_tech["Country (origin)"] == "US"]
    return "|".join(us_big_tech["Company"]).replace("Inc.", "Inc")


