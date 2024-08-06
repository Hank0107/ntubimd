import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 設定台灣主要ETF的列表
etf_list = ['0050.TW', '0056.TW', '006208.TW', '00692.TW', '00701.TW', '00713.TW']

# 定義下載ETF資料的函數
def download_data(selected_etfs):
    data = yf.download(selected_etfs, start="2018-01-01", end="2024-08-01")['Adj Close']
    if data.empty:
        messagebox.showerror("錯誤", "無法下載所選ETF的數據。")
    else:
        return data

# 定義計算投資組合結果的函數
def calculate_portfolio():
    selected_etfs = [etf_listbox.get(i) for i in etf_listbox.curselection()]
    if not selected_etfs:
        messagebox.showwarning("提示", "請至少選擇一個ETF。")
        return

    # 下載ETF數據
    Close = download_data(selected_etfs)

    # 計算共變異數矩陣
    cov_matrix = Close.pct_change().apply(lambda x: np.log(1 + x)).cov()

    # 計算預期報酬率
    expected_return = Close.resample('Y').last()[:-1].pct_change().mean()

    # 計算標準差
    standard_dev = Close.pct_change().apply(lambda x: np.log(1 + x)).std().apply(lambda x: x * np.sqrt(250))

    # 計算夏普比率
    risk_free_rate = 0.01  # 設定無風險利率
    sharpe_ratio = (expected_return - risk_free_rate) / standard_dev

    # 整理成表格
    return_dev_matrix = pd.concat([expected_return, standard_dev, sharpe_ratio], axis=1)
    return_dev_matrix.columns = ['預期報酬率', '標準差', '夏普比率']

    # 計算投資組合報酬與風險
    port_ret = []
    port_dev = []
    port_sharpe = []
    port_weights = []
    assets_nums = len(selected_etfs)
    port_nums = 2000

    for port in range(port_nums):
        weights = np.random.random(assets_nums)
        weights = weights / np.sum(weights)
        port_weights.append(weights)
        returns, ann_sd = calculate_portfolio_performance(weights, expected_return, cov_matrix)
        sharpe_ratio = (returns - risk_free_rate) / ann_sd
        port_ret.append(returns)
        port_dev.append(ann_sd)
        port_sharpe.append(sharpe_ratio)

    data = {'報酬率': port_ret, '標準差': port_dev, '夏普比率': port_sharpe}
    for counter, symbol in enumerate(Close.columns.tolist()):
        data[symbol + ' 權重'] = [w[counter] for w in port_weights]

    portfolios = pd.DataFrame(data)

    # 繪製效率前緣
    fig, ax = plt.subplots(figsize=(15, 10))
    scatter = ax.scatter(x=portfolios['標準差'], y=portfolios['報酬率'], c=portfolios['夏普比率'], cmap='YlGnBu', marker='o')
    plt.colorbar(scatter, label='夏普比率')
    ax.set_xlabel("標準差", fontsize=20)
    ax.set_ylabel("預期報酬率", fontsize=20)
    ax.set_title('效率前緣', fontsize=20)
    ax.grid()

    # 顯示效率前緣的投資組合
    std = []
    ret = [portfolios[portfolios['標準差'] == portfolios['標準差'].min()]['報酬率'].values[0]]
    eff_front_set = pd.DataFrame(columns=['報酬率', '標準差'] + [f'{symbol} 權重' for symbol in Close.columns])
    for i in range(800, 1800, 1):
        df = portfolios[(portfolios['標準差'] >= i / 10000) & (portfolios['標準差'] <= (i + 15) / 10000)]
        try:
            max_ret = df[df['報酬率'] == df['報酬率'].max()]['報酬率'].values[0]
            if max_ret >= max(ret):
                std.append(df[df['報酬率'] == df['報酬率'].max()]['標準差'].values[0])
                ret.append(df[df['報酬率'] == df['報酬率'].max()]['報酬率'].values[0])
                eff_front_set = eff_front_set.append(df[df['報酬率'] == df['報酬率'].max()], ignore_index=True)
        except:
            pass

    ret.pop(0)
    eff_front_std = pd.Series(std)
    eff_front_ret = pd.Series(ret)

    # 標註效率前緣
    ax.scatter(x=eff_front_std, y=eff_front_ret, c='r')

    # 顯示結果
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # 顯示結果
    result_window = tk.Toplevel(root)
    result_window.title("計算結果")

    tk.Label(result_window, text="ETF 預期報酬率、標準差及夏普比率", font=("Arial", 14)).pack(pady=10)
    result_text = tk.Text(result_window, height=10, width=80)
    result_text.insert(tk.END, return_dev_matrix.to_string())
    result_text.pack()

    tk.Label(result_window, text="\n效率前緣組合", font=("Arial", 14)).pack(pady=10)
    eff_text = tk.Text(result_window, height=15, width=80)
    eff_text.insert(tk.END, eff_front_set.to_string())
    eff_text.pack()

    # 顯示選擇的最佳投資組合的圓餅圖
    best_portfolio = portfolios.loc[portfolios['報酬率'].idxmax()]
    weights = [best_portfolio[f'{symbol} 權重'] for symbol in Close.columns]
    labels = Close.columns

    pie_fig, pie_ax = plt.subplots(figsize=(8, 8))
    pie_ax.pie(weights, labels=labels, autopct='%1.1f%%', startangle=140)
    pie_ax.set_title("最佳投資組合的權重分配", fontsize=16)

    pie_canvas = FigureCanvasTkAgg(pie_fig, master=result_window)
    pie_canvas.draw()
    pie_canvas.get_tk_widget().pack()

# 計算投資組合報酬與風險的輔助函數
def calculate_portfolio_performance(weights, expected_return, cov_matrix):
    returns = np.dot(weights, expected_return)
    var = cov_matrix.mul(weights, axis=0).mul(weights, axis=1).sum().sum()
    sd = np.sqrt(var)
    ann_sd = sd * np.sqrt(250)
    return returns, ann_sd

# GUI界面設置
root = tk.Tk()
root.title("ETF 投資組合選擇")

# 標題
label = tk.Label(root, text="選擇你要的ETF商品", font=("Arial", 14))
label.pack(pady=10)

# ETF列表
etf_listbox = tk.Listbox(root, selectmode="multiple", font=("Arial", 12), width=30, height=10)
for etf in etf_list:
    etf_listbox.insert(tk.END, etf)
etf_listbox.pack()

# 計算按鈕
button = tk.Button(root, text="計算", command=calculate_portfolio, font=("Arial", 12))
button.pack(pady=20)

root.mainloop()