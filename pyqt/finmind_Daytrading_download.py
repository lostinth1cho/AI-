from FinMind.data import DataLoader
import pandas as pd
from datetime import datetime
from os import listdir
import requests
import time


def fm_download(stock_id, start_date_str, end_date_str):
    api = DataLoader()
    # api.login_by_token(api_token='token')
    # api.login(user_id='user_id',password='password')
    df = api.taiwan_stock_daily(
        stock_id=stock_id,
        start_date=start_date_str,
        end_date=end_date_str
    )
    rename_dict = {
        "Trading_Volume": "Volume",
        "open": "Open",
        "max": "High",
        "min": "Low",
        "close": "Close",
    }

    df = df.rename(columns=rename_dict)
    #df = df[df["Close"] > 0]
    return df


if __name__ == "__main__":
    symbol_id = 2330
    start_date = "2023-12-04"
    end_date = "2024-01-04"
    df = fm_download(symbol_id, start_date, end_date)
