# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 13:53:15 2024

@author: a2089
"""

import pandas as pd
import talib

class trade_class:
    def __init__(self,data_df):
        self.data_df = data_df #傳入資料
        
        #不會因為交易參數改變而變動的變數
        #手續費 交易稅率 最低手續費
        self.fee_rate = 0.001425
        self.tax_rate = 0.003
        self.min_tax =20
        
    def get_num_fee_hold(self,cash,trade_price,BS):
        #整數除法,根據現有資金決定成交股數
        if BS =="B":
            num = cash //(trade_price*(1+self.fee_rate))
        else:
            num = cash // (trade_price*(1+self.fee_rate+self.tax_rate))

        #更動持有狀況,紀錄成交價格 交易數量 多空
        self.hold_data["price"] = trade_price
        self.hold_data["num"] = num
        self.hold_data["BS"] = BS
        
        #交易手續費
        fee = self.fee_cal(trade_price ,num)
        
        return num,fee
    
    def trade(self,para):
        #會因交易參數改變而變動的變數
        #定義交易紀錄
        self.record_df = pd.DataFrame(columns = ["time" ,"price" ,"BS" ,"num"])
        #定義持有資訊
        self.hold_data = {
            "price" :0, #進場價位
            "num" :0,   #數量
            "BS":""     #多空標記,空字串代表沒有部位
            }
    
        #將傳入參數字典各自指派給變數
        cash = para["cash"]
        Long_RSI = para["Long_RSI"]
        Short_RSI = para["short_RSI"]
        RSI_days = para["RSI_days"]
        L_loss_offset_rate = para["L_loss_offset_rate"]
        S_loss_offset_rate = para["S_loss_offset_rate"]
        L_profit_offset_rate = para["L_profit_offset_rate"]
        S_profit_offset_rate = para["L_profit_offset_rate"]
        
        #將物件屬性轉換成區域變數,以縮短程式撰寫長度
        data_df = self.data_df
        fee_rate = self.fee_rate
        tax_rate = self.tax_rate
        hold_data = self.hold_data
        record_df = self.record_df
        
        #計算RSI
        data_df["RSI"] = talib.RSI(data_df["收盤價"],RSI_days)
        #以上做資料處理
        #以下做逐交易日找買進或賣出,若找到舊紀錄當天的資訊
        for index,row in data_df.itterows():
            
            if cash <0:
                continue
            
            #沒有持有部位建倉判斷
            if hold_data["BS"] == "":
                #買入條件
                Buy_condition = [
                    row["RSI"] < Long_RSI,#若RSI<20,則做多
                    ]
                #賣出條件
                Sell_condition=[
                    row["RSI"] > Short_RSI, #若RSI>80 ,則做空
                    ]
                
                if all(Buy_condition):
                    trade_price = row["成交價格"] #取出當下的成交價格
                    
                    #已持有現金計算交易量 手續費 並更動持有資訊
                    num ,fee = self.get_num_fee_hold(cash , trade_price ,"B")
                    #紀錄做多交易
                    self.Recording(row["日期"],trade_price ,"B",num)
                    
                    #資金更動扣除買股票的資金
                    cash-= trade_price*num+fee
                elif all(Sell_condition):
                    trade_price = row["成交價格"] #取出當下的成交價格
                    
                    num, fee = self.get_num_fee_hold(cash, trade_price ,"S")
                    
                    self.Recording(row["日期"] ,trade_price,"S",num) #紀錄做空交易
                    
                    
                    #證交稅
                    tax = trade_price * num * tax_rate
                    
                    #資金更動 假設保證金率為1 且沒有融券手續費 利息
                    cash -= trade_price *num +fee +tax
                #持有部位 平倉判斷    
                else: 
                    #做多平倉條件
                    offset_Buy_condition = [
                        row['RSI'] > Short_RSI, #RSI大於80
                        
                        #做多停損停利
                        row['收盤價'] >(hold_data['price'] * (1 + L_profit_offset_rate)),
                        row['收盤價'] <(hold_data['price'] * (1 - L_loss_offset_rate))
                        ]
                    
                    #做空平倉條件
                    offset_Sell_condition =[
                        row['RSI'] < Long_RSI, #RSI小於20
                        
                        #做空停損停利
                        row['收盤價'] < (hold_data["price"] *(1-S_profit_offset_rate)),
                        row['收盤價'] > (hold_data["price"] *(1-S_loss_offset_rate))
                        ]
            else:
                #做多平倉條件
                if self.hold_data["BS"] == "B" and any(offset_Buy_condition):
                    num = self.hold_data['num'] #當下持有數量
                    
                    trade_price = row['成交價格'] #取出當下的成交價格
                    self.Recording(row["日期"] ,trade_price,"S",num) #紀錄平倉交易
                    #交易手續費
                    fee = self.fee_cal(trade_price ,num)
                    
                    #證交稅
                    tax = trade_price * num * tax_rate
                    
                    cash += trade_price*num -fee -tax #平倉取得金額
                    
                    #清空持有紀錄
                    self.hold_data = {
                        "price" : 0 ,#進場價位
                        "num" : 0 ,#數量
                        "BS" : ""  #多空標記,空字串代表沒有部位
                        }
                 #做空平倉條件   
                elif self.hold_data['BS'] == "S" and any(offset_Sell_condition):
                    num = self.hold_data['num'] #當下持有數量,將負數轉正
                    hold_price = self.hold_data["price"] #建倉成交價
                    trade_price = row["成交價格"] #取出當下的成交價格
                    self.Recording(row['日期'],trade_price,"B" ,num) #紀錄平倉交易
                    
                    #交易手續費
                    fee = self.fee_cal(trade_price ,num)
                    
                    #拿回保證金 賣出價金 減除回補成本
                    cash += hold_price *num + (hold_price - trade_price) *num -fee
                    
                    #清空持有紀錄
                    self.hold_data = {
                        "price" : 0, #進場價位
                        "num" : 0, #數量
                        "BS" :"" #多空標記,空字串代表沒有部位
                        }
         #最後一日平倉
        last_date = data_df.iloc[-1]['日期'] #最後一日日期
        last_trade_price = data_df.iloc[-1]['成交價格'] #最後一日成交價格
        
        if self.hold_data['BS'] == 'B':
            num = hold_data['num']
            self.Recording(last_date,last_trade_price,"S",hold_data["num"])
            #交易手續費
            fee = self.fee_cal(last_trade_price,num )
            #證交稅
            tax = last_trade_price * num *tax_rate
            
            cash+= last_trade_price*hold_data["num"] - fee -tax #平倉取得金額
            
        elif self.hold_data["BS"] == "S":
            num = hold_data['num']
            hold_price = hold_data["price"] #建倉成交價
            self.Recording(last_date ,last_trade_price ,"B" ,num)
            
            #交易手續費
            fee = self.fee_cal(last_trade_price,num)
            #拿回保證金賣出價金減除回補成本
            cash += hold_price *num +(hold_price - last_trade_price) *num -fee
        return record_df #回傳交易紀錄
    #計算手續費
    def fee_cal(self , trade_price,num):
        fee_rate = self.fee_rate
        min_fee = self.min_fee
        #交易手續費
        fee = trade_price *num *fee_rate
        
        #手續費不足20元則以20元計價
        if fee < min_fee:
            fee = min_fee
        return fee #回傳手續費
    def Recording(self,time,price,BS,num):
        record_df = self.record_df
        
        if record_df.empty: #若當下交易紀錄是空的則索引值設為0
            index_count = 0
        else: #若交易紀錄不是空的,則索引值設為最大值+1
            index_count = record_df.index[-1]+1
            
        #將交易資料寫入交易資料
        record_df.at[index_count,"time"] = time
        record_df.at[index_count,"price"] = price
        record_df.at[index_count,"BS"] = BS
        record_df.at[index_count,"num"] = num