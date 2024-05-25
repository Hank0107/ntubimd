import requests
from bs4 import BeautifulSoup
import mysql.connector
import datetime


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
    print(data_list)

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