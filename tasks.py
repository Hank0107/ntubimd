import datetime
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
import mysql.connector
import pymysql

def crawl_and_insert_stock_data():
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

    if existing_dates:
        last_date = datetime.datetime.strptime(str(existing_dates[-1]), '%Y-%m-%d')
    else:
        last_date = datetime.datetime.now() - datetime.timedelta(days=10*365)
    
    # 關閉資料庫連線
    conn.close()

    # 設定開始日期為資料庫中最後一個日期的下一天
    start_date = last_date + datetime.timedelta(days=1)
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

def crawl_and_insert_juridical_data():
    conn = mysql.connector.connect(
        host="140.131.114.242",
        user="rootii",
        password="!@Aa1234",
        database="113-Intelligent investment"
    )
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT date FROM juridical_data")
    existing_dates = [date[0] for date in cursor.fetchall()]

    if existing_dates:
        last_date = datetime.datetime.strptime(str(existing_dates[-1]), '%Y-%m-%d')
    else:
        last_date = datetime.datetime.now() - datetime.timedelta(days=2*365)

    start_date = last_date + datetime.timedelta(days=1)
    end_date = datetime.datetime.now()

    date_list = [(start_date + datetime.timedelta(days=i)).strftime('%Y%m%d') for i in range((end_date - start_date).days + 1)]

    data_list = []

    for iDate in date_list:
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={iDate}&selectType=ALLBUT0999&response=html"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")
        if table is None:
            continue
        rows = table.find_all("tr")
        for row in rows[2:]:
            cols = row.find_all("td")
            if len(cols) == 19:
                date = datetime.datetime.strptime(iDate, '%Y%m%d').strftime('%Y-%m-%d')
                stock_code = cols[0].text.strip()
                stock_name = cols[1].text.strip()
                foreign_investors_buy = int(cols[2].text.replace(",", ""))
                foreign_investors_sell = int(cols[3].text.replace(",", ""))
                foreign_investors_diff = int(cols[4].text.replace(",", ""))
                foreign_self_buy = int(cols[5].text.replace(",", ""))
                foreign_self_sell = int(cols[6].text.replace(",", ""))
                foreign_self_diff = int(cols[7].text.replace(",", ""))
                investment_trust_buy = int(cols[8].text.replace(",", ""))
                investment_trust_sell = int(cols[9].text.replace(",", ""))
                investment_trust_diff = int(cols[10].text.replace(",", ""))
                dealer_total_diff = int(cols[11].text.replace(",", ""))
                dealer_self_buy = int(cols[12].text.replace(",", ""))
                dealer_self_sell = int(cols[13].text.replace(",", ""))
                dealer_self_diff = int(cols[14].text.replace(",", ""))
                dealer_hedge_buy = int(cols[15].text.replace(",", ""))
                dealer_hedge_sell = int(cols[16].text.replace(",", ""))
                dealer_hedge_diff = int(cols[17].text.replace(",", ""))
                total_diff = int(cols[18].text.replace(",", ""))
                
                data_list.append((
                    date, stock_code, stock_name, foreign_investors_buy, foreign_investors_sell, foreign_investors_diff,
                    foreign_self_buy, foreign_self_sell, foreign_self_diff, investment_trust_buy, investment_trust_sell,
                    investment_trust_diff, dealer_total_diff, dealer_self_buy, dealer_self_sell, dealer_self_diff,
                    dealer_hedge_buy, dealer_hedge_sell, dealer_hedge_diff, total_diff
                ))
                print(
                    date, stock_code, stock_name, foreign_investors_buy, foreign_investors_sell, foreign_investors_diff,
                    foreign_self_buy, foreign_self_sell, foreign_self_diff, investment_trust_buy, investment_trust_sell,
                    investment_trust_diff, dealer_total_diff, dealer_self_buy, dealer_self_sell, dealer_self_diff,
                    dealer_hedge_buy, dealer_hedge_sell, dealer_hedge_diff, total_diff
                )

    conn = mysql.connector.connect(
        host="140.131.114.242",
        user="rootii",
        password="!@Aa1234",
        database="113-Intelligent investment"
    )
    cursor = conn.cursor()


    insert_query = """
    INSERT INTO juridical_data (
        date, stock_code, stock_name, foreign_investors_buy, foreign_investors_sell, foreign_investors_diff,
        foreign_self_buy, foreign_self_sell, foreign_self_diff, investment_trust_buy, investment_trust_sell,
        investment_trust_diff, dealer_total_diff, dealer_self_buy, dealer_self_sell, dealer_self_diff,
        dealer_hedge_buy, dealer_hedge_sell, dealer_hedge_diff, total_diff
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(insert_query, data_list)
    conn.commit()

    cursor.close()
    conn.close()

    print("新增日期資料匯入 MySQL 完成")

def crawl_and_insert_funds_holding():

    # 資料庫配置
    db_config = {
        'host': '140.131.114.242',
        'user': 'rootii',
        'password': '!@Aa1234',
        'database': '113-Intelligent investment'
    }

    def fetch_fund_name_data():
        url = "https://mops.twse.com.tw/mops/web/ajax_t78sb04"
        payload = {
            'encodeURIComponent': '1',
            'TYPEK': 'all',
            'step': '1',
            'run': '',
            'firstin': 'true',
            'FUNTYPE': '02',
            'year': '113',
            'season': '02',
            'fund_no': '0'
        }
        response = requests.post(url, data=payload)
        fund_name_data = []

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            no_border_tables = soup.find_all('table', {'class': 'noBorder'})
            has_border_tables = soup.find_all('table', {'class': 'hasBorder'})

            for i, table in enumerate(no_border_tables):
                fund_info = table.find_all('td')
                fund_season = fund_info[0].text.strip()
                fund_name = fund_info[1].text.strip()

                # 對應的 hasBorder 表格
                if i < len(has_border_tables):
                    rows = has_border_tables[i].find_all('tr')[1:]  # 跳過標題行

                    current_category = None
                    for row in rows:
                        th = row.find('th')
                        if th and 'rowspan' in th.attrs:
                            current_category = th.text.strip()
                        cols = row.find_all('td')
                        if len(cols) == 5:
                            stock_code = cols[0].text.strip()
                            stock_name = cols[1].text.strip()
                            stock_ratio = cols[2].text.strip().replace('%', '')
                            industry_type = cols[3].text.strip()
                            industry_ratio = cols[4].text.strip().replace('%', '')

                            stock_ratio = float(stock_ratio)
                            industry_ratio = float(industry_ratio)

                            fund_name_data.append((fund_season, fund_name, current_category, stock_code, stock_name, stock_ratio, industry_type, industry_ratio))

        return fund_name_data

    def fetch_fund_code_data():
        url = "https://mops.twse.com.tw/mops/web/ajax_t51sb11"
        payload = {
            'encodeURIComponent': '1',
            'TYPEK': 'sii',
            'step': '0',
            'run': '',
            'firstin': 'true'
        }
        response = requests.post(url, data=payload)
        fund_code_data = {}

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'hasBorder'})
            rows = table.find_all('tr')[1:]

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    fund_code = cols[0].text.strip()
                    fund_name = cols[1].text.strip()
                    fund_code_data[fund_name] = fund_code

        return fund_code_data

    # 抓取數據
    fund_name_data = fetch_fund_name_data()
    fund_code_data = fetch_fund_code_data()
    print(fund_name_data)
    print(fund_code_data)
    # 合併數據
    merged_data = []
    for row in fund_name_data:
        fund_season, fund_name, category, stock_code, stock_name, stock_ratio, industry_type, industry_ratio = row
        fund_code = fund_code_data.get(fund_name, "N/A")
        merged_data.append((fund_code, fund_name, fund_season, category, stock_code, stock_name, stock_ratio, industry_type, industry_ratio))

    # 連接資料庫並插入數據
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    # 創建表格
    create_table_query = """
    CREATE TABLE IF NOT EXISTS funds_holding (
        fund_code VARCHAR(255),
        fund_name VARCHAR(255),
        fund_season VARCHAR(255),
        category VARCHAR(255),
        stock_code VARCHAR(255),
        stock_name VARCHAR(255),
        stock_ratio FLOAT,
        industry_type VARCHAR(255),
        industry_ratio FLOAT
    )
    """
    cursor.execute(create_table_query)

    cursor.execute("DELETE FROM funds_holding")

    # 插入數據
    insert_query = """
    INSERT INTO funds_holding (
        fund_code, fund_name, fund_season, category, stock_code, stock_name, stock_ratio, industry_type, industry_ratio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, merged_data)
    connection.commit()

    # 關閉連接
    cursor.close()
    connection.close()

    print("funds數據插入成功")

def crawl_and_insert_dividend():
    result = []

    url = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&type=ALLBUT0999'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    if 'none' not in soup.text:
        table = soup.find_all('table')[8]
        columnNames = table.find('thead').find_all('tr')[2].find_all('td')
        columnNames = [elem.getText() for elem in columnNames]
        rowDatas = table.find('tbody').find_all('tr')

        for row in rowDatas:
            code = row.find_all("td")[0].text.strip()
            stock_name = row.find_all("td")[1].text.strip()

            detail_url = f"https://tw.stock.yahoo.com/quote/{code}/dividend"
            detail_response = requests.get(detail_url)
            if detail_response.status_code == 200:
                detail_soup = BeautifulSoup(detail_response.content.decode('utf-8'), "html.parser")
                no_data_msg = detail_soup.find('div', class_="W(100%) H(104px) D(f) Ai(c) Jc(c) Fz(16px) C($c-secondary-text) Fw(b)")
                if no_data_msg and "查無資料" in no_data_msg.text:
                    print(f"No dividend data found for {code} - {stock_name}")
                else:
                    detail_list_items = detail_soup.find('ul', class_="M(0) P(0) List(n)")
                    if detail_list_items:
                        for li_item in detail_list_items.find_all('li'):
                            divs = li_item.find_all('div')
                            if len(divs) >= 7:
                                data = [div.text.strip() for div in divs[2:]]
                                result.append([code, stock_name] + data)
                                print([code, stock_name] + data)
                    else:
                        print(f"No dividend data found for {code} - {stock_name}")


        conn = mysql.connector.connect(
            host="140.131.114.242",
            user="rootii",
            password="!@Aa1234",
            database="113-Intelligent investment"
        )
        cursor = conn.cursor()

        cursor.execute("DELETE FROM dividend")

        for item in result:
            stock_code, stock_name, Distribution_Date, Belong, Cash_Dividend, \
            stock_Dividend, Cash_Yield, Ex_Date_Close, Ex_Dividend_Date, \
            Ex_Right_Date, Cash_Dividend_Date, stock_Dividends_Date, Back_To_Close_Date = item
            
            Cash_Dividend = float(Cash_Dividend) if Cash_Dividend and Cash_Dividend != '-' else 0
            stock_Dividend = float(stock_Dividend) if stock_Dividend and stock_Dividend != '-' else 0
            Cash_Yield = float(Cash_Yield.strip('%')) if Cash_Yield and Cash_Yield != '-' else 0
            Ex_Date_Close = float(Ex_Date_Close.replace(',', '')) if Ex_Date_Close and Ex_Date_Close != '-' else 0
            
            Back_To_Close_Date = int(Back_To_Close_Date) if Back_To_Close_Date and Back_To_Close_Date != '-' else 0
        
            
            sql = """INSERT INTO dividend 
                    (stock_code, stock_name, Distribution_Date, Belong, Cash_Dividend, 
                    stock_Dividend, Cash_Yield, Ex_Date_Close, Ex_Dividend_Date, 
                    Ex_Right_Date, Cash_Dividend_Date, stock_Dividends_Date, Back_To_Close_Date) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            cursor.execute(sql, (stock_code, stock_name, Distribution_Date, Belong, Cash_Dividend, 
                                stock_Dividend, Cash_Yield, Ex_Date_Close, Ex_Dividend_Date, 
                                Ex_Right_Date, Cash_Dividend_Date, stock_Dividends_Date, Back_To_Close_Date))

        conn.commit()
        conn.close()

    else:
        print("Failed")

    print("下載完成")

def crawl_and_insert_funds_info():

    # 資料庫連線設定
    db_config = {
        'host': '140.131.114.242',
        'user': 'rootii',
        'password': '!@Aa1234',
        'database': '113-Intelligent investment'
    }

    # 連接 MySQL 資料庫
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # 建立表格的 SQL 語句
    create_table_query = """
    CREATE TABLE IF NOT EXISTS funds_info (
        id INT AUTO_INCREMENT PRIMARY KEY,
        fund_code VARCHAR(10) NOT NULL,
        fund_name VARCHAR(255) NOT NULL,
        listingDate DATE,
        indexName VARCHAR(255),
        totalAv DECIMAL(15, 2),
        valueYTD DECIMAL(15, 2),
        volumeYTD BIGINT,
        holdersNum INT,
        rorYTD DECIMAL(5, 2),
        issuer VARCHAR(255),
        tradingTax DECIMAL(5, 2),
        transactionFeeRate DECIMAL(5, 2),
        managementFee DECIMAL(5, 2),
        custodyFee DECIMAL(5, 2)
    );
    """
    # 執行建立表格的操作
    cursor.execute(create_table_query)
    connection.commit()
    cursor.execute("DELETE FROM funds_info")


    # 請求 API 獲取資料
    url = 'https://www.twse.com.tw/zh/ETFortune/ajaxProductsResult'
    response = requests.get(url)

    def fetch_with_retry(url, retries=3, delay=2):
        for attempt in range(retries):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response
            except requests.exceptions.RequestException as e:
                print(f"請求錯誤: {e}, 嘗試重試 {attempt+1}/{retries}")
            time.sleep(delay * (attempt + 1))  # 遞增延遲時間
        return None

    # 確認 API 回應是否正確
    if response.status_code == 200:
        try:
            json_data = response.json()
        except requests.exceptions.JSONDecodeError:
            print("無法將回應解析為 JSON。")
            cursor.close()
            connection.close()
            exit()

        etf_list = json_data.get('data', [])

        if isinstance(etf_list, list):
            # 定義 SQL 插入語句
            insert_query = """
            INSERT INTO funds_info (fund_code, fund_name, listingDate, indexName, totalAv, valueYTD, volumeYTD, holdersNum, rorYTD, issuer, tradingTax, transactionFeeRate, managementFee, custodyFee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            batch_size = 5
            for i in range(0, len(etf_list), batch_size):
                batch = etf_list[i:i+batch_size]
                # 從 API 解析的資料寫入資料庫
                for etf in batch:
                    stock_no = etf['stockNo']
                    print(stock_no)
                    # 獲取 ETF 詳細資料
                    detail_url = f'https://www.twse.com.tw/rwd/zh/ETF/productContent?id={stock_no}&response=json'
                    detail_response = fetch_with_retry(detail_url)

                    # 確認回應狀態碼
                    if detail_response.status_code == 200:
                        try:
                            detail_json = detail_response.json()
                        except requests.exceptions.JSONDecodeError:
                            print(f"無法將回應解析為 JSON，股票代號: {stock_no}")
                            continue

                        if detail_json['stat'] == 'ok' and detail_json['tables']:
                            # 取得需要的資料
                            fields = detail_json['tables'][0]['fields']
                            data = detail_json['tables'][0]['data'][0]
                            
                            # 創建一個字典來方便查找
                            detail_dict = dict(zip(fields, data))
                            
                            # 提取所需欄位
                            trading_tax = detail_dict.get("證券交易稅", None)
                            transaction_fee_rate = detail_dict.get("交易手續費費率", None)
                            management_fee = detail_dict.get("管理費", None)
                            custody_fee = detail_dict.get("保管費", None)

                            # 準備插入資料
                            data_to_insert = [
                                etf['stockNo'],  # 股票代號
                                etf['stockName'],  # ETF名稱
                                etf['listingDate'],  # 上市日期
                                etf['indexName'],  # 標的指數
                                etf['totalAv'].replace(',', ''),  # 資產規模(億元)
                                etf['valueYTD'].replace(',', ''),  # 年初至今日均成交值(百萬元)
                                etf['volumeYTD'].replace(',', ''),  # 年初至今日均成交量(股)
                                etf['holders'].replace(',', ''),  # 受益人數(人)
                                etf['rorYTD'],  # 年初至今績效(%)
                                etf['issuer'],   # 發行人
                                trading_tax,  # 證券交易稅
                                transaction_fee_rate,  # 交易手續費費率
                                management_fee,  # 管理費
                                custody_fee  # 保管費
                            ]

                            # 插入資料到資料庫
                            cursor.execute(insert_query, data_to_insert)
                time.sleep(20)

            # 提交變更並關閉連線
            connection.commit()
        else:
            print("API 回傳的 'data' 格式不是列表")

    else:
        print("無法取得API資料")

    # 關閉游標和資料庫連線
    cursor.close()
    connection.close()

    print("資料已成功插入資料庫")

def crawl_and_insert_funds_net_worth():

    # 資料庫連線設定
    db_config = {
        'host': '140.131.114.242',
        'user': 'rootii',
        'password': '!@Aa1234',
        'database': '113-Intelligent investment'
    }

    # 抓取資料
    url = f'https://mis.twse.com.tw/stock/data/all_etf.txt'
    response = requests.get(url)

    try:
        # 確認回應是 JSON 格式
        data = response.json()
    except ValueError as e:
        print("Error: Unable to parse JSON response")
        print("Response content:", response.text)
        exit()

    # 確認資料的主要結構是字典，並檢查 'a1' 是否存在
    if not isinstance(data, dict) or 'a1' not in data:
        print("Error: Unexpected data format. Expected a dictionary with 'a1'.")
        print("Response content:", data)
        exit()

    # 提取 'a1' 中的每個 'msgArray' 並過濾欄位
    filtered_data = []
    for group in data['a1']:
        if 'msgArray' in group:
            for item in group['msgArray']:
                try:
                    filtered_item = {
                        'a': item['a'],  # ETF代碼
                        'b': item['b'],  # ETF名稱
                        'e': float(item['e']),  # 買價
                        'f': float(item['f']),  # 賣價
                        'g': float(item['g']),  # 漲跌幅
                        'h': float(item['h'])   # 昨收價
                    }
                    filtered_data.append(filtered_item)
                except KeyError as e:
                    print(f"Error: Missing key {e} in item {item}")
                    continue
                except ValueError as e:
                    print(f"Error: Invalid data format in item {item} - {e}")
                    continue

    # 插入資料庫
    def insert_data_to_db(data):
        try:
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM funds_net_worth")
            # 定義插入SQL語句
            insert_query = """
                INSERT INTO funds_net_worth (fund_code, fund_name, close_price, net_worth, dp_percent, ytd_net_worth)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            # 插入每一筆資料
            for item in data:
                cursor.execute(insert_query, (
                    item['a'],  # ETF代碼
                    item['b'],  # ETF名稱
                    item['e'],  # close_price
                    item['f'],  # net_worth
                    item['g'],  # dp_percent
                    item['h']   # ytd_net_worth
                ))

            # 提交交易
            connection.commit()
            print("Data inserted successfully")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            connection.close()

    # 執行插入資料的函式
    insert_data_to_db(filtered_data)