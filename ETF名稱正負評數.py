import pymysql

# 数据库配置
db_config = {
    'host': '140.131.114.242',
    'user': 'rootii',
    'password': '!@Aa1234',
    'database': '113-Intelligent investment'
}

# 连接到数据库
connection = pymysql.connect(**db_config)
cursor = connection.cursor()

def update_sentiment_counts():
    # 获取所有的 search_key
    cursor.execute("SELECT search_key FROM news_search_key1")
    search_keys = cursor.fetchall()

    # 遍历每个 search_key
    for search_key_tuple in search_keys:
        search_key = search_key_tuple[0]
        print(search_key)
        # 加上 news_data 表中的 search_key 的单引号
        sanitized_search_key = f"'{search_key.strip('\'')}'"

        print(sanitized_search_key)

        # 获取对应 search_key 的所有 NewsData 的 sentiment
        cursor.execute("SELECT sentiment FROM news_data WHERE search_key = %s", (sanitized_search_key,))
        sentiments = cursor.fetchall()

        # 初始化计数器
        positive_count = 0
        negative_count = 0

        # 遍历所有相关的 NewsData，计算 sentiment
        for sentiment_tuple in sentiments:
            sentiment = sentiment_tuple[0]
            if sentiment is not None:  # 确保 sentiment 不是 None
                if sentiment > 0.3:
                    positive_count += 1
                elif sentiment < -0.3:
                    negative_count += 1

        # 更新 News_search_key1 的 positive 和 negative 字段
        cursor.execute(
            "UPDATE news_search_key1 SET positive = %s, negative = %s WHERE search_key = %s",
            (positive_count, negative_count, search_key)
        )
        print(positive_count)
        connection.commit()

    print("Sentiment counts updated.")

# 调用该函数来更新 sentiment 计数
update_sentiment_counts()

# 关闭连接
cursor.close()
connection.close()
