# 載入套件
import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
import json
import datetime
import AutoSummary as ausu

# 參數設定
# 要下載的股ETF新聞關鍵字清單(2330台積電)
searchList = ['ETF']
# 下載起始日10天內的新聞
nearStartDate = (datetime.date.today() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

# 整理Google新聞資料用
def arrangeGoogleNews(elem):
    pub_date = datetime.datetime.strptime(elem.find('pubDate').getText(), "%a, %d %b %Y %H:%M:%S %Z")
    return ([elem.find('title').getText(),
             elem.find('link').getText(),
             pub_date.strftime('%Y-%m-%d %H:%M:%S'),  # 格式化日期時間字串
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
        item1 = soup.find_all('figure', class_='article-content__cover')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="https://lh3.googleusercontent.com/T-WDXxdXrACC2u_UMcAmcgOCbEHYanszeW2wN1fEt3hwy1KVc-T7S0kMBqwEqIrwWYeIhpLs25Iso9RI_ZY=-s56-p-rw"
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://lh3.googleusercontent.com/T-WDXxdXrACC2u_UMcAmcgOCbEHYanszeW2wN1fEt3hwy1KVc-T7S0kMBqwEqIrwWYeIhpLs25Iso9RI_ZY=-s56-p-rw"

    elif domain == 'ec.ltn.com.tw':

        # 自由財經
        item = soup.find_all('div', class_='text')[0].find_all('p', class_='')
        item1 = soup.find_all('a', class_='image-popup-vertical-fit')
        if item:
            item = item[0].find_all('p', class_='')
            content = [elem.getText() for elem in item]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' '). \
                replace('一手掌握經濟脈動', '').replace('點我訂閱自由財經Youtube頻道', '')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="https://encrypted-tbn0.gstatic.com/faviconV2?url=http://ec.ltn.com.tw&client=NEWS_360&size=96&type=FAVICON&fallback_opts=TYPE,SIZE,URL"
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://encrypted-tbn0.gstatic.com/faviconV2?url=http://ec.ltn.com.tw&client=NEWS_360&size=96&type=FAVICON&fallback_opts=TYPE,SIZE,URL"

    elif domain in ['tw.stock.yahoo.com', 'tw.news.yahoo.com']:

        # Yahoo奇摩股市
        item = soup.find_all('div', class_='caas-body')
        item1 = soup.find_all('div', class_='caas-img-container')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            del_text = soup.find_all('div', class_='caas-body')[0].find_all('a')
            del_text = [elem.getText() for elem in del_text]
            content = [elem for elem in content if elem not in del_text]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="https://encrypted-tbn3.gstatic.com/faviconV2?url=http://tw.stock.yahoo.com&client=NEWS_360&size=96&type=FAVICON&fallback_opts=TYPE,SIZE,URL"
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://encrypted-tbn3.gstatic.com/faviconV2?url=http://tw.stock.yahoo.com&client=NEWS_360&size=96&type=FAVICON&fallback_opts=TYPE,SIZE,URL"

    elif domain == 'money.udn.com':

        # 經濟日報
        item = soup.find_all('section', id='article_body')
        item1 = soup.find_all('figure', class_='article-image')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            content = [elem for elem in content]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcRahA2YTqpp_5Uo3BsFoIbB84ZtS8AKg-CQojlVpCy7ydZLDun-I04pX9LPfdqYG1a3qGTXcund3sduqfO83mGqF2QT-u6XMYc5D9XbTJJk4z_L"         
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcRahA2YTqpp_5Uo3BsFoIbB84ZtS8AKg-CQojlVpCy7ydZLDun-I04pX9LPfdqYG1a3qGTXcund3sduqfO83mGqF2QT-u6XMYc5D9XbTJJk4z_L"

    elif domain == 'www.chinatimes.com':

        # 中時新聞網
        item = soup.find_all('div', class_='article-body')
        item = soup.find_all('div', class_='photo-container')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            content = [elem for elem in content]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcQHrhT2vHPSIRFDsmDeIIjd3HaqakkoYyr-fc9cGyBhjAB5g_KuSJGLrvYKtwpZbBZxQGPwrxo3ApzoGMhus24"
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcQHrhT2vHPSIRFDsmDeIIjd3HaqakkoYyr-fc9cGyBhjAB5g_KuSJGLrvYKtwpZbBZxQGPwrxo3ApzoGMhus24"


    elif domain == 'ctee.com.tw':

        # 工商時報
        item = soup.find_all('div', class_='article-wrap')
        item1 = soup.find_all('figure', class_='picture--article')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            content = [elem for elem in content]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('a')
            if img_tags:
                img = img_tags[0].get('href')
            else:
                img="https://lh3.googleusercontent.com/FVqGBOHKOygWnChrQJGDQ0YZ7sXZBYbrIECNqhmSRue6_9fSZsdNSJJOwfvGNAeyyBotgmqnU7WjkSqfig=-s56-rw"
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://lh3.googleusercontent.com/FVqGBOHKOygWnChrQJGDQ0YZ7sXZBYbrIECNqhmSRue6_9fSZsdNSJJOwfvGNAeyyBotgmqnU7WjkSqfig=-s56-rw"
        
        
    elif domain == 'news.cnyes.com':

        # 鉅亨網
        item = soup.find_all('main', id='article-container')
        item1 = soup.find_all('div', class_='iirgi4a')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            content = [elem for elem in content]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item1[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="data:image/png;base64,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"
        else:
            # 找不到符合條件的元素
            return newsUrl, "unknow domain", "data:image/png;base64,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"



    elif domain == 'finance.ettoday.net':

        # ETtoday
        item = soup.find_all('div', itemprop='articleBody')
        if item:
            item = item[0].find_all('p')
            content = [elem.getText() for elem in item]
            content = [elem for elem in content]
            content = ''.join(content)
            content = content.replace('\r', ' ').replace('\n', ' ').replace(u'\xa0', ' ')
            # 新增抓取第一個 img 的 src 屬性
            img_tags = item[0].find_all('img')
            if img_tags:
                img = img_tags[0].get('src')
            else:
                img="https://lh3.googleusercontent.com/sUgEvUYXBFjj7OQ_lvrRQnRmpM6NWGb0guQhFlnUtOeoYNRXSR6W0hHEhA4d8Jjgy5YW6xM5o1Zerug0xPQ=-s56-p-rw"
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://lh3.googleusercontent.com/sUgEvUYXBFjj7OQ_lvrRQnRmpM6NWGb0guQhFlnUtOeoYNRXSR6W0hHEhA4d8Jjgy5YW6xM5o1Zerug0xPQ=-s56-p-rw"

    elif domain == 'fnc.ebc.net.tw':

        # EBC東森財經新聞
        item1 = soup.find_all('div', class_='img')
        content = str(soup.find_all('script')[-2]).split('ReactDOM.render(React.createElement(')[1]
        content = content.split(',')[1].replace('{"content":"', '').replace('"})', '')
        content = re.sub(u'\\\\u003[a-z]+', '', content)
        content = content.replace('/p', ' ').replace('\\n', '')
        # 新增抓取第一個 img 的 src 屬性
        img_tags = item1[0].find_all('img')
        if img_tags:
            img = img_tags[0].get('src')
        else:
            img="https://lh3.googleusercontent.com/dTAgaNAPgC9ix6K6z2Op2oWDh2OZvpBgfI3145T-z6DsdS6O-84ar401IbQOs2J3nz1l3tG83huGysRC1xg=-s56-p-rw"
        if content:
            return newsUrl, content,img
        else:
          # 找不到符合條件的元素
          return newsUrl, "unknow domain", "https://lh3.googleusercontent.com/dTAgaNAPgC9ix6K6z2Op2oWDh2OZvpBgfI3145T-z6DsdS6O-84ar401IbQOs2J3nz1l3tG83huGysRC1xg=-s56-p-rw"

    else:

        # 未知domain
        content = 'unknow domain'
        img = 'unknow domain'

    return newsUrl, content, img

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
    summars = list()
    imgs = list()
    for iLink in range(len(df['link'])):

        print('目前正在下載: ' + searchList[iSearch] +
              ' 各家新聞  進度: ' + str(iLink + 1) + ' / ' + str(len(df['link'])))

        newsUrl, content, img = beautifulSoupNews(url=df['link'][iLink])
        if content is not "unknow domain":
            newsUrls.append(newsUrl)
            contents.append(content)
            imgs.append(img)

            # 使用摘要程式進行摘要
            with open('dictionary/stopWord_summar.txt', 'r', encoding='utf8') as f:  # 停用詞庫
                stops = [line.strip() for line in f.readlines()]

            sentences, indexs = ausu.split_sentence(content)  # 按標點分割句子
            tfidf = ausu.get_tfidf_matrix(sentences, stops)  # 移除停用詞並轉換為矩陣
            word_weight = ausu.get_sentence_with_words_weight(tfidf)  # 計算句子關鍵詞權重
            posi_weight = ausu.get_sentence_with_position_weight(sentences)  # 計算位置權重
            scores = ausu.get_similarity_weight(tfidf)  # 計算相似度權重
            sort_weight = ausu.ranking_base_on_weigth(word_weight, posi_weight, scores, feature_weight=[1, 1, 1])  # 按句子權重排序
            summar = ausu.get_summarization(indexs, sort_weight, topK_ratio=0.1)  # 取得摘要
            summars.append(summar)
        else:
            # 如果無法獲取新聞連結和內容，將 None 添加到列表中以匹配 DataFrame 的行數
            newsUrls.append(newsUrl)
            contents.append(None)
            summars.append(None)
            imgs.append(img)
        time.sleep(3)

    # 新增新聞連結與內容欄位
    df['newsUrl'] = newsUrls
    df['content'] = contents
    df['summar'] = summars
    df['image_url'] = imgs

    # 儲存資料
    stockNews = pd.concat([stockNews, df])

# 儲存資料
output_path = 'C:/Users/pc/Desktop/大學專題/新聞Data.csv'
try:
    stockNews.to_csv(output_path, index=False)
    print("資料已成功寫入檔案:", output_path)
except Exception as e:
    print("寫入檔案時發生錯誤:", e)

import pymysql

# 資料庫連接資訊
host = '140.131.114.242'
user = 'rootii'
password = '!@Aa1234'
database = '113-Intelligent investment'

# 建立資料庫連接
connection = pymysql.connect(host=host,
                             user=user,
                             password=password,
                             database=database,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

try:
    with connection.cursor() as cursor:
        # 將 DataFrame 中的每一行插入到資料庫中
        for index, row in stockNews.iterrows():
            # 建立 SQL 插入語句
            sql = "INSERT INTO news_data (search_time, search_key, title, link, pub_date, description, source, newsUrl, content, summar, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            # 根據 DataFrame 中的資料填入參數
            cursor.execute(sql, (row['search_time'], row['search_key'], row['title'], row['link'], row['pub_date'], row['description'], row['source'], row['newsUrl'], row['content'], row['summar'], row['image_url'],))
        # 提交事務
        connection.commit()
        print("資料已成功插入資料庫")
finally:
    # 無論如何，最後都要關閉資料庫連接
    connection.close()
