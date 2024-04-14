import jieba
import pymysql
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from wordcloud import WordCloud

jieba.load_userdict(r'C:/Users/pc/Desktop/大學專題/dict.txt.big') 

# 連接 MySQL 資料庫
connection = pymysql.connect(
    host='140.131.114.242',
    user='rootii',
    password='!@Aa1234',
    database='113-Intelligent investment',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 讀取資料庫中的表格資料
# 使用 pymysql 庫進行讀取
try:
    with connection.cursor() as cursor:
        # SQL 查詢語句
        sql = 'SELECT * FROM news_data'
        # 執行 SQL 查詢
        cursor.execute(sql)
        # 獲取所有結果
        result = cursor.fetchall()
        # 將結果轉換為 DataFrame
        df = pd.DataFrame(result)
finally:
    # 關閉資料庫連接
    connection.close()

# 合併所有新聞內容
all_content = ' '.join(df['content'].dropna())

# 移除不需要的字符
all_content = all_content.replace('[^\w\s]','').replace('／',"").replace('《','').replace('》','').replace('，','').replace('。','').replace('「','').replace('」','').replace('（','').replace('）','').replace('！','').replace('？','').replace('、','').replace('▲','').replace('…','').replace('：','')
print(all_content)

# 設定停用詞
stopwords = {}.fromkeys(["也","但","來","個","再","的","和","是","有","更","會","可能","有何","從","對","就", '\n','越','為','這種','多','越來',' '])

# 使用精確模式進行斷詞
words = jieba.cut(all_content, cut_all=False)

# 剔除停用詞
filtered_words = [word for word in words if word not in stopwords]

# 計算詞頻
word_freq = {}
for word in filtered_words:
    if word in word_freq:
        word_freq[word] += 1
    else:
        word_freq[word] = 1

# 將詞頻結果轉換為 DataFrame
word_freq_df = pd.DataFrame.from_dict(word_freq, orient='index', columns=['詞頻'])
# 依詞頻降序排序
word_freq_df = word_freq_df.sort_values(by=['詞頻'], ascending=False)

# 顯示詞頻 DataFrame
print(word_freq_df)

# 生成文字雲
wc = WordCloud(font_path="C:/Users/pc/Desktop/大學專題/MSJHBD.TTC",
               background_color="white",
               max_words=2000,
               stopwords=stopwords)

# 使用字典中的詞頻產生文字雲
wc.generate_from_frequencies(word_freq)

# 顯示文字雲
plt.imshow(wc)
plt.axis("off")
plt.show()
