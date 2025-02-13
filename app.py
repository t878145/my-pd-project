import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io

# 設定 Streamlit 全域 CSS，強制 UI 使用支援中文字的字型
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC&display=swap');
    * {
        font-family: 'Noto Sans TC', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 設定 matplotlib 使用支援中文的備選字型清單
plt.rcParams['font.sans-serif'] = [
    'Noto Sans CJK TC',  # Google 免費中文字型，適用於 Linux & Mac
    'Microsoft JhengHei', # Windows 預設中文字型
    'SimHei',             # Linux 可能有預裝
    'WenQuanYi Zen Hei'   # Ubuntu 常見中文字型
]
plt.rcParams['axes.unicode_minus'] = False  # 避免負號顯示錯誤

# ==================================
# 版本及作者資訊
# ==================================
CURRENT_VERSION = "1.0.11"
UPDATE_LOG = """版本更新紀錄：
1.0.0 - 初始版本。
1.0.11 - 修改刪除專案功能：可多重選取後一次刪除。
"""
AUTHOR = "KIM"

# ==================================
# 1. 初始化資料庫 (若無則建立)
# ==================================
def init_db():
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year TEXT NOT NULL,
            site_name TEXT NOT NULL,
            project_name TEXT NOT NULL,
            contract_price REAL DEFAULT 0,
            execution_budget REAL DEFAULT 0,
            contractor_price REAL DEFAULT 0,
            indirect_cost REAL DEFAULT 0,
            contractor TEXT,
            remarks TEXT
        );
    ''')
    conn.commit()
    conn.close()

# ==================================
# 9. 分析功能：年度趨勢分析
# ==================================
def analyze_yearly_trend():
    df = get_all_projects()
    if df.empty:
        st.warning("目前沒有專案資料，無法進行年度分析。")
        return

    df["contract_price"] = pd.to_numeric(df["contract_price"], errors="coerce")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    yearly_sum = df.groupby("year")["contract_price"].sum()
    yearly_count = df.groupby("year")["id"].count()

    fig, ax = plt.subplots(1, 2, figsize=(12, 5))

    bars1 = ax[0].bar(yearly_sum.index, yearly_sum.values, color="skyblue")
    ax[0].set_title("每年度總契約來價")
    ax[0].set_xlabel("年度")
    ax[0].set_ylabel("契約來價")
    for bar in bars1:
        height = bar.get_height()
        ax[0].text(bar.get_x() + bar.get_width()/2, height, f"{height:,.0f}",
                   ha="center", va="bottom", fontsize=9)

    bars2 = ax[1].bar(yearly_count.index, yearly_count.values, color="salmon")
    ax[1].set_title("每年度專案數量")
    ax[1].set_xlabel("年度")
    ax[1].set_ylabel("專案數量")
    for bar in bars2:
        height = bar.get_height()
        ax[1].text(bar.get_x() + bar.get_width()/2, height, f"{int(height)}",
                   ha="center", va="bottom", fontsize=9)

    st.pyplot(fig)

# ==================================
# Streamlit 主程式
# ==================================
def main():
    st.set_page_config(page_title="工程專案資料庫", layout="wide")
    st.title("🏗️ 工程專案資料庫 (Streamlit 版)")

    # 初始化資料庫
    init_db()

    # 建立分頁
    tab1, tab2, tab3 = st.tabs(["專案管理", "資料分析", "關於"])

    # ============== 資料分析 ==============
    with tab2:
        st.subheader("📊 資料分析")
        st.write("使用下方按鈕進行圖表分析：")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            if st.button("年度趨勢分析"):
                analyze_yearly_trend()

    # ============== 關於 ==============
    with tab3:
        st.subheader("ℹ️ 關於本程式")
        info = f"""
        **程式名稱**：工程專案資料庫 (Streamlit 版)  
        **目前版本**：{CURRENT_VERSION}  
        **作者**：{AUTHOR}  

        **更新紀錄**：  
        {UPDATE_LOG}
        """
        st.markdown(info)

# ==================================
# 主程式進入點
# ==================================
if __name__ == "__main__":
    main()
