import pandas as pd
import talib


class trade_class:
    def __init__(self, data_df):
        self.data_df = data_df  # 傳入的資料
        # 不會因為交易參數而改變的變數
        # 手續費(買賣都要) 交易稅率(賣出才繳) 最低手續費
        self.fee_rate = 0.001425
        self.tax_rate = 0.003
        self.min_fee = 20

    # BS代表買(B)賣(S),cash代表現金,trade_price代表交易價格
    def get_num_fee_hold(self, cash, trade_price, BS):
        # 整數除法,根據現有資金決定成交股數
        if BS == "B":
            num = cash // (trade_price * (1 + self.fee_rate))
        else:
            num = cash // (trade_price * (1 + self.fee_rate + self.tax_rate))
        # 更動持有狀況，紀錄成交價格、交易數量、多空
        self.hold_data["price"] = trade_price
        self.hold_data["num"] = num
        self.hold_data["BS"] = BS
        # 交易手續費
        fee = self.fee_cal(trade_price, num)

        return num, fee

    def trade(self, para):
        # 會因交易參數改變而變動的參數
        # 建立一個DF放交易紀錄
        self.record_df = pd.DataFrame(columns=["time", "price", "BS", "num"])

        # 定義持有資訊
        self.hold_data = {
            "price": 0,  # 進場價格
            "num": 0,  # 數量
            "BS": ""  # 多空標記 空字串代表沒有部位
        }

        # 將傳入參數字典各自指派給變數
        cash = para["cash"]
        RSI_days = para["RSI_days"]
        Low_RSI = para["Low_RSI"]
        High_RSI = para["High_RSI"]
        # 將物件轉成區域變數以縮短程式撰寫長度
        data_df = self.data_df
        fee_rate = self.fee_rate
        tax_rate = self.tax_rate
        record_df = self.record_df
        # 計算技術指標
        data_df["RSI"] = talib.RSI(data_df["收盤價"], RSI_days)
        # 計算短期均線(5日均線)
        data_df["MA_5"] = talib.SMA(data_df["收盤價"], 5)
        # 計算中期均線(10日)
        data_df["MA_10"] = talib.SMA(data_df["收盤價"], 10)
        # 計算長期均線(20日)
        data_df["MA_20"] = talib.SMA(data_df["收盤價"], 20)
        # 五天平均交易量
        data_df["Volume_5MA"] = talib.SMA(data_df['成交量'], 5)

        for index, row in data_df.iterrows():
            if cash < 0:
                continue
            # 沒有持倉部位時的建倉判斷
            if self.hold_data["BS"] == "":  # 空手
                # 買進條件
                Buy_condition = [
                    row["RSI"] > High_RSI,
                    row["MA_5"] > row["MA_10"],
                    row["MA_10"] > row["MA_20"],
                    row['成交量'] > (row["Volume_5MA"] * 1.5)
                ]
                # 賣出條件
                Sell_condition = [
                    row["RSI"] < Low_RSI,
                    row["MA_5"] < row["MA_10"],
                    row["MA_10"] < row["MA_20"],
                    row['成交量'] > (row["Volume_5MA"] * 1.5)
                ]
                # 若條件全部成立則"做多"
                if all(Buy_condition):
                    trade_price = row["成交價格"]  # 取出當下的成交價格
                    # 以持有資金計算交易量、手續費、並更動持有資訊
                    num, fee = self.get_num_fee_hold(cash, trade_price, "B")

                    # 紀錄做多交易
                    self.Recoding(row["日期"], trade_price, "B", num)

                    # 資金更動，扣除買股票的資金
                    cash -= trade_price * num + fee
                # 若條件全部成立則"做空"
                elif all(Sell_condition):
                    trade_price = row["成交價格"]
                    # 以持有資金計算交易量、手續費、並更動持有資訊
                    num, fee = self.get_num_fee_hold(cash, trade_price, "S")
                    # 紀錄做空交易
                    self.Recoding(row["日期"], trade_price, "S", num)
                    # 證交稅
                    tax = trade_price * num * tax_rate
                    # 資金更動，扣除買股票的資金
                    cash -= trade_price * num + fee + fee + tax
            # 持有部位，平倉判斷
            else:
                # 做多平倉條件
                offset_Buy_condition = [
                    row["MA_5"] < row["MA_10"]
                ]
                # 做空平倉條件
                offset_Sell_condition = [
                    row["MA_5"] > row["MA_10"]
                ]
                # 做多平倉紀錄
                if self.hold_data["BS"] == "B" and any(offset_Buy_condition):
                    num = self.hold_data["num"]  # 當下持有數量
                    trade_price = row["成交價格"]  # 取出當下的成交價格
                    self.Recoding(row["日期"], trade_price, "S", num)
                    # 交易手續費
                    fee = self.fee_cal(trade_price, num)
                    # 證交稅
                    tax = trade_price * num * tax_rate
                    # 平倉取得金額
                    cash += trade_price * num - fee - tax
                    # 清空持有紀錄
                    self.hold_data = {
                        "price": 0,  # 進場價位
                        "num": 0,  # 數量
                        "BS": ""  # 多空標記，空字串代表沒有部位
                    }
                # 做空平倉紀錄
                elif self.hold_data["BS"] == "S" and any(offset_Sell_condition):
                    num = self.hold_data["num"]  # 當下持有數量,將負轉正
                    hold_price = self.hold_data["price"]  # 建倉成交價
                    trade_price = row["成交價格"]  # 取出當下的成交價格
                    self.Recoding(row["日期"], trade_price, "B", num)  # 紀錄平倉交易
                    # 交易手續費
                    fee = self.fee_cal(trade_price, num)
                    # 拿回保證金、賣出價金,減掉回補成本
                    cash += hold_price * num + \
                        (hold_price - trade_price) * num - fee
                    # 清空持有紀錄
                    self.hold_data = {
                        "price": 0,  # 進場價位
                        "num": 0,  # 數量
                        "BS": ""  # 多空標記，空字串代表沒有部位
                    }
        # 最後一日平倉資訊
        last_date = data_df.iloc[-1]["日期"]  # 最後一日日期
        last_trade_price = data_df.iloc[-1]["成交價格"]  # 最後一日成交價格

        if self.hold_data["BS"] == "B":
            num = self.hold_data["num"]
            self.Recoding(last_date, last_trade_price,
                          "S", self.hold_data["num"])
            # 交易手續費
            fee = self.fee_cal(last_trade_price, num)
            # 證交稅
            tax = last_trade_price * num * tax_rate
            # 平倉取得金額
            cash += last_trade_price * self.hold_data["num"] - fee - tax
        elif self.hold_data["BS"] == "S":
            num = self.hold_data["num"]
            hold_price = self.hold_data["price"]
            self.Recoding(last_date, last_trade_price, "B", num)
            # 交易手續費
            fee = self.fee_cal(last_trade_price, num)
            # 拿回保證金、賣出價金,減掉回補成本
            cash += hold_price * num + \
                (hold_price - last_trade_price) * num - fee
        return record_df  # 回傳交易紀錄

    # 計算手續費
    def fee_cal(self, trade_price, num):
        fee_rate = self.fee_rate
        min_fee = self.min_fee
        # 交易手續費
        fee = trade_price * num * fee_rate
        # 手續費不足20則以20元計算
        if fee < min_fee:
            fee = min_fee
        return fee

    def Recoding(self, time, price, BS, num):
        record_df = self.record_df

        if record_df.empty:
            index_count = 0
        else:
            index_count = record_df.index[-1] + 1
        record_df.at[index_count, "time"] = time
        record_df.at[index_count, "price"] = price
        record_df.at[index_count, "BS"] = BS
        record_df.at[index_count, "num"] = num
