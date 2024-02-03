import pandas as pd

def proc_KPI(record_df, origin_cash, fee_rate, tax_rate):
    if record_df.shape[0] == 0:
        output_KPI ={
            #獲益指標
            "累計報酬率" : -999,
            "平均報酬率" : -999,
            #風險指標
            "獲利標準差" : 999,
            #獲利/風險
            "夏普指標" : -999,
            #人性指標
            "交易次數" : 0,
            "勝率" : -999,
            
            #"最大回落(MDD)" : 999,
            #"獲利標準差" : 999,
            #"獲利因子" : -999,
            #"賺賠比" : -999,
            #"期望值" : -999,
            #"最大連續獲利次數" : -999,
            #"最大連續虧損次數"  : 999,
        }
        return output_KPI
    trade_df = pd.DataFrame(columns = ["買入日期", "買入價格", "賣出日期", "賣出價格", "成交量"])
    
    Long_index = 0
    Short_index = 0
    
    for index, row in record_df.iterrows():
        if row["BS"] == "B":
            trade_df.at[Long_index, "買入日期"] = row["time"]
            trade_df.at[Long_index, "買入價格"] = row["price"]
            trade_df.at[Long_index, "成交量"] = row["num"]
            Long_index += 1
        else:
            trade_df.at[Short_index, "賣出日期"] = row["time"]
            trade_df.at[Short_index, "賣出價格"] = row["price"]
            trade_df.at[Short_index, "成交量"] = row["num"]
            Short_index += 1
    #將買入手續費視為成本的增加
    trade_df["買入價格"] = trade_df["買入價格"] * (1 + fee_rate)
    #將賣出手續費與交易稅視為收益減少
    trade_df["賣出價格"] = trade_df["賣出價格"] * (1 - fee_rate - tax_rate)
    
    #交易次數
    trade_times = len(trade_df)
    trade_df["單筆報酬率"] = pd.NA
    for index, row in trade_df.iterrows():
        #做多
        if row["買入日期"] < row["賣出日期"]:
            trade_df.at[index, "單筆報酬率"] = row["賣出價格"] / row["買入價格"] -1
        #做空
        else:
            trade_df.at[index, "單筆報酬率"] = 1 - row["買入價格"] / row["賣出價格"]
    #平均報酬率
    avg_ROI = trade_df["單筆報酬率"].mean()
    #報酬率標準差
    std_ROI = trade_df["單筆報酬率"].std()
    #夏普指標 平均報酬減無風險利率除以標準差
    sharpe = (avg_ROI - 0.01270) / std_ROI
    
    win_rate = (trade_df["單筆報酬率"] > 0).sum() / trade_times
    
    trade_df["獲利金額"] = ( trade_df["賣出價格"] - trade_df["買入價格"]) * trade_df["成交量"]
    
    #累計報酬率
    acc_ROI = trade_df["獲利金額"].sum() / origin_cash
    #win_data = trade_df[trade_df["獲利金額"] > 0]
    #loss_data = trade_df[trade_df["獲利金額"] <= 0]
    
    #獲利因子
    output_KPI ={
            #獲益指標
            "累計報酬率" : round(acc_ROI, 4),
            "平均報酬率" : round(avg_ROI, 4),
            #風險指標
            "獲利標準差" : round(std_ROI, 4),
            #"最大回落(MDD)" : MDD,
            #獲利/風險
            "夏普指標" : round(sharpe),
            #"獲利因子" : profit_factor,
            #"賺賠比" : profit_rate,
            #"期望值" : expected_rate,
            #人性指標
            "交易次數" : trade_times,
            "勝率" : round(win_rate),
            #"最大連續獲利次數" : max_profit_times,
            #"最大連續虧損次數"  : max_loss_times,
        }
    return output_KPI
'''
    if len( loss_data ) > 0 :
        profit_factor = win_data["獲利金額"].sum() / loss_data["獲利金額"].sum()
        profit_factor = abs(profit_factor) #加絕對值方便比較
        profit_factor = round(profit_factor, 2) #四捨五入到第二位(非必要)
    else:
        profit_factor = pd.NA #無法計算 給NA
    
    #賺賠比
    if len( loss_data) > 0:
        profit_rate = win_data["獲利金額"].mean() / loss_data["獲利金額"].mean()
        profit_rate = abs(profit_rate )
        profit_rate = round(profit_rate, 2) 
    else:
        profit_rate = pd.NA 
    
    #期望值
    expected_rate = win_data["獲利金額"].mean() * win_rate + loss_data["獲利金額"].mean() * (1 - win_rate)
    
    #連續獲利與虧損次數
    max_profit_times = 0  #最大連續獲益次數
    max_loss_times = 0    #最大連續虧損次數
    times = 0             #當下的累計次數，紀錄連續獲益，以正數計，虧損以負計
    
    for p in trade_df["獲利金額"] :
        if p > 0 and times >= 0:
            times += 1
        elif p <= 0 and times <= 0:
            times -= 1
        elif p > 0 and times < 0:
            times = 1
        elif p > 0 and times > 0:
            times = -1
            
        max_profit_times = max(times, max_profit_times)
        max_loss_times = min(times, max_loss_times)
        
    max_loss_times = abs(max_loss_times)
    
    trade_df["累計資金"] = trade_df["獲利金額"].cumsum() + origin_cash
    
    peak = 0    #當下高峰
    MDD = 0     #最大回落
    
    for i in trade_df["累計資金"]:
        peak = max(peak, i)
        diff = (peak - i) / peak
        MDD = max(MDD, diff)
        
'''
