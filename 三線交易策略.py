import pandas as pd
import talib
from KPI import proc_KPI
from process_data import get_data, split_data

cash = 1e6

fee_rate = 0.001425
min_fee = 20
tax_rate = 0.003

def trade(data_df, cash):
    global record_df, hold_data
    
    #定義交易紀錄
    record_df = pd.DataFrame(columns = ["time", "price", "BS", "num"])
    
    #定義持有資訊
    hold_data = {
        "price": 0,
        "num": 0,
        "BS": ""
    }
    
    #最後一日平倉資訊
    last_date = data_df.iloc[-1]["日期"]
    last_trade_price = data_df.iloc[-1]["成交價格"]
    
    #走訪資料，進行回測
    for index, row in data_df.iterrows():
        #空手，建倉判斷
        if hold_data["BS"] == "":
            
            #買入條件
            Buy_condition = [
                row["MA_short"] > row["MA_medium"],
                row["MAmedium"] > row["MA_long"],
                row["成交量"] > (row["Volume_mean"] * 1.5)
            ]
            #賣出條件
            Sell_condition = [
                row["MA_short"] < row["MA_medium"],
                row["MA_medium"] < row["MA_long"],
                row["成交量"] > (row["Volume_mean"] * 1.5)
            ]
            
            if all(Buy_condition):
                trade_price = row["成交價格"]
                
                num, fee = get_num_fee_hold(cash, trade_price, "B")
                Recording(row["日期"], trade_price, "B", num)
                
                cash -= trade_price * num + fee
            elif all(Sell_condition):
                trade_price = row["成交價格"]
                num, fee = get_num_fee_hold(cash, trade_price, "S")
                
                Recording(row["日期"], trade_price, "S", num)
                
                tax = trade_price * num * tax_rate
                
                cash -= trade_price * num + fee + tax
        else:
            #做多平倉條件
            offset_Buy_condition = [
                row["MA_short"] < row["MA_medium"],
                hold_data["BS"] == "B"
            ]
            #做空平倉條件
            offset_Sell_condition = [
                row["MA_short"] > row["MA_medium"],
                hold_data["BS"] == "S"
            ]
            
            if all(offset_Buy_condition):
                num = hold_data["num"] #當前持有數量
                trade_price = row["成交價格"]#當前價格
                Recording(row["日期"], trade_price, "S", num)#紀錄平倉交易
                fee = fee_cal( trade_price, num)
                #證交稅
                tax = trade_price * num * tax_rate
                #平倉取得金額
                cash += trade_price * num - fee - tax
                #清空持有紀錄
                hold_data = {
                        "price" : 0,
                        "num" : 0,
                        "BS" : ""
                    }
            elif all(offset_Sell_condition):
                num = hold_data["num"]#當下持有數量
                hold_price = hold_data["price"]#建倉成交價
                trade_price = row["成交價格"]#當下價格
                Recording(row["日期"], trade_price, "B", num)
                #交易手續費
                fee = fee_cal(trade_price, num )
                #拿回保證金。賣出價金，剪除回補成本
                cash += hold_price * num + (hold_price - trade_price) * num - fee
                hold_data = {
                        "price": 0, 
                        "num": 0,
                        "BS": ""
                    }
    if hold_data["BS"] == "B":
        #若持有數量部位大於0，將做多平倉
        num = hold_data["num"]
        Recording(last_date, last_trade_price, "S", hold_data["num"])
        
        fee = fee_cal(last_trade_price, num)
        tax = last_trade_price * num * tax_rate
        
        cash += last_trade_price * hold_data["num"] - fee - tax
        
    elif hold_data["BS"] == "S":
        num = hold_data["num"]
        hold_price = hold_data["price"]
        Recording(last_date, last_trade_price, "B", num)
        fee = fee_cal( last_trade_price, num)
        
        cash += hold_price * num + (hold_price - last_trade_price) * num - fee
    return record_df
        
def get_num_fee_hold(cash, trade_price, BS):
    if BS == "B":
        num = cash // (trade_price * (1 + fee_rate))
    else:
        num = cash // (trade_price * (1 + fee_rate + tax_rate))
    hold_data["price"] = trade_price
    hold_data["num"] = num
    hold_data["BS"] = BS
    
    fee = fee_cal(trade_price, num)
    return num, fee

def fee_cal(trade_price, num):
    fee = trade_price * num * fee_rate
    
    return max(fee, min_fee)

def Recording(time, price, BS, num):
    
    if record_df.empty: #若當下的交易紀錄是空，索引值設為0
        index_count = 0
    else:               #若交易紀錄簿不是空，索引值為最大值+1
        index_count = record_df.index[-1] + 1
    
    record_df.at[index_count, "time"] = time
    record_df.at[index_count, "price"] = price
    record_df.at[index_count, "BS"] = BS
    record_df.at[index_count, "num"] = num

def get_tech(df):
    #以隔天開盤價當作成交價格
    df["成交價格"] = df["開盤價"].shift(-1)
    #最後一天以收盤價當作交易價格
    df["成交價格"].fillna(method = "ffill", inplace = True)
    #計算短期均線(5日均線)
    df["MA_short"] = talib.SMA(df["收盤價"], 5)
    #計算中期均線(20日)
    df["MA_medium"] = talib.SMA(df["收盤價"], 20)
    #計算長期均線(60日)
    df["MA_long"] = talib.SMA(df["收盤價"], 60)
    #平均交易量
    df["Volume_mean"] = talib.SMA(df["成交量"], 20)
    df = df.dropna()
    return df

df = get_data( stock_id = 2603)

df = get_tech(df)

train_data, test_data = split_data(data = df, train_part = 0.7)

train_record = trade(train_data, cash)
test_record = trade(test_data, cash)

train_KPI = proc_KPI(train_record, cash, fee_rate, tax_rate)
test_KPI = proc_KPI(test_record, cash, fee_rate, tax_rate)

print(train_KPI)
print(test_KPI)
