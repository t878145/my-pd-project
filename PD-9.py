import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io

# 設定 matplotlib 使用支援中文的備選字型清單
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'Microsoft JhengHei', 'SimHei', 'WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus'] = False

# ==================================
# 版本及作者資訊
# ==================================
CURRENT_VERSION = "1.1.0"
UPDATE_LOG = """版本更新紀錄：
1.1.0 - 加入登入系統與帳號管理功能。
1.0.11 - 修改刪除專案功能：可多重選取後一次刪除。
"""
AUTHOR = "KIM"

# ==================================
# 1. 初始化資料庫 (確保有 `projects` 和 `users` 表)
# ==================================
def init_db():
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    # 專案資料表
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
    # 使用者帳號表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
    ''')
    # 預設管理員帳號
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

# ==================================
# 2. 登入驗證
# ==================================
def authenticate(username, password):
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# ==================================
# 3. 帳號管理（僅限 `admin`）
# ==================================
def manage_accounts():
    st.subheader("👤 帳號管理")
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()

    # 顯示現有帳號
    df_users = pd.read_sql_query("SELECT username, role FROM users", conn)
    st.dataframe(df_users, use_container_width=True)

    # 新增帳號
    with st.form("add_user_form"):
        new_username = st.text_input("新帳號")
        new_password = st.text_input("新密碼", type="password")
        new_role = st.selectbox("角色", ["admin", "user"])
        add_user = st.form_submit_button("新增帳號")
        if add_user and new_username and new_password:
            try:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_username, new_password, new_role))
                conn.commit()
                st.success(f"✅ 帳號 `{new_username}` 已新增！")
            except sqlite3.IntegrityError:
                st.error("❌ 該帳號已存在！")

    # 刪除帳號
    del_username = st.text_input("要刪除的帳號")
    if st.button("刪除帳號"):
        if del_username and del_username != "admin":
            cursor.execute("DELETE FROM users WHERE username = ?", (del_username,))
            conn.commit()
            st.warning(f"🗑️ 帳號 `{del_username}` 已刪除！")
        else:
            st.error("❌ 不可刪除 `admin` 帳號！")

    conn.close()

# ==================================
# 4. Streamlit 主程式
# ==================================
def main():
    st.set_page_config(page_title="工程專案資料庫", layout="wide")
    st.title("🏗️ 工程專案資料庫")
    
    init_db()  # 確保資料庫存在

    # ============== 登入功能 ==============
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""

    if not st.session_state.logged_in:
        with st.form("login_form"):
            st.subheader("🔑 登入")
            username = st.text_input("帳號")
            password = st.text_input("密碼", type="password")
            login_btn = st.form_submit_button("登入")

        if login_btn:
            role = authenticate(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.experimental_rerun()
            else:
                st.error("❌ 帳號或密碼錯誤")

    else:
        st.sidebar.success(f"👋 歡迎，{st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("登出"):
            st.session_state.logged_in = False
            st.experimental_rerun()

        # ============== 建立分頁 ==============
        tab1, tab2, tab3 = st.tabs(["專案管理", "帳號管理" if st.session_state.role == "admin" else None, "關於"])

        # ============== 專案管理 ==============
        with tab1:
            st.subheader("🔨 專案管理")
            st.write("這裡可以管理你的工程專案")

        # ============== 帳號管理（僅 `admin`） ==============
        if st.session_state.role == "admin":
            with tab2:
                manage_accounts()

        # ============== 關於 ==============
        with tab3:
            st.subheader("ℹ️ 關於本程式")
            info = f"""
            **程式名稱**：工程專案資料庫  
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
