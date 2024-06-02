def crawl_and_insert_stock_data():
    import datetime
    import requests
    import pandas as pd
    import time
    from bs4 import BeautifulSoup
    import mysql.connector

    # 連接到 MySQL 資料庫
    conn = mysql.connector.connect(
        host="140.131.114.242",
        user="rootii",
        password="!@Aa1234",
        database="113-Intelligent investment"
    )
    cursor = conn.cursor()

    # 取得資料庫中已存在的日期資料
    cursor.execute("SELECT DISTINCT date FROM stock_data")
    existing_dates = [date[0] for date in cursor.fetchall()]

    # 關閉資料庫連線
    conn.close()

    # 設定開始日期為資料庫中最後一個日期的下一天
    start_date = datetime.datetime.strptime(str(existing_dates[-1]), '%Y-%m-%d') + datetime.timedelta(days=1)
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
        df = df.rename({'證券代號': 'stock_code', '證券名稱': 'stock_name', '開盤價': 'open_price', '最高價': 'high_price',
                        '最低價': 'low_price', '收盤價': 'close_price', '漲跌(+/-)': 'pos_neg', '漲跌價差':'change_percent', '成交股數': 'total_volume', '成交金額': 'total_value'}, axis=1)
        df.insert(0, 'date', iDate, True)

        df = df.replace('', 0)

        # 將每個日期的資料合併到 all_etf_data DataFrame 中
        all_etf_data = pd.concat([all_etf_data, df], ignore_index=True)

        time.sleep(1)
        print(all_etf_data)

    # 重新連接到 MySQL 資料庫
    conn = mysql.connector.connect(
        host="140.131.114.242",
        user="rootii",
        password="!@Aa1234",
        database="113-Intelligent investment"
    )
    cursor = conn.cursor()

    # 迴圈插入新日期資料到 MySQL 資料庫
    for index, row in all_etf_data.iterrows():
        sql = "INSERT INTO stock_data (date, stock_code, stock_name, open_price, high_price, low_price, close_price, pos_neg, change_percent, total_volume, total_value) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (row['date'], row['stock_code'], row['stock_name'], row['open_price'], row['high_price'], row['low_price'], row['close_price'], row['pos_neg'], row['change_percent'], row['total_volume'], row['total_value'])
        cursor.execute(sql, val)

    # 提交資料庫變更
    conn.commit()

    # 關閉資料庫連線
    conn.close()

    print("新增日期資料匯入 MySQL 完成")
