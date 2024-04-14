# 載入套件
import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
import json
import datetime

# 參數設定
# 要下載的股ETF新聞關鍵字清單(2330台積電)
searchList = ['0050']
# 下載起始日10天內的新聞
nearStartDate = (datetime.date.today() + datetime.timedelta(days=-10)).strftime('%Y-%m-%d')

# 整理Google新聞資料用
def arrangeGoogleNews(elem):
    return ([elem.find('title').getText(),
             elem.find('link').getText(),
             elem.find('pubDate').getText(),
             BeautifulSoup(elem.find('description').getText(), 'html.parser').find('a').getText(),
             elem.find('source').getText()])

# 擷取各家新聞網站新聞函數
def beautifulSoupNews(url):

    # 設定hearers
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/87.0.4280.141 Safari/537.36'}

    # 取得Google跳轉頁面的新聞連結
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    newsUrl = soup.find_all('c-wiz', class_='jtabgf')[0].getText()
    newsUrl = newsUrl.replace('Opening ', '')

    # 取得該篇新聞連結內容
    response = requests.get(newsUrl, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 判斷url網域做對應文章擷取
    domain = re.findall('https://[^/]*', newsUrl)[0].replace('https://', '')

    if domain == 'udn.com':

        # 聯合新聞網
        item = soup.find_all('section', class_='article-content__editor')
        if item:
          item = item[0].find_all('p')
          content = [elem.getText() for elem in item]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ')
        else:
          # 找不到符合條件的元素
          return None, None

    elif domain == 'ec.ltn.com.tw':

        # 自由財經
        item = soup.find_all('div', class_='text')[0].find_all('p', class_='')
        if item:
          item = item[0].find_all('p', class_='')
          content = [elem.getText() for elem in item]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' '). \
              replace('一手掌握經濟脈動', '').replace('點我訂閱自由財經Youtube頻道', '')
        else:
          # 找不到符合條件的元素
          return None, None

    elif domain in ['tw.stock.yahoo.com', 'tw.news.yahoo.com']:

        # Yahoo奇摩股市
        item = soup.find_all('div', class_='caas-body')
        if item:
          item = item[0].find_all('p')
          content = [elem.getText() for elem in item]
          del_text = soup.find_all('div', class_='caas-body')[0].find_all('a')
          del_text = [elem.getText() for elem in del_text]
          content = [elem for elem in content if elem not in del_text]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' ')
        else:
          # 找不到符合條件的元素
          return None, None

    elif domain == 'money.udn.com':

        # 經濟日報
        item = soup.find_all('section', id='article_body')
        if item:
          item = item[0].find_all('p')
          content = [elem.getText() for elem in item]
          content = [elem for elem in content]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ')
        else:
          # 找不到符合條件的元素
          return None, None

    elif domain == 'www.chinatimes.com':

        # 中時新聞網
        item = soup.find_all('div', class_='article-body')
        if item:
          item = item[0].find_all('p')
          content = [elem.getText() for elem in item]
          content = [elem for elem in content]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ')
        else:
          # 找不到符合條件的元素
          return None, None


    elif domain == 'ctee.com.tw':

        # 工商時報
        item = soup.find_all('div', class_='entry-content clearfix single-post-content')
        if item:
          item = item[0].find_all('p')
          content = [elem.getText() for elem in item]
          content = [elem for elem in content]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ')
        else:
          # 找不到符合條件的元素
          return None, None


    elif domain == 'finance.ettoday.net':

        # ETtoday
        item = soup.find_all('div', itemprop='articleBody')
        if item:
          item = item[0].find_all('p')
          content = [elem.getText() for elem in item]
          content = [elem for elem in content]
          content = ''.join(content)
          content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' ')
        else:
          # 找不到符合條件的元素
          return None, None

    elif domain == 'fnc.ebc.net.tw':

        # EBC東森財經新聞
        content = str(soup.find_all('script')[-2]).split('ReactDOM.render(React.createElement(')[1]
        content = content.split(',')[1].replace('{"content":"', '').replace('"})', '')
        content = re.sub(u'\\\\u003[a-z]+', '', content)
        content = content.replace('/p', ' ').replace('\\n', '')
        if content:
            return newsUrl, content
        else:
          # 找不到符合條件的元素
          return None, None

    else:

        # 未知domain
        content = 'unknow domain'

    return newsUrl, content

# 迴圈下載股票清單的Google新聞資料
stockNews = pd.DataFrame()
for iSearch in range(len(searchList)):

    print('目前正在搜尋股票: ' + searchList[iSearch] +
          ' 在Google的新聞清單  進度: ' + str(iSearch + 1) + ' / ' + str(len(searchList)))

    # 建立搜尋網址
    url = 'https://news.google.com/news/rss/search/section/q/' + \
          searchList[iSearch] + '/?hl=zh-tw&gl=TW&ned=zh-tw_tw'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'xml')
    item = soup.find_all('item')
    rows = [arrangeGoogleNews(elem) for elem in item]

    # 組成pandas
    df = pd.DataFrame(data=rows, columns=['title', 'link', 'pub_date', 'description', 'source'])
    # 新增時間戳記欄位
    df.insert(0, 'search_time', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), True)
    # 新增搜尋字串
    df.insert(1, 'search_key', searchList[iSearch], True)
    # 篩選最近的新聞
    df['pub_date'] = df['pub_date'].astype('datetime64[ns]')
    df = df[df['pub_date'] >= nearStartDate]
    # 按發布時間排序
    df = df.sort_values(['pub_date']).reset_index(drop=True)

    # 迴圈爬取新聞連結與內容
    newsUrls = list()
    contents = list()
    for iLink in range(len(df['link'])):

        print('目前正在下載: ' + searchList[iSearch] +
              ' 各家新聞  進度: ' + str(iLink + 1) + ' / ' + str(len(df['link'])))

        newsUrl, content = beautifulSoupNews(url=df['link'][iLink])
        if newsUrl is not None and content is not None:
            newsUrls.append(newsUrl)
            contents.append(content)
        else:
            # 如果無法獲取新聞連結和內容，將 None 添加到列表中以匹配 DataFrame 的行數
            newsUrls.append(None)
            contents.append(None)
        time.sleep(3)

    # 新增新聞連結與內容欄位
    df['newsUrl'] = newsUrls
    df['content'] = contents


    # 儲存資料
    stockNews = pd.concat([stockNews, df])

# 儲存資料
output_path = 'C:/Users/pc/Desktop/大學專題/新聞Data.csv'
try:
    stockNews.to_csv(output_path, index=False)
    print("資料已成功寫入檔案:", output_path)
except Exception as e:
    print("寫入檔案時發生錯誤:", e)