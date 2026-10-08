import collections
import jieba
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from wordcloud import WordCloud

# 設定網頁版面
st.set_page_config(
    page_title="華語文教材微型文字探勘儀表板", layout="wide"
)

st.title("📚 華語文教材內容分析儀表板 (Mini-Voyant)")
st.write(
    "上傳整理好的華語教材 CSV 語料檔案，系統將自動進行繁體中文斷詞、功能詞過濾"
    "，並即時產出文字雲與詞頻統計表！"
)

# 1. 側邊欄：檔案上傳與格式說明
st.sidebar.header("1. 資料上傳與欄位規範")

uploaded_file = st.sidebar.file_uploader(
    "上傳 Voyant 專用 CSV 檔案", type=["csv"]
)

# 提供清晰的 CSV 欄位說明
with st.sidebar.expander("📌 CSV 欄位格式說明 (點此展開)", expanded=False):
  st.markdown("""
        您的 CSV 檔案必須包含以下三個欄位（建議 UTF-8 編碼）：
        - **Book**：冊別（例如：`第一冊`, `第二冊`）
        - **Lesson**：課別（例如：`第一課：歡迎你來台灣！`）
        - **Text_Content**：該課的完整對話與文章文本
    """)

st.sidebar.markdown("---")
st.sidebar.header("2. 斷詞與功能詞（停用詞）設定")

# 預設中文功能詞
default_stopwords = (
    "的,了,和,是,就,都,而,及,與,著,或,一個,沒有,我們,你們,他們,你,我,他,"
    "這,那,在,有,個,要,去,來,說,吧,嗎,呢,啊,呀,哦,啦,把,被,讓,向,從,這"
    "個,那裡,這裡,什麼,怎麼,時候"
)

# 教學互動：是否啟用過濾功能詞
enable_stopwords = st.sidebar.checkbox(
    "啟用功能詞（Stopwords）過濾",
    value=True,
    help="勾選後將會排除下方設定的無意義虛詞，幫助學生看見真正的實詞。",
)

# 可編輯的停用詞清單
stopwords_input = st.sidebar.text_area(
    "編輯停用詞清單 (以逗號分隔)", default_stopwords, height=150
)
stopwords = set([w.strip() for w in stopwords_input.split(",") if w.strip()])

# 若有上傳檔案
if uploaded_file is not None:
  try:
    # 讀取 CSV
    df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    st.sidebar.success("CSV 檔案載入成功！")
  except Exception as e:
    st.sidebar.error(f"CSV 讀取錯誤（請確認編碼是否為 UTF-8）：{e}")
    st.stop()

  # 檢查必要欄位
  required_cols = ["Book", "Lesson", "Text_Content"]
  if not all(col in df.columns for col in required_cols):
    st.error(
        f"CSV 欄位不符！您的檔案欄位為: {list(df.columns)}，必須包含 Book,"
        " Lesson, Text_Content。"
    )
    st.stop()

  # 選擇要分析的冊別
  books = df["Book"].dropna().unique().tolist()
  selected_book = st.sidebar.selectbox("選擇要分析的冊別", sorted(books))

  # 篩選該冊的文本
  df_filtered = df[df["Book"] == selected_book]
  corpus_text = " ".join(df_filtered["Text_Content"].astype(str).tolist())

  if corpus_text.strip():
    # 進行 jieba 斷詞
    words = jieba.cut(corpus_text)

    # 過濾邏輯：若勾選啟用停用詞，則排除；同時預設排除長度為 1 的單字與空白
    filtered_words = []
    for w in words:
      w_clean = w.strip()
      if not w_clean:
        continue
      if len(w_clean) <= 1:
        continue  # 排除單字
      if enable_stopwords and w_clean in stopwords:
        continue  # 排除停用詞
      filtered_words.append(w_clean)

    # 計算詞頻
    word_counts = collections.Counter(filtered_words)
    df_freq = pd.DataFrame(
        word_counts.most_common(50), columns=["詞彙", "出現頻次"]
    )

    # 畫面左右排版（修正 st.columns 語法錯誤）
    col1, col2 = st.columns(2)

    with col1:
      st.subheader(f"📊 {selected_book} - 詞頻排行榜 Top 50")
      st.dataframe(df_freq, height=500, use_container_width=True)

    with col2:
      st.subheader("☁️ 文字雲視覺化 (Word Cloud)")
      if len(word_counts) > 0:
        try:
          # Windows 本地測試可用微軟正黑體，若部署到雲端 Linux 建議放一個 .ttf 字型檔在專案中
          font_path = "C:/Windows/Fonts/msjh.ttc"
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
              f"文字雲繪製提示（若在雲端環境未內建中文字型，可改看下方長條圖）：{e}"
          )
          st.bar_chart(df_freq.set_index("詞彙").head(20))
      else:
        st.warning(
            "目前篩選條件下沒有足夠的詞彙可產生文字雲，請試著取消部分停用詞。"
        )

  else:
    st.warning("該冊內容為空，請檢查 CSV 檔案。")

else:
  st.info(
      "👈 請從左側側邊欄上傳您的 Voyant 專用 CSV 檔案（包含 Book, Lesson,"
      " Text_Content 欄位）開始分析！"
  )
