from os import listdir
import pandas as pd
from trade import trade
from get_tech import get_tech
from KPI import proc_KPI
from process_data import get_data, split_data

# 初始金額設定
cash = 1e6

catched_stock_list = listdir("FINMIND資料/")
# 空DataFrame紀錄最後結果
all_stock_performance = pd.DataFrame()
for s_id in catched_stock_list:
    # 將檔案名分割成"股票代號",".xlsx"
    s_id: list = s_id.split('.')
    # 只取"股票代號"
    stock_id: str = s_id[0]
    # 取得"股票代號"的資料
    df = get_data(stock_id=stock_id)
    if df.shape[0] < 1000:
        continue
    print("id:", s_id[0])
    # 計算技術指標
    df = get_tech(df)
    # 資料分割為訓練和測驗集
    train_data, test_data = split_data(data=df, train_part=0.7)
    # 經過交易後產生交易紀錄
    train_record = trade(train_data, cash)
    test_record = trade(test_data, cash)

    fee_rate = 0.001425  # 手續費
    tax_rate = 0.003  # 證交稅
    # 計算KPI
    train_KPI: dict() = proc_KPI(train_record, cash, fee_rate, tax_rate)
    test_KPI: dict() = proc_KPI(test_record, cash, fee_rate, tax_rate)
    # 轉換成DataFrame
    train_KPI_df = pd.DataFrame(train_KPI, index=[0])
    test_KPI_df = pd.DataFrame(test_KPI, index=[0])
    # 重新命名欄位以便區分
    train_KPI_df.columns = ["訓練集累計報酬率", "訓練集平均報酬率", "訓練集帳戶淨值(MDD)",
                            "訓練集獲利標準差", "訓練集賺賠比", "訓練集交易次數", "訓練集勝率",
                            "訓練集最大連續獲利次數", "訓練集最大連續虧損次數"]
    test_KPI_df.columns = ["測試集累計報酬率", "測試集平均報酬率", "測試集帳戶淨值(MDD)",
                           "測試集獲利標準差", "測試集賺賠比", "測試集交易次數", "測試集勝率",
                           "測試集最大連續獲利次數", "測試集最大連續虧損次數"]
    # 將訓練集和測試集合併
    result_df = pd.concat([train_KPI_df.reset_index(),
                           test_KPI_df.reset_index()],
                          axis=1)
    # 把索引改成股票代號
    result_df = result_df.drop(['index'], axis=1)
    result_df.index.name = 'stock_id'
    result_df.index = [f'{stock_id}']
    # 紀錄最後結果
    all_stock_performance = pd.concat([all_stock_performance, result_df])
    all_stock_performance.to_excel("策略回測.xlsx")
    # 輸出excel
# =============================================================================
#     performance_result_df = all_stock_performance.copy()
#     # 輸入取出範圍 , []內指定取出的欄位
#     performance_result_df = performance_result_df.loc[:, ["訓練集累計報酬率"]]
#     #performance_result_df.to_excel("結果.xlsx", index=False)
# =============================================================================
