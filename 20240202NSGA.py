from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.pntx import SinglePointCrossover
from pymoo.operators.mutation.pm import PM
from pymoo.core.problem import Problem
from pymoo.optimize import minimize

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from process_data import get_data, split_data
from trade import trade_class
from KPI import proc_KPI

from datetime import datetime

class trade_problem(Problem):
    def __init__(self):
        super().__init__(n_var = 12, 
                        n_obj = 2,
                        n_ieq_constr = 1,
                        n_eq_constr = 0,
                        xl = [1,1,1,1,1,0,0, 5, 2, 2, 2, 2], 
                        xu = [5,5,5,5,5,8,8,15,10,10,10,10])
        concated_record_df = pd.DataFrame()
    def _evaluate(self, x, out, *args, **kwargs):
        f1_list = []
        f2_list = []
        g1_list = []
        
        for xi in x :
            xi = xi.round(0)
            
            cash_part_list = xi[0:5]
            cash_part_list = cash_part_list / cash_part_list.sum()
            cash_part_list = (cash_part_list * total_cash).round(0)
            
            Long_RSI = 10 + xi[5] * 5
            Short_RSI = 50 + xi[6] * 5
            RSI_days = xi[7]
            
            L_profit_offset_rate = xi[8]/100
            L_loss_offset_rate = xi[9]/100
            S_profit_offset_rate = xi[10]/100
            S_loss_offset_rate = xi[11]/100
            
            para = {
                "Long_RSI": Long_RSI,
                "Short_RSI": Short_RSI,
                "RSI_days" :RSI_days,
                "L_profit_offset_rate": L_profit_offset_rate,
                "L_loss_offset_rate": L_loss_offset_rate,
                "S_profit_offset_rate": S_profit_offset_rate,
                "S_loss_offset_rate": S_loss_offset_rate
            }
            
            concated_record_df = pd.DataFrame()
            for i in range(5):
                para["cash"] = cash_part_list[i]
                train_obj = train_obj_list[i]
                train_obj.trade(para)
                traded_record_df = train_obj.record_df
                concated_record_df = pd.concat([concated_record_df, traded_record_df], axis=0)
            KPI_dict = proc_KPI(concated_record_df, total_cash, fee_rate, tax_rate)
            
            f1 = KPI_dict["累計報酬率"]
            f2 = KPI_dict["最大回落(MDD)"]
            g1 = -f1
            
            f1_list.append(-f1)
            f2_list.append(f2)
            g1_list.append(g1)
            
        out["F"] = np.column_stack( [f1_list, f2_list])
        out["G"] = np.column_stack( [g1_list])
        
def main(PS, NGEN, CXPB, MUTPB):
    crossover = SinglePointCrossover( prob = CXPB)
    mut = PM( prob=MUTPB)
    
    algorithm = NSGA2(pop_size=PS,
                        crossover=crossover,
                        mutation=mut)
    
    problem = trade_problem()
    
    res = minimize(problem, algorithm, ('n_gen', NGEN), save_history=True)
    
    for i in range(NGEN):
        print("第" + str(i+1) + "代")
        print("族群")
        print(res.history[i].pop.get("X").round(0))
        print("適應函數")
        print(res.history[i].pop.get("F"))
    
        f1_list = res.history[i].pop.get("F")[:,0] * -1
        f2_list = res.history[i].pop.get("F")[:,1]
    
        plt.plot(f1_list, f2_list, "ro", color='green')
        plt.title("GEN" + str(i+1))
        plt.xlabel("acc_ROI")
        plt.ylabel("MDD")
        plt.show()
    
    f1_list = res.pop.get("F")[:,0] * -1
    f2_list = res.pop.get("F")[:,1]
    
    result_df = pd.DataFrame(res.pop.get("X").round(0))
    
    result_df["累計報酬率"] = f1_list
    result_df["最大回落(MDD)"] = f2_list
    
    result_df["累計報酬率"] = (result_df["累計報酬率"] * 100).round(2)
    result_df["最大回落(MDD)"] = (result_df["最大回落(MDD)"] * 100).round(2)
    
    result_df.columns = stock_list + ["Long_RSI", "Short_RSI", "RSI_days",
                                        "做多停利", "做多停損", "做空停利", "做空停損",
                                        "累計報酬率", "最大回落(MDD)"]
    result_df.to_excel("NSGA2優化參數結果.xlsx", index = False)
    
    for index, row in result_df.copy().iterrows():
        #解碼
        cash_part_list = row.iloc[0:5]
        cash_part_list = cash_part_list / cash_part_list.sum()
        cash_part_list = (cash_part_list * total_cash).round(0).to_list()
        
        Long_RSI = 10 + row.iloc[5]
        Short_RSI = 50+row.iloc[6] * 5
        RSI_days = row.iloc[7]
        
        L_profit_offset_rate = row.iloc[8]/100
        L_loss_offset_rate = row.iloc[9]/100
        S_profit_offset_rate = row.iloc[10]/100
        S_loss_offset_rate = row.iloc[11]/100

        para = {
            "Long_RSI": Long_RSI,
            "Short_RSI": Short_RSI,
            "RSI_days" :RSI_days,
            "L_profit_offset_rate": L_profit_offset_rate,
            "L_loss_offset_rate": L_loss_offset_rate,
            "S_profit_offset_rate": S_profit_offset_rate,
            "S_loss_offset_rate": S_loss_offset_rate
        }
        concated_record_df = pd.DataFrame()
        
        for i in range(5):
            para["cash"] = cash_part_list[i]
            train_obj = test_obj_list[i]
            train_obj.trade(para)
            traded_record_df = train_obj.record_df
            
            concated_record_df = pd.concat([concated_record_df, traded_record_df], axis = 0)
        
        KPI_dict = proc_KPI(concated_record_df, total_cash, fee_rate, tax_rate)
        
        result_df.at[index, "測試集交易次數"] = KPI_dict["交易次數"]
        result_df.at[index, "測試集累計報酬率"] = KPI_dict["累計報酬率"]
        result_df.at[index, "測試集最大回落(MDD)"] = KPI_dict["最大回落(MDD)"]
        
    result_df["測試集累計報酬率"] = (result_df["測試集累計報酬率"] * 100).round(2)
    result_df["測試集最大回落(MDD)"] = (result_df["測試集最大回落(MDD)"] * 100).round(2)
    
    result_df.to_excel("NSGAu優化參數結果_測試集.xlsx", index = False)
    
start_time = datetime.now()
print(start_time)

selected_stock_df = pd.read_excel("NSGA2最後一代結果.xlsx")
selected_stock_df = selected_stock_df.sort_values(by=["平均相關係數"], ascending=[True])
stock_list = selected_stock_df.iloc[0, :5].astype(int).to_list()

train_obj_list = []
test_obj_list = []

for stock_id in stock_list:
    
    df = get_data(stock_id=stock_id)
    
    df["成交價格"] = df["開盤價"].shift(-1)
    df.dropna()
    train_data, test_data = split_data(data=df, training_part = 0.7)
    
    train_obj = trade_class(train_data)
    test_obj = trade_class(test_data)
    
    train_obj_list.append(train_obj)
    test_obj_list.append(test_obj)

total_cash = 1e7
fee_rate, tax_rate = 0.001425, 0.003
PS, NGEN, CXPB, MUTPB = 100, 20, 0.8, 0.01
main(PS, NGEN, CXPB, MUTPB)

end_time = datetime.now()

print("開始運算時間", start_time)
print("結束運算時間", end_time)
print("花費運算時間", end_time - start_time)