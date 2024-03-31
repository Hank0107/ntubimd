import datetime
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup

# 指定開始日期和結束日期
start_date = datetime.datetime(2014, 3, 31)
end_date = datetime.datetime.now()

# 建立日期範圍列表
dateList = [(start_date + datetime.timedelta(days=i)).strftime('%Y%m%d') for i in range((end_date - start_date).days + 1)]

# 建立空的 DataFrame 用於存儲所有 ETF 的資料
all_etf_data = pd.DataFrame()

# 迴圈日期下載資料
for iDate in dateList:
    # 下載證交所資料
    # 取得目標日期資料
    url = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date=' + iDate + '&type=ALLBUT0999'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 判斷是否有空資料存在 若存在則跳離此次迴圈
    if '很抱歉，沒有符合條件的資料!' in soup.text:
        continue

    # 整理證交所每日收盤行情表
    table = soup.find_all('table')[8]
    columnNames = table.find('thead').find_all('tr')[2].find_all('td')
    columnNames = [elem.getText() for elem in columnNames]
    rowDatas = table.find('tbody').find_all('tr')
    rows = list()
    for row in rowDatas:
        rows.append([elem.getText().replace(',', '').replace('--', '') for elem in row.find_all('td')])
    df = pd.DataFrame(data=rows, columns=columnNames)
    df = df[['證券代號', '證券名稱', '開盤價', '最高價', '最低價', '收盤價', '漲跌(+/-)', '漲跌價差', '成交股數', '成交金額']]
    df = df.rename({'證券代號': 'code', '證券名稱': 'name', '開盤價': 'open', '最高價': 'high',
                    '最低價': 'low', '收盤價': 'close', '漲跌(+/-)': 'pos/neg', '漲跌價差':'change', '成交股數': 'volume', '成交金額': 'value'}, axis=1)
    df.insert(0, 'date', iDate, True)
    
    # 將每個日期的資料合併到 all_etf_data DataFrame 中
    all_etf_data = pd.concat([all_etf_data, df], ignore_index=True)

    time.sleep(1)

# 分別儲存每個 ETF 的資料到不同的 CSV 檔案中
for code in all_etf_data['code'].unique():
    etf_data = all_etf_data[all_etf_data['code'] == code]
    file_name = f"C:/stock/data/{code}.csv"
    etf_data.to_csv(file_name, index=False)

print("下載完成")