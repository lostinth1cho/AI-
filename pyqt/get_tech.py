import talib


def get_tech(df):
    # 以隔天開盤價當作成交價格
    df["成交價格"] = df["開盤價"].shift(-1)
    # 最後一天以收盤價當作交易價格
    df["成交價格"].ffill(inplace=True)
    # 計算短期均線(5日均線)
    df["MA_5"] = talib.SMA(df["收盤價"], 5)
    # 計算中期均線(10日)
    df["MA_10"] = talib.SMA(df["收盤價"], 10)
    # 計算長期均線(20日)
    df["MA_20"] = talib.SMA(df["收盤價"], 20)
    # 五天平均交易量
    df["Volume_5MA"] = talib.SMA(df["成交量"], 5)
    # 計算RSI(預設為14)
    df["RSI"] = talib.RSI(df["收盤價"], timeperiod=14)
    # 低檔RSI標準
    df["low_RSI"] = 20
    # 高檔RSI標準
    df["high_RSI"] = 80
    df = df.dropna()
    return df
