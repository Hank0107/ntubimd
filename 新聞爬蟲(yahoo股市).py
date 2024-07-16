import jieba.analyse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import pymysql
from datetime import datetime
from snownlp import SnowNLP  # 導入情緒分析模組
import AutoSummary as ausu  # 導入摘要模組

# 資料庫連接資訊
db_config = {
    'host': '140.131.114.242',
    'user': 'rootii',
    'password': '!@Aa1234',
    'database': '113-Intelligent investment',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 建立資料庫連接
connection = pymysql.connect(**db_config)
cursor = connection.cursor()

# 初始化 Selenium 驅動
driver = webdriver.Chrome()
driver.get('https://tw.stock.yahoo.com/tw-market')
time.sleep(2)  # 等待網頁完全加載

# 模擬滾動加載更多內容
SCROLL_PAUSE_TIME = 3  # 滾動後等待加載的時間
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight")
    print(new_height)
    print(last_height)
    if new_height == last_height:
        break
    last_height = new_height

# 使用 BeautifulSoup 解析網頁內容
soup = BeautifulSoup(driver.page_source, 'lxml')

# 初始化一個列表來存儲新聞連結
yahoo_news = []

# 找到所有的新聞鏈接
for each_item in soup.find_all("h3", class_="Mt(0) Mb(8px)"):
    a_tag = each_item.find("a")
    if a_tag:
        yahoo_url = a_tag.get('href')
        if yahoo_url in yahoo_url:
            yahoo_news.append(yahoo_url)

# 關閉 Selenium 驅動
driver.quit()

# 讀取兩個不同的金融相關關鍵字白名單
def load_financial_terms(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        financial_terms = set([line.strip() for line in f])
    return financial_terms

financial_terms = load_financial_terms('C:/Users/ntubimd/website/news/123/ETF關鍵字/financial_terms.txt')
financial_terms1 = load_financial_terms('C:/Users/ntubimd/website/news/123/ETF關鍵字/financial_terms1.txt')

# 檢查新聞內容是否包含白名單關鍵字
def contains_keywords(content, keywords):
    matched_keywords = [keyword for keyword in keywords if keyword in content]
    return matched_keywords

# 更新或插入關鍵字進資料表 news_search_key
def update_or_insert_search_key(search_key, sentiment):
    cursor.execute("SELECT * FROM news_search_key WHERE search_key = %s", (search_key,))
    result = cursor.fetchone()
    
    if result:
        if sentiment > 0.3:
            cursor.execute("UPDATE news_search_key SET positive = positive + 1 WHERE search_key = %s", (search_key,))
        elif sentiment < -0.3:
            cursor.execute("UPDATE news_search_key SET negative = negative + 1 WHERE search_key = %s", (search_key,))
    else:
        positive = 1 if sentiment > 0.3 else 0
        negative = 1 if sentiment < -0.3 else 0
        cursor.execute(
            "INSERT INTO news_search_key (search_key, positive, negative) VALUES (%s, %s, %s)",
            (search_key, positive, negative)
        )
    connection.commit()

# 更新或插入關鍵字進資料表 news_search_key1
def update_or_insert_search_key1(search_key, sentiment):
    cursor.execute("SELECT * FROM news_search_key WHERE search_key1 = %s", (search_key,))
    result = cursor.fetchone()

    if result:
        if sentiment > 0.3:
            cursor.execute("UPDATE news_search_key SET positive = positive + 1 WHERE search_key1 = %s", (search_key,))
        elif sentiment < -0.3:
            cursor.execute("UPDATE news_search_key SET negative = negative + 1 WHERE search_key1 = %s", (search_key,))
    else:
        positive = 1 if sentiment > 0.3 else 0
        negative = 1 if sentiment < -0.3 else 0
        cursor.execute(
            "INSERT INTO news_search_key (search_key1, positive, negative) VALUES (%s, %s, %s)",
            (search_key, positive, negative)
        )
    connection.commit()

# 修改爬取新聞數據的邏輯
for yahoo_all in yahoo_news:
    cursor.execute("SELECT COUNT(*) FROM news_data WHERE link = %s", (yahoo_all,))
    result = cursor.fetchone()

    if result['COUNT(*)'] > 0:
        print(f"新聞連結已存在，跳過: {yahoo_all}")
        continue

    news = requests.get(yahoo_all)
    single_news = BeautifulSoup(news.text, 'lxml')

    try:
        title = single_news.find('h1').text.strip()
        pub_date = single_news.find('time').text.strip()
        content = single_news.find('div', class_='caas-body').text.strip()
        search_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        source = 'Yahoo新聞'
        image_url = "https://play-lh.googleusercontent.com/d3IPmnFpCXdBM-wmFf9QfHGnCdu3rtq2PiLMQUsVAgsqf3B8xc5ulO86q8HZ5uf4sMc=w240-h480-rw"

        # 使用第一個白名單篩選
        matched_keywords1 = contains_keywords(content, financial_terms)

        # 使用第二個白名單篩選
        matched_keywords2 = contains_keywords(content, financial_terms1)

        # 合併兩個白名單中的關鍵字
        combined_keywords = ','.join(set(matched_keywords1 + matched_keywords2))

        # 生成摘要
        with open('C:/Users/ntubimd/website/news/123/dictionary/stopWord_summar.txt', 'r', encoding='utf8') as f:
            stops = [line.strip() for line in f.readlines()]

        sentences, indexs = ausu.split_sentence(content)
        tfidf = ausu.get_tfidf_matrix(sentences, stops)
        word_weight = ausu.get_sentence_with_words_weight(tfidf)
        posi_weight = ausu.get_sentence_with_position_weight(sentences)
        scores = ausu.get_similarity_weight(tfidf)
        sort_weight = ausu.ranking_base_on_weigth(word_weight, posi_weight, scores, feature_weight=[1, 1, 1])
        summar = ausu.get_summarization(indexs, sort_weight, topK_ratio=0.1)

        # 情緒分析
        s = SnowNLP(content)
        sentiment_score = s.sentiments
        sentiment = (sentiment_score * 2) - 1

        # 更新或插入關鍵字到對應資料表
        if matched_keywords1:
            for kw in matched_keywords1:
                update_or_insert_search_key(kw, sentiment)

        if matched_keywords2:
            for kw in matched_keywords2:
                update_or_insert_search_key1(kw, sentiment)

        # 將新聞插入資料庫，包括合併後的 search_key
        sql = """
        INSERT INTO news_data (search_time, title, link, pub_date, source, content, search_key, summar, image_url, sentiment)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (search_time, title, yahoo_all, pub_date, source, content, combined_keywords, summar, image_url, sentiment))
        connection.commit()
        print(f"成功插入新聞: {title}，摘要: {summar}，情緒得分: {sentiment}")

    except AttributeError:
        print(f"跳過新聞: {yahoo_all}")
        
# 關閉資料庫連接
cursor.close()
connection.close()

print("爬蟲完成並插入資料庫。")
