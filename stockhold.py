import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import mysql.connector

url = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&type=ALLBUT0999'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

if 'none' not in soup.text:
    table = soup.find_all('table')[8]
    columnNames = table.find('thead').find_all('tr')[2].find_all('td')
    columnNames = [elem.getText() for elem in columnNames]
    rowDatas = table.find('tbody').find_all('tr')

    result = []

    for row in rowDatas:
        code = row.find_all("td")[0].text.strip()
        stock_name = row.find_all("td")[1].text.strip()

        detail_url = f"https://tw.stock.yahoo.com/quote/{code}/holding"
        detail_response = requests.get(detail_url)
        if detail_response.status_code == 200:
            detail_soup = BeautifulSoup(detail_response.content.decode('utf-8'), "html.parser")
            detail_list_items = detail_soup.find_all('ul', class_="Bxz(bb) Bgc($c-light-gray) Bdrs(8px) P(20px)")

            if len(detail_list_items) >= 2:
                detail_list_item = detail_list_items[1]

                headers = ["代號", "股票名稱", "持股票名稱", "持股(%)"]

                list_items = detail_list_item.find_all('li', class_="D(f) Ai(c) Jc(sb) C($c-link-text) Fz(16px) Lh(24px) Pt(8px) Pb(7px) Bdbs(s) Bdbw(1px) Bdbc($bd-primary-divider)")

                for li_item in list_items:
                    divs = li_item.find_all('div', recursive=False)
                    if len(divs) >= 2:
                        stock_holder = divs[0].text.strip()
                        stock_holder = re.sub(r'^\d+\.', '', stock_holder)
                        holding_percentage = divs[1].text.strip()
                        holding_percentage = re.sub(r'%', '', holding_percentage)
                        result.append([code, stock_name, stock_holder, holding_percentage])
                        print([code, stock_name, stock_holder, holding_percentage])

    conn = mysql.connector.connect(
        host="140.131.114.242",
        user="rootii",
        password="!@Aa1234",
        database="113-Intelligent investment"
    )
    cursor = conn.cursor()

    cursor.execute("DELETE FROM stock_hold")

    insert_query = """
    INSERT INTO stock_hold (stock_code, stock_name, stock_holder, percentage)
    VALUES (%s, %s, %s, %s)
    """
    for data in result:
        cursor.execute(insert_query, data)

    conn.commit()
    cursor.close()
    conn.close()

else:
    print("Failed")

print("下載完成")