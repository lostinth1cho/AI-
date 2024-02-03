'''
Date: 2024-01-30 11:49:53
LastEditors: lostinth1cho b07902128@ntu.edu.tw
LastEditTime: 2024-02-02 14:15:33
FilePath: \NSGA選股_20240128\process_data.py
'''
import pandas as pd 

def get_data(**para):
    path = "FINMIND資料/"
    stock_id = para["stock_id"]
    df = pd.read_excel(f"{path}{stock_id}.xlsx")
    
    rename_dict = {
        "date": "日期",
        "Volume": "成交量",
        "Open": "開盤價",
        "High": "最高價",
        "Low": "最低價",
        "Close":"收盤價",
    }
    df = df.rename(columns = rename_dict)
    df = df[df["收盤價"] > 0]
    return df

def split_data(**para):
    df = para["data"]
    training_part = para["training_part"]
    df = df.sort_values(by=["日期"])
    training_split = int(df.shape[0] * training_part)
    
    train_data = df.iloc[:training_split]
    test_data = df.iloc[training_split:]
    
    return train_data, test_data

if __name__ == "__main__":
    df = get_data(stock_id = 2330)
    print(df)
    print(split_data(data = df, training_part=0.7))