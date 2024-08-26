import requests
import pymysql
from bs4 import BeautifulSoup

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
                        stock_ratio = cols[2].text.strip('%')
                        industry_type = cols[3].text.strip()
                        industry_ratio = cols[4].text.strip('%')
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
