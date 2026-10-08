import collections
import json
import jieba
import pandas as pd
import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 設定網頁標題
st.set_page_config(
    page_title="華語文教材微型文字探勘儀表板", layout="wide"
)

st.title("📚 華語文教材內容分析儀表板 (Mini-Voyant)")
st.write(
    "上傳您的教材 JSON 檔案，系統將自動進行繁體中文斷詞、排除功能詞，並即時產出"
    "文字雲與詞頻統計表！"
)

# 1. 側邊欄：功能設定與上傳
st.sidebar.header("1. 資料與參數設定")
uploaded_file = st.sidebar.file_uploader(
    "上傳 JSON 語料檔案", type=["json"]
)

# 自訂功能詞（停用詞）排除清單
default_stopwords = (
    "的,了,和,是,就,都,而,及,與,著,或,一個,沒有,我們,你們,他們,你,我,it,他,"
    "這,那,在,有,個,要,去,來,說,吧,嗎,呢,啊,呀,哦,啦,吧,把,被,讓,向,從"
)
stopwords_input = st.sidebar.text_area(
    "排除功能詞設定 (以逗號分隔)", default_stopwords
)
stopwords = set([w.strip() for w in stopwords_input.split(",") if w.strip()])

# 載入繁體中文自訂詞庫（選填：如果有特定華語詞彙不想被切開，可在此加入）
# jieba.load_userdict("my_dict.txt")


if uploaded_file is not None:
  # 讀取 JSON
  try:
    data = json.load(uploaded_file)
    st.sidebar.success("檔案載入成功！")
  except Exception as e:
    st.sidebar.error(f"JSON 格式錯誤: {e}")
    st.stop()

  # 選擇要分析的冊別
  books = list(set([item.get("冊", "未分類") for item in data]))
  selected_book = st.sidebar.selectbox("選擇要分析的冊別", sorted(books))

  # 過濾該冊的文本
  corpus_text = ""
  for item in data:
    if item.get("冊") == selected_book:
      # 串接該課的所有對話與文章
      d1 = item.get("對話1", "")
      d2 = item.get("對話2", "")
      a1 = item.get("文章1", "")
      a2 = item.get("文章2", "")
      corpus_text += f" {d1} {d2} {a1} {a2}"

  if corpus_text.strip():
    # 2. jieba 斷詞與清理
    words = jieba.cut(corpus_text)
    filtered_words = [
        w.strip()
        for w in words
        if w.strip()
        and w.strip() not in stopwords
        and len(w.strip()) > 1  # 排除單字，保留實詞
    ]

    # 計算詞頻
    word_counts = collections.Counter(filtered_words)
    df_freq = pd.DataFrame(
        word_counts.most_common(50), columns=["詞彙", "出現頻次"]
    )

    # 3. 畫面呈現
    col1, col2 = st.column_config(2) if hasattr(st, "column_config") else (
        st.columns(2)
    )
    # 為了相容性，改用標準 st.columns(2)
    col1, col2 = st.columns(2)

    with col1:
      st.subheader(f"📊 {selected_book} - 詞頻排行榜 Top 50")
      st.dataframe(df_freq, height=450, use_container_width=True)

    with col2:
      st.subheader("☁️ 文字雲視覺化 (Word Cloud)")
      # 產生文字雲
      # 注意：雲端部署時需確保有安裝中文字型，或使用內建設定
      try:
        # 假設系統中備有支援中文的字型路徑（Windows 可用 C:/Windows/Fonts/msjh.ttc）
        # 雲端 Linux 環境通常需指定字型，或使用預設
        font_path = (
            "C:/Windows/Fonts/msjh.ttc"  # 本地測試路徑，上雲端時可換成專案內的字型檔
        )
        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=600,
            background_color="white",
            max_words=100,
        ).generate_from_frequencies(word_counts)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
      except Exception as e:
        st.warning(
            f"文字雲繪製提示（若在雲端未設定中文字型可能會跳過）：{e}"
        )
        # 退而求其次，直接用長條圖呈現
        st.bar_chart(df_freq.set_index("詞彙").head(20))

  else:
    st.warning("該冊內容為空，請檢查 JSON 結構。")

else:
  st.info("👈 請從左側側邊欄上傳您的 `DANGDAI_ALL.json` 檔案開始分析！")