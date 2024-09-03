import requests
import mysql.connector

# 定義API URL
api_url = "https://openapi.twse.com.tw/v1/opendata/t187ap07_L_ci"

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
CREATE TABLE IF NOT EXISTS company_data_Balance_sheet (
    年度 INT,
    季別 INT,
    stock_code VARCHAR(10),
    stock_name VARCHAR(50),
    流動資產 DECIMAL(20,2),
    非流動資產 DECIMAL(20,2),
    資產總額 DECIMAL(20,2),
    流動負債 DECIMAL(20,2),
    非流動負債 DECIMAL(20,2),
    負債總額 DECIMAL(20,2),
    股本 DECIMAL(20,2),
    資本公積 DECIMAL(20,2),
    保留盈餘 DECIMAL(20,2),
    其他權益 DECIMAL(20,2),
    庫藏股票 DECIMAL(20,2),
    權益總額 DECIMAL(20,2),
    每股參考淨值 DECIMAL(10,2)
)
"""
cursor.execute(create_table_query)

# 插入資料的SQL語句
insert_query = """
INSERT INTO company_data_Balance_sheet (
    年度, 季別, stock_code, stock_name, 流動資產, 非流動資產, 資產總額, 流動負債, 
    非流動負債, 負債總額, 股本, 資本公積, 保留盈餘, 其他權益, 庫藏股票, 
    權益總額, 每股參考淨值
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# 逐行處理並插入資料
for entry in data:
    年度 = entry["年度"]
    季別 = entry["季別"]
    公司代號 = entry["公司代號"]
    公司名稱 = entry["公司名稱"]
    流動資產 = float(entry["流動資產"]) if entry["流動資產"] else 0
    非流動資產 = float(entry["非流動資產"]) if entry["非流動資產"] else 0
    資產總額 = float(entry["資產總額"]) if entry["資產總額"] else 0
    流動負債 = float(entry["流動負債"]) if entry["流動負債"] else 0
    非流動負債 = float(entry["非流動負債"]) if entry["非流動負債"] else 0
    負債總額 = float(entry["負債總額"]) if entry["負債總額"] else 0
    股本 = float(entry["股本"]) if entry["股本"] else 0
    資本公積 = float(entry["資本公積"]) if entry["資本公積"] else 0
    保留盈餘 = float(entry["保留盈餘"]) if entry["保留盈餘"] else 0
    其他權益 = float(entry["其他權益"]) if entry["其他權益"] else 0
    庫藏股票 = float(entry["庫藏股票"]) if entry["庫藏股票"] else 0
    權益總額 = float(entry["權益總額"]) if entry["權益總額"] else 0
    每股參考淨值 = float(entry["每股參考淨值"]) if entry["每股參考淨值"] else 0

    cursor.execute(insert_query, (
        年度, 季別, 公司代號, 公司名稱, 流動資產, 非流動資產, 資產總額, 流動負債, 
        非流動負債, 負債總額, 股本, 資本公積, 保留盈餘, 其他權益, 庫藏股票, 
        權益總額, 每股參考淨值
    ))

# 提交變更並關閉資料庫連接
conn.commit()
cursor.close()
conn.close()

print("資產負債表資料插入完成。")
