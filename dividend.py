import requests
from bs4 import BeautifulSoup
import mysql.connector

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