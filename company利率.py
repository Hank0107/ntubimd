import requests
import mysql.connector

# 定義API URL
api_url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"

# 取得API資料
response = requests.get(api_url)
data = response.json()

# 連接到資料庫
db_config = {
    'host': '140.131.114.242',
    'user': 'rootii',
    'password': '!@Aa1234',
    'database': '113-Intelligent investment'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# 建立資料表
create_table_query = """
CREATE TABLE IF NOT EXISTS company_ratio (
    stock_code VARCHAR(10),
    stock_name VARCHAR(50),
    PEratio DECIMAL(20,2),
    PBratio DECIMAL(20,2),
    DividendYield DECIMAL(20,2)
)
"""
cursor.execute(create_table_query)

# 插入資料的SQL語句
insert_query = """
INSERT INTO company_ratio (
    stock_code, stock_name, PEratio, PBratio, DividendYield
) VALUES (%s, %s, %s, %s, %s)
"""

# 逐行處理並插入資料
for entry in data:
    Code = entry["Code"]
    Name = entry["Name"]
    PEratio = float(entry["PEratio"]) if entry["PEratio"] else 0
    PBratio = float(entry["PBratio"]) if entry["PBratio"] else 0
    DividendYield = float(entry["DividendYield"]) if entry["DividendYield"] else 0

    cursor.execute(insert_query, (
        Code, Name, PEratio, PBratio, DividendYield
    ))

# 提交變更並關閉資料庫連接
conn.commit()
cursor.close()
conn.close()

print("利率資料插入完成。")
