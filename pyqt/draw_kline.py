import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt


def main(df, stock_id, cash, rsi_record_df):
    # 重新設定欄位以供繪圖參數使用
    rename_dict = {
        "日期": "date",
        "成交量": "Volume",
        "開盤價": "Open",
        "最高價": "High",
        "最低價": "Low",
        "收盤價": "Close",
    }
    df = df.rename(columns=rename_dict)

    # 使用pd.to_datetime()将"date"列转换为时间序列
    df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d')
    # 使用set_index()方法将"date"列设置为索引
    df.set_index("date", inplace=True)

    # 調整圖表標示顏色
    mc = mpf.make_marketcolors(
        up='tab:red', down='tab:green',  # 上漲為紅，下跌為綠
        wick={'up': 'red', 'down': 'green'},  # 影線上漲為紅，下跌為綠
        volume='tab:blue',  # 交易量顏色
    )
    # 定義圖表風格
    mstyle = mpf.make_mpf_style(marketcolors=mc,
                                rc={
                                    'font.size': 10,  # 文字大小
                                    # 字型
                                    "font.family": ['sans-serif', "Microsoft JhengHei"]
                                }
                                )
    addp = []
    addp.append(mpf.make_addplot(df['MA_5']))
    addp.append(mpf.make_addplot(df['MA_10']))
    addp.append(mpf.make_addplot(df['MA_20']))
    addp.append(mpf.make_addplot(df["RSI"], panel=2))
    addp.append(mpf.make_addplot(df["low_RSI"], panel=2))
    addp.append(mpf.make_addplot(df["high_RSI"], panel=2))
    mpf.plot(df,  # 開高低收量的資料
             type='candle',  # 類型為蠟燭圖，也就是 K 線圖
             style=mstyle,  # 套用圖表風格
             ylabel='價格',  # 設定 Y 軸標題
             title="stock_id",  # 設定圖表標題
             volume=True,  # 顯示量能
             addplot=addp,  # 將均線畫在一起
             savefig='stock_Kbar.png')  # 儲存檔案

    cash = cash

    TA_df = df.iloc[0:, [3, 4, 5, 6, 9]]

    record_df = rsi_record_df
    # 使用pd.to_datetime()将"date"列转换为时间序列
    record_df["time"] = pd.to_datetime(record_df["time"], format='%Y-%m-%d')
    record_df = record_df.rename(columns={"time": "date"})
    # 使用set_index()方法将"date"列设置为索引
    record_df.set_index("date", inplace=True)

    fee_rate = 0.001425
    min_fee = 20
    tax_rate = 0.003
    # 計算買多少張股票
    BaH_num = ((cash // (TA_df['成交價格'].iloc[0] * (1 + fee_rate))) // 1000)*1000
    # 買入的手續費
    BaH_num_buy_fee = TA_df['成交價格'].iloc[0] * BaH_num * fee_rate
    # 買股票的支出
    BaH_buy_stock_cost = (BaH_num * TA_df['成交價格'].iloc[0]) + BaH_num_buy_fee
    # 賣出的手續費
    BaH_sell_fee = TA_df['成交價格'] * BaH_num * fee_rate
    # 賣出的證交稅
    BaH_tax = TA_df['成交價格'] * BaH_num * tax_rate
    # 資本利得
    TA_df["B&H資本利得"] = (BaH_num * TA_df['成交價格']) - BaH_sell_fee - BaH_tax
    #帳戶價值 = 帳戶餘額-買股票的支出+股票現在賣出後的價值
    TA_df["B&H帳戶資產變化"] = cash - BaH_buy_stock_cost + TA_df["B&H資本利得"]

    TA_df = pd.concat([TA_df, record_df], axis=1)

    TA_df["RSI帳戶資產變化"] = pd.NA
    TA_df["股票價值"] = pd.NA
    current_cash = 1000000
    TA_df.iloc[0, 10] = current_cash
    TA_df["rsi資本利得"] = 0


# =============================================================================
#     TA_df["B&H帳戶資產變化"] = TA_df["B&H帳戶資產變化"].astype(int)
#     TA_df["RSI帳戶資產變化"] = TA_df["RSI帳戶資產變化"].astype(int)
#     # 绘制折线图
#     plt.plot(TA_df['RSI帳戶資產變化'], label='RSI Account Asset Change')
#     plt.plot(TA_df['B&H帳戶資產變化'], label='B&H Account Asset Change')
#
#     # 添加标题和标签
#     plt.title("""RSI vs buy&hold
#               Account Asset Change""")
#     plt.xlabel('Date')
#     plt.ylabel('Account Asset Change')
#     # 添加图例
#     plt.legend(['RSI Account Asset', 'B&H Account Asset'])
#     # 设置y轴刻度格式为真实数字
#     plt.ticklabel_format(style='plain', axis='y')
#     # 保存图形为新文件
#     plt.savefig('plot.png')
# =============================================================================
    # 走訪df判斷買賣後的帳戶資產變化
#     for index, row in TA_df.iterrows():
#         # 買進之股票價值
#         TA_df.at[index, "股票價值"] = row['price'] * (row['num']*1000)
#         if row["BS"] == "B":
#             # 買入的手續費
#             rsi_num_buy_fee = row['price'] * (row['num']*1000) * fee_rate
#             # 買股票的支出
#             rsi_buy_stock_cost = ((row['num']*1000) *
#                                   row['price']) + rsi_num_buy_fee
#
#             current_cash -= rsi_buy_stock_cost
#
#             TA_df.at[index, "RSI帳戶資產變化"] = current_cash
#
#         elif row["BS"] == "S":
#             # 賣出的手續費
#             rsi_num_sell_fee = row['price'] * (row['num']*1000) * fee_rate
#             # 賣出的證交稅
#             rsi_tax = row['price'] * (row['num']*1000) * tax_rate
#             # 資本利得
#             TA_df.at[index, "rsi資本利得"] = ((row['num']*1000) * row['price']
#                                           ) - rsi_num_sell_fee - rsi_tax
#             current_cash += TA_df.loc[index, "rsi資本利得"]
#             TA_df.at[index, "RSI帳戶資產變化"] = current_cash
#
#     TA_df["RSI帳戶資產變化"] = TA_df["RSI帳戶資產變化"].fillna(method="ffill")
