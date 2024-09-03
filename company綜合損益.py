import requests
import mysql.connector

# 定義API URL
api_url = "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci"

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
CREATE TABLE IF NOT EXISTS company_data_comprehensive_income (
    年度 INT,
    季別 INT,
    stock_code VARCHAR(10),
    stock_name VARCHAR(50),
    營業收入 DECIMAL(20,2),
    營業成本 DECIMAL(20,2),
    營業毛利（毛損） DECIMAL(20,2),
    營業費用 DECIMAL(20,2),
    營業利益（損失） DECIMAL(20,2),
    營業外收入及支出 DECIMAL(20,2),
    稅前淨利（淨損） DECIMAL(20,2),
    所得稅費用（利益） DECIMAL(20,2),
    本期淨利（淨損） DECIMAL(20,2),
    本期綜合損益總額 DECIMAL(20,2),
    基本每股盈餘（元） DECIMAL(10,2)
)
"""
cursor.execute(create_table_query)

# 插入資料的SQL語句
insert_query = """
INSERT INTO company_data_comprehensive_income (
    年度, 季別, stock_code, stock_name, 營業收入, 營業成本, 營業毛利（毛損）, 營業費用, 
    營業利益（損失）, 營業外收入及支出, 稅前淨利（淨損）, 所得稅費用（利益）, 本期淨利（淨損）,
      本期綜合損益總額, 基本每股盈餘（元）
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# 逐行處理並插入資料
for entry in data:
    年度 = entry["年度"]
    季別 = entry["季別"]
    公司代號 = entry["公司代號"]
    公司名稱 = entry["公司名稱"]
    營業收入 = float(entry["營業收入"]) if entry["營業收入"] else 0
    營業成本 = float(entry["營業成本"]) if entry["營業成本"] else 0
    營業毛利毛損 = float(entry["營業毛利（毛損）"]) if entry["營業毛利（毛損）"] else 0
    營業費用 = float(entry["營業費用"]) if entry["營業費用"] else 0
    營業利益損失 = float(entry["營業利益（損失）"]) if entry["營業利益（損失）"] else 0
    營業外收入及支出 = float(entry["營業外收入及支出"]) if entry["營業外收入及支出"] else 0
    稅前淨利淨損 = float(entry["稅前淨利（淨損）"]) if entry["稅前淨利（淨損）"] else 0
    所得稅費用利益 = float(entry["所得稅費用（利益）"]) if entry["所得稅費用（利益）"] else 0
    本期淨利淨損 = float(entry["本期淨利（淨損）"]) if entry["本期淨利（淨損）"] else 0
    本期綜合損益總額 = float(entry["本期綜合損益總額"]) if entry["本期綜合損益總額"] else 0
    基本每股盈餘元 = float(entry["基本每股盈餘（元）"]) if entry["基本每股盈餘（元）"] else 0

    cursor.execute(insert_query, (
        年度, 季別, 公司代號, 公司名稱, 營業收入, 營業成本, 營業毛利毛損, 營業費用, 
        營業利益損失, 營業外收入及支出, 稅前淨利淨損, 所得稅費用利益, 本期淨利淨損, 
        本期綜合損益總額, 基本每股盈餘元
    ))

# 提交變更並關閉資料庫連接
conn.commit()
cursor.close()
conn.close()

print("綜合損益表資料插入完成。")
