import collections
import jieba
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# 設定網頁版面
st.set_page_config(
    page_title="通用型華語文文字探勘儀表板", layout="wide"
)

st.title("📚 通用型文本內容分析儀表板 (Mini-Voyant)")
st.write(
    "支援**多筆同格式 CSV 檔案同時上傳**，系統將自動合併並鎖定**最後一個欄位**"
    "進行繁體中文斷詞，即時產出詞頻排行榜與詞頻長條圖！"
)

# 1. 側邊欄：檔案上傳與設定
st.sidebar.header("1. 資料上傳與設定")
uploaded_files = st.sidebar.file_uploader(
    "上傳 CSV 語料檔案 (可多選)", type=["csv"], accept_multiple_files=True
)

with st.sidebar.expander("📌 檔案格式與多檔上傳說明", expanded=False):
  st.markdown("""
        - 檔案格式必須為 **CSV**（建議編碼：`UTF-8 with BOM`）。
        - 支援**同時上傳多個檔案**。
        - **格式安全機制**：若上傳多個檔案，系統會自動檢查欄位是否完全一致。
        - **系統規則**：自動將 **「最後一個欄位」** 視為要分析的文本內容（Text Content）。
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

# 長條圖顯示數量設定
st.sidebar.markdown("---")
st.sidebar.header("3. 圖表顯示設定")
top_n = st.sidebar.slider(
    "長條圖顯示詞彙數量 (Top N)", min_value=5, max_value=50, value=20
)

# 若有上傳檔案
if uploaded_files:
  dfs = []
  base_columns = None
  format_error = False

  for file in uploaded_files:
    try:
      temp_df = pd.read_csv(file, encoding="utf-8-sig")
    except Exception as e:
      st.error(f"檔案 `{file.name}` 讀取錯誤：{e}")
      st.stop()

    if base_columns is None:
      base_columns = temp_df.columns.tolist()
    else:
      if temp_df.columns.tolist() != base_columns:
        format_error = True
        break
    dfs.append(temp_df)

  if format_error:
    st.error(
        "⚠️ **格式不符警告**：您上傳的多個 CSV 檔案中，欄位結構存在差異！"
        "請整理成格式完全相同的 CSV 後再重新一起上傳。"
    )
    st.stop()

  df = pd.concat(dfs, ignore_index=True)

  cols = df.columns.tolist()
  text_col = cols[-1]
  meta_cols = cols[:-1]

  st.sidebar.markdown("---")
  st.sidebar.info(
      f"🔍 **已成功合併 {len(uploaded_files)} 個檔案**\n\n自動識別文本欄位："
      f" `{text_col}`"
  )

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

    word_counts = collections.Counter(filtered_words)
    df_freq = pd.DataFrame(
        word_counts.most_common(50), columns=["詞彙", "出現頻次"]
    )

    st.markdown(f"### 🎯 目前分析範圍：`{selected_group_name}`")
    st.markdown(f"共整合分析了 **{len(selected_subset)}** 筆文本資料。")

    # 完整呈現詞頻排行榜（全寬顯示，清晰易讀）
    st.subheader("📊 詞頻排行榜 Top 50")
    st.dataframe(df_freq, height=400, use_container_width=True)

    # 呈現長條圖
    st.markdown("---")
    st.subheader(f"📈 前 {top_n} 大熱門詞彙分佈（長條圖）")
    if len(df_freq) > 0:
      st.bar_chart(df_freq.set_index("詞彙")["出現頻次"].head(top_n))
    else:
      st.info("尚無數據可繪製長條圖。")

  else:
    st.warning("選取的範圍內文字內容為空。")

else:
  st.info("👈 請從左側側邊欄上傳您的 CSV 語料檔案（支援多檔同格式）開始分析！")
