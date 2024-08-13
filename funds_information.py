import requests
import mysql.connector
import time

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
