import pymysql
from snownlp import SnowNLP

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

# 抓取content数据
cursor.execute("SELECT id, cleaned_message FROM ptt_data")
rows = cursor.fetchall()

# 遍历每条数据，进行情绪分析，并更新sentiment字段
for row in rows:
    content_id = row[0]
    content_text = row[1]
    
    # 使用SnowNLP进行情绪分析
    s = SnowNLP(content_text)
    sentiment_score = s.sentiments  # 输出0到1之间的情感得分，接近1表示正面情感

    # 将0-1的得分转换为-1到1的范围
    sentiment = (sentiment_score * 2) - 1  # 0变为-1，1变为1
    
    # 更新数据库
    cursor.execute("UPDATE ptt_data SET sentiment = %s WHERE id = %s", (sentiment, content_id))
    connection.commit()

# 关闭连接
cursor.close()
connection.close()

print("情绪分析完成并更新到数据库。")
