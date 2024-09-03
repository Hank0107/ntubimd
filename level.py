import pandas as pd
import numpy as np
import mysql.connector
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

# 資料庫連接配置
db_config = {
    'host': '140.131.114.242',
    'user': 'rootii',
    'password': '!@Aa1234',
    'database': '113-Intelligent investment'
}

# 連接資料庫
conn = mysql.connector.connect(**db_config)

# 加載數據
balance_sheet = pd.read_sql("SELECT * FROM company_data_Balance_sheet", conn)
comprehensive_income = pd.read_sql("SELECT * FROM company_data_comprehensive_income", conn)
ratio = pd.read_sql("SELECT * FROM company_ratio", conn)
stock_data = pd.read_sql("SELECT * FROM stock_data", conn)
funds_holding = pd.read_sql("SELECT * FROM funds_holding", conn)

# 關閉連接
conn.close()

# 數據預處理和特徵工程
financial_data = pd.merge(balance_sheet, comprehensive_income, on=['年度', '季別', 'stock_code', 'stock_name'], how='inner')
financial_data = pd.merge(financial_data, ratio, on=['stock_code', 'stock_name'], how='inner')

print(financial_data.head())

# 基於財務指標創建評估指標，並將結果限制為兩位小數
financial_data['EPS'] = financial_data['基本每股盈餘（元）']  #每股盈餘
financial_data['PE_ratio'] = financial_data['PEratio']  #本益比
financial_data['PB_ratio'] = financial_data['PBratio']  #股價淨值比
financial_data['Debt_to_Equity'] = (financial_data['負債總額'] / financial_data['權益總額']).round(2)  #負債權益比
financial_data['Current_Ratio'] = ((financial_data['流動資產'] / financial_data['流動負債']) * 100).round(2)  #流動比率
financial_data['Gross_Profit_Margin'] = ((financial_data['營業毛利（毛損）'] / financial_data['營業收入']) * 100).round(2)  #毛利率
financial_data['Operating_Profit_Margin'] = ((financial_data['營業利益（損失）'] / financial_data['營業收入']) * 100).round(2)  #營業利益率
financial_data['Net_Profit_Margin'] = ((financial_data['本期淨利（淨損）'] / financial_data['營業收入']) * 100).round(2)  #淨利率
financial_data['ROA'] = ((financial_data['本期淨利（淨損）'] / financial_data['資產總額']) * 100).round(2)  #資產報酬率
financial_data['ROE'] = ((financial_data['本期淨利（淨損）'] / financial_data['權益總額']) * 100).round(2)  #權益報酬率
financial_data['Debt_ratio'] = ((financial_data['負債總額'] / financial_data['資產總額']) * 100).round(2)  #負債比率


# 定義一個非常小的正數來避免除以零的錯誤
#epsilon = 1e-10

# 基於財務指標創建評估指標，並將結果限制為兩位小數
#financial_data['EPS'] = financial_data['基本每股盈餘（元）'].replace(0, epsilon).round(2)
#financial_data['PE_ratio'] = (stock_data['close_price'] / financial_data['EPS']).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['PB_ratio'] = (stock_data['close_price'] / financial_data['每股參考淨值'].replace(0, epsilon)).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['Debt_to_Equity'] = (financial_data['負債總額'] / financial_data['權益總額'].replace(0, epsilon)).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['Current_Ratio'] = ((financial_data['流動資產'] / financial_data['流動負債'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['Gross_Profit_Margin'] = ((financial_data['營業毛利（毛損）'] / financial_data['營業收入'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['Operating_Profit_Margin'] = ((financial_data['營業利益（損失）'] / financial_data['營業收入'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['Net_Profit_Margin'] = ((financial_data['本期淨利（淨損）'] / financial_data['營業收入'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['ROA'] = ((financial_data['本期淨利（淨損）'] / financial_data['資產總額'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['ROE'] = ((financial_data['本期淨利（淨損）'] / financial_data['權益總額'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
#financial_data['Debt_ratio'] = ((financial_data['負債總額'] / financial_data['資產總額'].replace(0, epsilon)) * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(2)

# 新增技術指標特徵
stock_data['price_change'] = stock_data['close_price'].pct_change()  #價格變化
stock_data['ma5'] = stock_data['close_price'].rolling(window=5).mean()
stock_data['ma10'] = stock_data['close_price'].rolling(window=10).mean()
stock_data['ma20'] = stock_data['close_price'].rolling(window=20).mean()
stock_data['ma60'] = stock_data['close_price'].rolling(window=60).mean()
stock_data['ma120'] = stock_data['close_price'].rolling(window=120).mean()
stock_data['ma240'] = stock_data['close_price'].rolling(window=240).mean()

#乖離率
stock_data['bias5'] = ((stock_data['close_price'] - stock_data['ma5']) / stock_data['ma5'] * 100).round(2)
stock_data['bias10'] = ((stock_data['close_price'] - stock_data['ma10']) / stock_data['ma10'] * 100).round(2)
stock_data['bias20'] = ((stock_data['close_price'] - stock_data['ma20']) / stock_data['ma20'] * 100).round(2)
stock_data['bias60'] = ((stock_data['close_price'] - stock_data['ma60']) / stock_data['ma60'] * 100).round(2)
stock_data['bias120'] = ((stock_data['close_price'] - stock_data['ma120']) / stock_data['ma120'] * 100).round(2)
stock_data['bias240'] = ((stock_data['close_price'] - stock_data['ma240']) / stock_data['ma240'] * 100).round(2)

# 相對強度指標（RSI）
delta = stock_data['price_change']
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
stock_data['rsi'] = (100 - (100 / (1 + rs))).round(2)

# 布林通道
stock_data['upper_band'] = (stock_data['close_price'].rolling(window=20).mean() + 2 * stock_data['close_price'].rolling(window=20).std()).round(2)
stock_data['lower_band'] = (stock_data['close_price'].rolling(window=20).mean() - 2 * stock_data['close_price'].rolling(window=20).std()).round(2)

# MACD
ema12 = stock_data['close_price'].ewm(span=12, adjust=False).mean()
ema26 = stock_data['close_price'].ewm(span=26, adjust=False).mean()
stock_data['macd'] = (ema12 - ema26).round(2)

# ATR
high_low = stock_data['high_price'] - stock_data['low_price']
high_close = np.abs(stock_data['high_price'] - stock_data['close_price'].shift())
low_close = np.abs(stock_data['low_price'] - stock_data['close_price'].shift())
tr = high_low.combine(high_close, max).combine(low_close, max)
stock_data['atr'] = tr.rolling(window=14).mean().round(2)

# 成交量加權平均價 (VWAP)
stock_data['cum_price_volume'] = (stock_data['close_price'] * stock_data['total_volume']).cumsum()
stock_data['cum_volume'] = stock_data['total_volume'].cumsum()
stock_data['vwap'] = (stock_data['cum_price_volume'] / stock_data['cum_volume']).round(2)

# 隨機指標
low_min = stock_data['low_price'].rolling(window=14).min()
high_max = stock_data['high_price'].rolling(window=14).max()
stock_data['stochastic_k'] = ((stock_data['close_price'] - low_min) / (high_max - low_min) * 100).round(2)
stock_data['stochastic_d'] = stock_data['stochastic_k'].rolling(window=3).mean().round(2)

# 指數移動平均線 (EMA)
stock_data['ema20'] = stock_data['close_price'].ewm(span=20, adjust=False).mean().round(2)
stock_data['ema50'] = stock_data['close_price'].ewm(span=50, adjust=False).mean().round(2)

# 動量指標
stock_data['momentum'] = stock_data['close_price'].diff(10).round(2)

# 威廉指數 (Williams %R)
highest_high = stock_data['high_price'].rolling(window=14).max()
lowest_low = stock_data['low_price'].rolling(window=14).min()
stock_data['williams_r'] = ((highest_high - stock_data['close_price']) / (highest_high - lowest_low) * -100).round(2)

# 商品通道指數 (CCI)
tp = (stock_data['high_price'] + stock_data['low_price'] + stock_data['close_price']) / 3
sma_tp = tp.rolling(window=20).mean()
mean_deviation = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
stock_data['cci'] = ((tp - sma_tp) / (0.015 * mean_deviation)).round(2)

# 三重指標 (TRIX)
single_ema = stock_data['close_price'].ewm(span=15, adjust=False).mean()
double_ema = single_ema.ewm(span=15, adjust=False).mean()
triple_ema = double_ema.ewm(span=15, adjust=False).mean()
stock_data['trix'] = triple_ema.pct_change().round(2)

# 平均定向指標 (ADX)
# True Range (TR) calculation
high_low = stock_data['high_price'] - stock_data['low_price']
high_close = abs(stock_data['high_price'] - stock_data['close_price'].shift(1))
low_close = abs(stock_data['low_price'] - stock_data['close_price'].shift(1))
tr = high_low.combine(high_close, max).combine(low_close, max)

# Plus Directional Movement (+DM) and Minus Directional Movement (-DM)
plus_dm = stock_data['high_price'].diff()
minus_dm = stock_data['low_price'].diff()

plus_dm[(plus_dm <= 0) | (plus_dm <= minus_dm)] = 0
minus_dm[(minus_dm >= 0) | (minus_dm >= plus_dm)] = 0

# Smoothed TR, +DI, and -DI
tr_smooth = tr.rolling(window=14).mean()
plus_di = 100 * (plus_dm.ewm(span=14, adjust=False).mean() / tr_smooth)
minus_di = 100 * (abs(minus_dm).ewm(span=14, adjust=False).mean() / tr_smooth)

# DX and ADX calculation
dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
stock_data['adx'] = dx.rolling(window=14).mean().round(2)


# 合併財務數據和股價數據
data = pd.merge(stock_data, financial_data, on=['stock_code', 'stock_name'], how='inner')

# 選擇特徵和目標變量
evaluation_features = [
    'EPS', 'PE_ratio', 'PB_ratio', 'DividendYield', 'Debt_to_Equity', 'Current_Ratio',
    'Gross_Profit_Margin', 'Operating_Profit_Margin', 'Net_Profit_Margin', 
    'ROA', 'ROE', 'Debt_ratio', '流動資產', '非流動資產', '資產總額', '流動負債',
    '非流動負債', '負債總額', '資本公積', '保留盈餘', '權益總額', '每股參考淨值',
    '本期淨利（淨損）', '基本每股盈餘（元）', 'ma5', 'ma10', 'ma20' , 'ma60', 'ma120', 'ma240',
    'bias5', 'bias10', 'bias20' , 'bias60', 'bias120', 'bias240', 'rsi', 'upper_band', 'lower_band', 'macd', 'atr',
    'vwap', 'stochastic_k', 'stochastic_d', 'ema20', 'ema50', 'momentum', 'williams_r', 'cci', 'trix', 'adx'
]
X = data[evaluation_features]
y = (data['price_change'] > 0).astype(int)

# 檢查每一列是否包含無窮大或非常大的值
for col in X.columns:
    if np.isinf(X[col]).any() or (np.abs(X[col]) > 1e10).any():
        print(f"Column {col} contains infinity or very large values")
        print(X[X[col] == np.inf])
        print(X[np.abs(X[col]) > 1e10])
        
# 訓練測試集劃分
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 標準化數據
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 使用XGBoost進行模型訓練和調參
xgb_model = XGBClassifier(random_state=42)
param_grid = {
    'n_estimators': [50, 100, 150],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1]
}

grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_

# 模型評估
y_pred = best_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'最佳模型準確度: {accuracy:.2f}')

#data.drop_duplicates(subset=['stock_code', 'stock_name'], keep='last', inplace=True)

# 計算每支股票的performance
data['performance'] = best_model.predict_proba(scaler.transform(data[evaluation_features]))[:, 1]

avg_performance = data.groupby(['stock_code', 'stock_name']).agg({
    'Debt_to_Equity': 'last',
    'Current_Ratio': 'last',
    'Gross_Profit_Margin': 'last',
    'Operating_Profit_Margin': 'last',
    'Net_Profit_Margin': 'last',
    'ROA': 'last',
    'ROE': 'last',
    'Debt_ratio': 'last',
    'performance': 'mean'
}).reset_index()

print(avg_performance)

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# 創建新的表格來儲存財務指標和股票表現
create_table_query = """
CREATE TABLE IF NOT EXISTS stock_performance (
    stock_code VARCHAR(255),
    stock_name VARCHAR(255),
    Debt_to_Equity FLOAT,
    Current_Ratio FLOAT,
    Gross_Profit_Margin FLOAT,
    Operating_Profit_Margin FLOAT,
    Net_Profit_Margin FLOAT,
    ROA FLOAT,
    ROE FLOAT,
    Debt_ratio FLOAT,
    performance FLOAT
)
"""
cursor.execute(create_table_query)

delete_query = "DELETE FROM stock_performance"
cursor.execute(delete_query)

for _, row in avg_performance.iterrows():
    insert_query = """
    INSERT INTO stock_performance (stock_code, stock_name, Debt_to_Equity, Current_Ratio, Gross_Profit_Margin, 
    Operating_Profit_Margin, Net_Profit_Margin, ROA, ROE, Debt_ratio, performance)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = [
        row['stock_code'], row['stock_name'], row['Debt_to_Equity'], row['Current_Ratio'], 
        row['Gross_Profit_Margin'], row['Operating_Profit_Margin'], row['Net_Profit_Margin'], 
        row['ROA'], row['ROE'], row['Debt_ratio'], row['performance']
    ]
    cursor.execute(insert_query, tuple(values))

conn.commit()
cursor.close()
conn.close()

print('stock_performance寫入成功')

funds_holding['stock_ratio'] = funds_holding['stock_ratio'].str.rstrip('%').astype(float)
stock_hold_data = pd.merge(funds_holding, avg_performance[['stock_name', 'performance']], left_on='stock_name', right_on='stock_name', how='left')
stock_hold_data['performance'] = stock_hold_data['performance'].fillna(0)

# 計算每個ETF持有台灣股票的加權平均表現
def weighted_performance(group):
    total_percentage = group['stock_ratio'].sum()
    group['weighted_performance'] = group['performance'] * group['stock_ratio'] / total_percentage
    return group

stock_hold_data = stock_hold_data.groupby('fund_code', group_keys=False).apply(weighted_performance)

# 計算加權平均表現
etf_performance = stock_hold_data.groupby(['fund_code', 'fund_name'])['weighted_performance'].sum().reset_index(name='average_performance')

# 過濾掉average_performance為0的行
etf_performance = etf_performance[etf_performance['average_performance'] > 0]

# ETF遞減排序
sorted_etfs = etf_performance.sort_values(by='average_performance', ascending=False)

# 排序
sorted_etfs['rank'] = sorted_etfs['average_performance'].rank(method='dense', ascending=False).astype(int)

# 顯示排序結果
sorted_etfs = sorted_etfs[['rank', 'fund_code', 'fund_name', 'average_performance']]

print(sorted_etfs)

# 重新連接資料庫進行寫入操作
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS etf_performance (
    rank INT,
    fund_code VARCHAR(255),
    fund_name VARCHAR(255),
    average_performance FLOAT
)
"""
cursor.execute(create_table_query)

delete_query = "DELETE FROM etf_performance"
cursor.execute(delete_query)

for _, row in sorted_etfs.iterrows():
    insert_query = """
    INSERT INTO etf_performance (rank, fund_code, fund_name, average_performance)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, tuple(row))

conn.commit()
cursor.close()
conn.close()

print('etf_performance寫入完成')