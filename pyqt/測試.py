import mplfinance as plt
import pandas as pd
df = pd.DataFrame()
df = pd.read_excel("全部日K資料.xlsx")
cash = 1000000
# def main(df, stock_id):
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

# =============================================================================
# # 調整圖表標示顏色
# mc = mpf.make_marketcolors(
#     up='tab:red', down='tab:green',  # 上漲為紅，下跌為綠
#     wick={'up': 'red', 'down': 'green'},  # 影線上漲為紅，下跌為綠
#     volume='tab:blue',  # 交易量顏色
# )
# # 定義圖表風格
# mstyle = mpf.make_mpf_style(marketcolors=mc,
#                             rc={
#                                 'font.size': 10,  # 文字大小
#                                 # 字型
#                                 "font.family": ['sans-serif', "Microsoft JhengHei"]
#                             }
#                             )
# addp = []
# addp.append(mpf.make_addplot(df['MA_5']))
# addp.append(mpf.make_addplot(df['MA_10']))
# addp.append(mpf.make_addplot(df['MA_20']))
# addp.append(mpf.make_addplot(df["RSI"], panel=2))
# addp.append(mpf.make_addplot(df["low_RSI"], panel=2))
# addp.append(mpf.make_addplot(df["high_RSI"], panel=2))
# mpf.plot(df,  # 開高低收量的資料
#          type='candle',  # 類型為蠟燭圖，也就是 K 線圖
#          style=mstyle,  # 套用圖表風格
#          ylabel='價格',  # 設定 Y 軸標題
#          title="stock_id",  # 設定圖表標題
#          volume=True,  # 顯示量能
#          addplot=addp,)  # 將均線畫在一起
# # savefig='stock_Kbar.png')  # 儲存檔案
# =============================================================================

#
cash = cash
TA_df = df.iloc[0:, [4, 5, 6, 7, 10]]
record_df = pd.read_excel("交易紀錄.xlsx")
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
# TA_df["B&H帳戶資產變化"].plot()
TA_df = pd.concat([TA_df, record_df], axis=1)


TA_df["RSI帳戶餘額"] = cash
TA_df["RSI多頭部位價值"] = 0
TA_df["RSI空頭部位價值"] = 0
TA_df["RSI帳戶資產變化"] = 0
# 透過"BS"欄位判斷持有部位以及持有時的價值變化
trend = ""
for index, row in TA_df.copy().iterrows():
    if not(pd.isna(row["BS"])) and trend == "":
        trend = row["BS"]
        num = row["num"]
        # 判斷作多與做空的部位並計算帳戶餘額變化
        if row["BS"] == 'B':
            print(index, "B")
        elif row["BS"] == 'S':
            print(index, "S")
        continue
    if trend == "B" and row["BS"] == "S":
        trend = ""
    elif trend == "S" and row["BS"] == "B":
        trend = ""
    elif trend == "B":
        TA_df.at[index, "BS"] = "B"
        TA_df.at[index, "price"] = row["成交價格"]
        TA_df.at[index, "num"] = num
    elif trend == "S":
        TA_df.at[index, "BS"] = "S"
        TA_df.at[index, "price"] = row["成交價格"]
        TA_df.at[index, "num"] = num

#TA_df.at[index, "帳戶餘額"] += row["成交價格"] * (row['num'] * 1000) - rsi_num_sell_fee - rsi_tax
aaaaa
TA_df["RSI帳戶資產變化"] = TA_df["RSI帳戶餘額"] + TA_df["RSI帳戶部位價值"]
# 買進之股票價值
#TA_df["帳戶股票價值"] = TA_df["price"] * TA_df['num'] * 1000
TA_df["rsi資本利得"] = TA_df["price"] * TA_df['num'] * 1000
for index, row in TA_df.copy().iterrows():
    if row["BS"] == "S" or row["BS"] == "B":

        TA_df.at[index, "帳戶餘額"] = a


# 買股票的支出
rsi_buy_stock_cost = ((row['num'].shift(-1)*1000) *
                      row['price'].shift(-1)) + rsi_num_buy_fee
TA_df.at[index-1, "帳戶餘額"] -= rsi_buy_stock_cost
TA_df.at[index-1, "股票價值"] = row['成交價格'].shift(-1) * (row['num'].shift(-1)*1000)

######################################################
# =============================================================================
# print(TA_df["RSI帳戶資產變化"])
#
# TA_df["B&H帳戶資產變化"] = TA_df["B&H帳戶資產變化"].astype(int)
# TA_df["RSI帳戶資產變化"] = TA_df["RSI帳戶資產變化"].astype(int)
# # 绘制折线图
# TA_df['RSI帳戶資產變化'].plot()
# TA_df['B&H帳戶資產變化'].plot()
# # 添加标题和标签
# plt.title("""RSI vs buy&hold
#           Account Asset Change""")
# plt.xlabel('Date')
# plt.ylabel('Account Asset Change')
# # 添加图例
# plt.legend(['RSI Account Asset', 'B&H Account Asset'])
# # 设置y轴刻度格式为真实数字
# plt.ticklabel_format(style='plain', axis='y')
# # 保存图形为新文件
# #plt.savefig('plot.png')
# =============================================================================
