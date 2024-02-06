# -*- coding: utf-8 -*-
from os import listdir
from pymoo.algorithms.moo.nsga2 import NSGA2  # 引用 NSGA2 方法

from pymoo.operators.crossover.pntx import SinglePointCrossover  # 引用交配方法
from pymoo.operators.mutation.pm import PM  # 引用變異方法

from pymoo.core.problem import Problem  # 引用適應函數方法
from pymoo.optimize import minimize  # 引用最小化目標方法

import numpy as np  # 資料整理工具
import pandas as pd

import matplotlib.pyplot as plt  # 繪圖工具
# 引用取得資料、交易、計算績效的程式
from process_data_0204 import get_data, split_data
from trade_0204 import trade_class
from KPI import proc_KPI

# 處理時間套件
from datetime import datetime


class trade_problem(Problem):
    def __init__(self):
        # n_var = 基因數,
        # n_obj = 目標數,
        # n_eq_constr = 相等限制式數量,
        # n_ieq_constr = 小於0限制式數量,
        # xl = 基因最小值,
        # xu = 基因最大值
        # 變數參考 https://pymoo.org/problems/definition.html
        super().__init__(n_var=3,
                         n_obj=3,
                         n_ieq_constr=1,  # 小於等於 0 的限制式
                         n_eq_constr=0,  # 等於 0 的限制式
                         xl=[6, 0, 0],
                         xu=[14, 8, 8]
                         )

    # 評估函數請參考 https://pymoo.org/getting_started/part_2.html
    def _evaluate(self, x, out, *args, **kwargs):
        f1_list = []
        f2_list = []
        f3_list = []
        g1_list = []

        for xi in x:  # 將所有的族群放入適應函數
            # 將 xi 四捨五入到整數位
            # 編碼基因，RSI天數、低檔RSI判斷標準、高檔RSI判斷標準
            xi = xi.round(0)
            RSI_days = xi[0]
            Low_RSI = 10 + xi[1] * 5  # 低檔RSI最低為10 間隔為5 最高為50
            High_RSI = 50 + xi[2] * 5  # 高檔RSI最低為50 間隔為5 最高為90

            # 設定參數字典
            para = {
                "cash": cash,
                "RSI_days": RSI_days,
                "Low_RSI": Low_RSI,
                "High_RSI": High_RSI,
            }

            concated_record_df = pd.DataFrame()  # 儲存交易紀錄
            train_obj.trade(para)  # 使用物件交易方法
            traded_racord_df = train_obj.record_df  # 交易後，取出物件的record_df 屬性
            # 合併交易紀錄
            concated_record_df = pd.concat(
                [concated_record_df, traded_racord_df], axis=0)

            KPI_dict = proc_KPI(concated_record_df,
                                cash, fee_rate, tax_rate)
            
            # 從績效指標取出適應值
            f1 = KPI_dict["累計報酬率"]
            f2 = KPI_dict["帳戶淨值MDD"]
            f3 = KPI_dict["勝率"]

            # 限制累計報酬率不得為負
            g1 = -f1

            # 將適應函數放入串列
            f1_list.append(-f1)  # 求最大累計報酬率
            f2_list.append(f2)  # 最小帳戶淨值MDD
            f3_list.append(-f3)  # 最大勝率
            g1_list.append(g1)  # 累計報酬率不得為負

        out["F"] = np.column_stack([f1_list, f2_list, f3_list])
        out["G"] = np.column_stack([g1_list])


# 主要函數， 傳入族群數，演化代數，交配率，變異率，四個參數
def main(PS, NGEN, CXPB, MUTPB):
    crossover = SinglePointCrossover(prob=CXPB)  # 交配設定
    mut = PM(prob=MUTPB)  # 變異設定

    # 建立演算法物件
    # https://pymoo.org/algorithms/moo/nsga2.html
    algorithm = NSGA2(pop_size=PS,  # 族群數
                      crossover=crossover,  # 交配物件
                      mutation=mut  # 變異物件
                      )

    # 定義問題
    problem = trade_problem()

    # 執行最佳化
    # https://pymoo.org/interface/minimize.html

    res = minimize(problem,  # 問題
                   algorithm,  # 使用演算法
                   ('n_gen', NGEN),  # 設定演化代數
                   save_history=True  # 記錄每一代的結果
                   )

    # 輸出每一代的族群與適應函數
    for i in range(NGEN):
        # =============================================================================
        #         print("第"+str(i+1)+"代")
        #         print("族群")
        #         print(res.history[i].pop.get("X").round(0))  # 輸出族群
        #         print("適應函數")
        #         print(res.history[i].pop.get("F"))  # 輸出適應值
        # =============================================================================

        f1_list = res.history[i].pop.get("F")[:, 0] * -1
        f2_list = res.history[i].pop.get("F")[:, 1]

        title_name = f"{stock_id},GEN" + str(i + 1)
        # 繪圖 要另存圖片
        plt.plot(f2_list, f1_list,  "ro", color="green")
        plt.title(title_name)
        plt.xlabel("MDD")
        plt.ylabel("acc_ROI")
        plt.savefig(f"效率前緣曲線/{title_name}")
        plt.show()

    # 最後一代適應值
    f1_list = res.pop.get("F")[:, 0] * -1
    f2_list = res.pop.get("F")[:, 1]
    f3_list = res.pop.get("F")[:, 2] * -1

    result_df = pd.DataFrame(res.pop.get("X").round(0))  # 將族群變成DF
    result_df["stock_id"] = stock_id
    result_df["累計報酬率"] = f1_list
    result_df["帳戶淨值MDD"] = f2_list
    result_df["勝率"] = f3_list

    # 將結果四捨五入
    result_df["累計報酬率"] = (result_df["累計報酬率"] * 100).round(2)
    result_df["帳戶淨值MDD"] = (result_df["帳戶淨值MDD"] * 100).round(2)
    #
    result_df.columns = ["RSI_days", "Low_RSI", "High_RSI",
                         "stock_id", "累計報酬率", "帳戶淨值MDD", "勝率"]
    result_df.to_excel(
        f"NSGA參數優化與適應值結果/NSGA參數優化與適應值結果{stock_id}.xlsx", index=False)

    for index, row in result_df.copy().iterrows():
        # 解碼基因
        # RSI天數、低檔RSI判斷標準、高檔RSI判斷標準
        RSI_days = row.iloc[0]
        Low_RSI = 10 + row.iloc[1] * 5  # 低檔RSI最低為10 間隔為5 最高為50
        High_RSI = 50 + row.iloc[2] * 5  # 高檔RSI最低為50 間隔為5 最高為90
        # 設定參數字典
        para = {
            "cash": cash,
            "RSI_days": RSI_days,
            "Low_RSI": Low_RSI,
            "High_RSI": High_RSI,
        }
        concated_record_df = pd.DataFrame()

        test_obj.trade(para)  # 使用物件交易方法
        traded_racord_df = test_obj.record_df  # 交易後，取出物件的record_df 屬性
        # 合併交易紀錄
        concated_record_df = pd.concat(
            [concated_record_df, traded_racord_df], axis=0)

        # 計算績效指標
        KPI_dict = proc_KPI(concated_record_df,
                            cash, fee_rate, tax_rate)
        
        # 紀錄測試集結果
        result_df.at[index, "測試集交易次數"] = KPI_dict["交易次數"]
        result_df.at[index, "測試集累計報酬率"] = KPI_dict["累計報酬率"]
        result_df.at[index, "測試集帳戶淨值MDD"] = KPI_dict["帳戶淨值MDD"]
        result_df.at[index, "測試集勝率"] = KPI_dict["勝率"]

    # 將結果四捨五入
    result_df["測試集累計報酬率"] = (result_df["測試集累計報酬率"]*100).round(2)
    result_df["測試集帳戶淨值MDD"] = (result_df["測試集帳戶淨值MDD"]*100).round(2)
    result_df.to_excel(f"測試集結果/NSGA優化參數結果_測試集{stock_id}.xlsx", index=False)


# 開始時間
start_time = datetime.now()
print("開始時間:", start_time)
catched_stock_list = listdir("../FINMIND資料/")
#train_obj_list = []
#test_obj_list = []

for s_id in catched_stock_list:
    # 將檔案名分割成"股票代號",".xlsx"
    s_id: list = s_id.split('.')
    # 只取"股票代號"
    stock_id: str = s_id[0]
    df = get_data(stock_id=stock_id)
    # 個股的資料筆數少於1000的就跳過此迴圈
    if df.shape[0] < 1000:
        continue
    df["成交價格"] = df["開盤價"].shift(-1)
    df = df.dropna()  # 刪除空值
    # 分割訓練 測試
    train_data, test_data = split_data(data=df,
                                       training_part=0.7)
    # 根據資料建構物件
    train_obj = trade_class(train_data)
    test_obj = trade_class(test_data)
    #
    stock_id: int = int(stock_id)
    # 將物件放入串列
    # train_obj_list.append(train_obj)
    # test_obj_list.append(test_obj)
    # 總資金
    cash = 1000000
    fee_rate, tax_rate = 0.001425, 0.003
    PS, NGEN, CXPB, MUTPB = 5, 5, 0.8, 0.01
    main(PS, NGEN, CXPB, MUTPB)

# 結束時間
end_time = datetime.now()
print("結束時間:", end_time)
print("耗費時間:", end_time - start_time)
