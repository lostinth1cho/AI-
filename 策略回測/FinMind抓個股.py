# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 13:14:38 2024

@author: a2089
"""

#抓全部上市上櫃資料
#抓完資料按照我們的選股邏輯
#<三大法人連續買超 小於100天&ETF刪掉>
#抓出個股明細>> 匯出成excel檔
from FinMind.data import DataLoader
import pandas as pd
from datetime import datetime
from os import listdir
import requests, time
#另一個list為抓出來的資料
catched_stock_list = listdir("FINMIND資料/")


#Finmind資料抓取
api = DataLoader()
# api.login_by_token(api_token='token')
api.login(user_id='nkust_finmind5@gmail.com',
          password='nkust_finmind5@gmail.com')

#TaiwanStockInfo為台股總覽
#取得指定時間的所有股票代號
stock_info = api.taiwan_stock_info()

stock_info = stock_info[(stock_info["date"] == "2024-02-05") & #
                        (stock_info["type"] == "twse") &
                        (stock_info["industry_category"] != "ETF")&
                        (stock_info["industry_category"] != "ETN")]
stock_list = pd.unique(stock_info["stock_id"])#unique撈取條件下的股票,且不讓股票代號重複
rename_dict = {
    "Trading_Volume" : "Volume",
    "open" : "Open",
    "max" : "High",
    "min" : "Low",
    "close" : "Close",
    }
for s_id in stock_list:
    if (s_id+".xlsx") in catched_stock_list:#限制只取沒有下載過的股票代號,防止重複抓取
    
        continue
    
    #下載台股資料
    stock_data = api.taiwan_stock_daily(
        stock_id = s_id,
        start_date = '2019-01-01',
        end_date = '2024-01-29'
    )
    if stock_data.shape[0] < 100: #資料筆數小於100筆的
        continue
    if len(s_id) != 4 :
        continue
    print(s_id,datetime.now(),stock_data.shape) 

    stock_data = stock_data.drop(["stock_id"],axis = 1)#不重複下載股票
    stock_data = stock_data.rename(columns = rename_dict)
    
    stock_data.to_excel(f"FINMIND資料/{s_id}.xlsx",index = False)
    time.sleep(6)