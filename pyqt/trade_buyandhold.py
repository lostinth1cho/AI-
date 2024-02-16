import pandas as pd

fee_rate = 0.001425
min_fee = 20
tax_rate = 0.003


def trade(data_df, cash):
    global record_df, hold_data

    # 定義交易紀錄
    record_df = pd.DataFrame(columns=["time", "price", "BS", "num"])

    # 定義持有資訊
    hold_data = {
        "price": 0,
        "num": 0,
        "BS": ""
    }

    if hold_data["BS"] == "":
        trade_price = data_df['成交價格'].iloc[0]

        num, fee = get_num_fee_hold(cash, trade_price, "B")
        Recording(data_df["日期"].iloc[0], trade_price, "B", num)

        cash -= trade_price * num + fee

    # 最後一日平倉資訊
    last_date = data_df.iloc[-1]["日期"]
    last_trade_price = data_df.iloc[-1]["成交價格"]
    if hold_data["BS"] == "B":
        # 若持有數量部位大於0，將做多平倉
        num = hold_data["num"]
        Recording(last_date, last_trade_price, "S", hold_data["num"])

        fee = fee_cal(last_trade_price, num)
        tax = last_trade_price * num * tax_rate

        cash += last_trade_price * hold_data["num"] - fee - tax

    elif hold_data["BS"] == "S":
        num = hold_data["num"]
        hold_price = hold_data["price"]
        Recording(last_date, last_trade_price, "B", num)
        fee = fee_cal(last_trade_price, num)

        cash += hold_price * num + (hold_price - last_trade_price) * num - fee
    return record_df


def get_num_fee_hold(cash, trade_price, BS):
    if BS == "B":
        num = (cash // (trade_price * (1 + fee_rate)))
    else:
        num = (cash // (trade_price * (1 + fee_rate + tax_rate)))
    hold_data["price"] = trade_price
    hold_data["num"] = num
    hold_data["BS"] = BS

    fee = fee_cal(trade_price, num)
    return num, fee


def fee_cal(trade_price, num):
    fee = trade_price * num * fee_rate

    return max(fee, min_fee)


def Recording(time, price, BS, num):

    if record_df.empty:  # 若當下的交易紀錄是空，索引值設為0
        index_count = 0
    else:  # 若交易紀錄簿不是空，索引值為最大值+1
        index_count = record_df.index[-1] + 1

    record_df.at[index_count, "time"] = time
    record_df.at[index_count, "price"] = price
    record_df.at[index_count, "BS"] = BS
    record_df.at[index_count, "num"] = num
