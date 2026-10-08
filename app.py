import collections
import jieba
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from wordcloud import WordCloud

# 設定網頁版面
st.set_page_config(
    page_title="通用型華語文文字探勘儀表板", layout="wide"
)

st.title("📚 通用型文本內容分析儀表板 (Mini-Voyant)")
st.write(
    "上傳任意結構的 CSV 語料檔案，系統將自動鎖定**最後一個欄位**進行繁體中文斷詞"
    "，並即時產出文字雲與詞頻統計！"
)

# 1. 側邊欄：檔案上傳與設定
st.sidebar.header("1. 資料上傳與設定")
uploaded_file = st.sidebar.file_uploader("上傳 CSV 語料檔案", type=["csv"])

with st.sidebar.expander("📌 檔案格式說明 (點此展開)", expanded=False):
  st.markdown("""
        - 檔案格式必須為 **CSV**（建議編碼：`UTF-8 with BOM`）。
        - 欄位數量不限。
        - **系統規則**：會自動將 **「最後一個欄位」** 視為要分析的文本內容（Text Content）。
    """)

st.sidebar.markdown("---")
st.sidebar.header("2. 斷詞與功能詞設定")

# 預設中文功能詞
default_stopwords = (
    "的,了,和,是,就,都,而,及,與,著,或,一個,沒有,我們,你們,他們,你,我,他,"
    "這,那,在,有,個,要,去,來,說,吧,嗎,呢,啊,呀,哦,啦,把,被,讓,向,從,這"
    "個,那裡,這裡,什麼,怎麼,時候"
)

enable_stopwords = st.sidebar.checkbox("啟用功能詞（Stopwords）過濾", value=True)
stopwords_input = st.sidebar.text_area(
    "編輯停用詞清單 (以逗號分隔)", default_stopwords, height=120
)
stopwords = set([w.strip() for w in stopwords_input.split(",") if w.strip()])

# 若有上傳檔案
if uploaded_file is not None:
  try:
    df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
  except Exception as e:
    st.sidebar.error(f"CSV 讀取錯誤（請確認編碼是否為 UTF-8）：{e}")
    st.stop()

  cols = df.columns.tolist()
  if len(cols) < 1:
    st.error("CSV 檔案沒有欄位！")
    st.stop()

  text_col = cols[-1]
  meta_cols = cols[:-1]

  st.sidebar.markdown("---")
  st.sidebar.info(f"🔍 **自動識別文本欄位**：`{text_col}`")

  selected_subset = df
  selected_group_name = "全部資料（綜合分析）"

  if len(meta_cols) > 0:
    group_col = st.sidebar.selectbox("選擇分類篩選欄位", meta_cols)
    unique_vals = ["全部"] + sorted(
        df[group_col].dropna().unique().astype(str).tolist()
    )
    selected_val = st.sidebar.selectbox(f"篩選 [{group_col}] 的數值", unique_vals)

    if selected_val != "全部":
      selected_subset = df[df[group_col].astype(str) == selected_val]
      selected_group_name = f"{group_col}: {selected_val}"

  # 重新分析按鈕
  st.sidebar.markdown("---")
  if st.sidebar.button("🔄 重新分析", use_container_width=True):
    st.toast("已重新整理分析結果！", icon="🚀")

  # 針對最後一欄進行斷詞
  corpus_text = " ".join(selected_subset[text_col].astype(str).tolist())

  if corpus_text.strip():
    words = jieba.cut(corpus_text)

    filtered_words = []
    for w in words:
      w_clean = w.strip()
      if not w_clean or len(w_clean) <= 1:
        continue
      if enable_stopwords and w_clean in stopwords:
        continue
      filtered_words.append(w_clean)

    # 計算詞頻
    word_counts = collections.Counter(filtered_words)
    df_freq = pd.DataFrame(
        word_counts.most_common(50), columns=["詞彙", "出現頻次"]
    )

    st.markdown(f"### 🎯 目前分析範圍：`{selected_group_name}`")
    st.markdown(f"共分析了 **{len(selected_subset)}** 筆文本資料。")

    col1, col2 = st.columns(2)

    with col1:
      st.subheader("📊 詞頻排行榜 Top 50")
      st.dataframe(df_freq, height=500, use_container_width=True)

    with col2:
      st.subheader("☁️ 文字雲視覺化 (Word Cloud)")
      if len(word_counts) > 0:
        try:
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
          st.warning(f"文字雲繪製提示：{e}")
      else:
        st.warning("沒有足夠詞彙產生文字雲。")

    # 保留乾淨的直式長條圖
    st.markdown("---")
    st.subheader("📈 前 20 大熱門詞彙分佈（長條圖）")
    if len(df_freq) > 0:
      st.bar_chart(df_freq.set_index("詞彙")["出現頻次"].head(20))
    else:
      st.info("尚無數據可繪製長條圖。")

  else:
    st.warning("選取的範圍內文字內容為空。")

else:
  st.info("👈 請從左側側邊欄上傳您的 CSV 語料檔案開始進行分析！")
