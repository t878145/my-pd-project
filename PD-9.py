import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io

# 設定 matplotlib 使用支援中文的備選字型清單
plt.rcParams['font.sans-serif'] = [
    'Noto Sans CJK TC', 'Microsoft JhengHei', 'SimHei', 'WenQuanYi Zen Hei'
]
plt.rcParams['axes.unicode_minus'] = False

# ================================
# 初始化資料庫
# ================================
def init_db():
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()

    # 建立專案資料表
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

    # 建立使用者資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
    ''')

    # 預設建立 `admin` 帳號
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")

    conn.commit()
    conn.close()

# ================================
# 登入功能
# ================================
def login_user(username, password):
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# ================================
# 新增使用者（僅限 admin）
# ================================
def add_user(username, password, role):
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("此帳號已存在")
    finally:
        conn.close()

# ================================
# 刪除使用者（僅限 admin）
# ================================
def delete_user(username):
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

# ================================
# 取得所有使用者（僅限 admin）
# ================================
def get_all_users():
    conn = sqlite3.connect("projects.db")
    df = pd.read_sql_query("SELECT username, role FROM users", conn)
    conn.close()
    return df

# ================================
# Streamlit 主程式
# ================================
def main():
    st.set_page_config(page_title="工程專案管理", layout="wide")

    # 初始化資料庫
    init_db()

    # ----------------------------
    # **登入頁面**
    # ----------------------------
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None

    if not st.session_state["logged_in"]:
        st.title("🔑 登入工程專案管理系統")
        username = st.text_input("使用者名稱", key="login_user")
        password = st.text_input("密碼", type="password", key="login_pass")

        if st.button("登入"):
            user = login_user(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user[0]
                st.rerun()
            else:
                st.error("登入失敗，請檢查帳號或密碼")
        return

    # ----------------------------
    # **主畫面**
    # ----------------------------
    st.sidebar.title("🔧 功能選單")
    option = st.sidebar.radio("選擇功能", ["專案管理", "帳號管理", "登出"])

    # ----------------------------
    # **專案管理**
    # ----------------------------
    if option == "專案管理":
        st.title("🏗️ 工程專案管理")
        st.write(f"**登入帳號：** {st.session_state['username']} **(角色：{st.session_state['role']})**")

        df_projects = get_all_users()  # 這裡應該是查詢專案，僅示範
        st.dataframe(df_projects)

    # ----------------------------
    # **帳號管理（僅限 admin）**
    # ----------------------------
    if option == "帳號管理":
        if st.session_state["role"] != "admin":
            st.warning("⚠️ 只有管理員 (admin) 才能進入帳號管理")
        else:
            st.title("🔑 帳號管理")
            st.subheader("現有使用者")

            df_users = get_all_users()
            st.dataframe(df_users)

            st.subheader("新增帳號")
            new_username = st.text_input("帳號")
            new_password = st.text_input("密碼", type="password")
            new_role = st.selectbox("角色", ["admin", "user"])

            if st.button("新增使用者"):
                if new_username and new_password:
                    add_user(new_username, new_password, new_role)
                    st.success(f"✅ 已新增帳號：{new_username}（角色：{new_role}）")
                    st.rerun()
                else:
                    st.error("請輸入帳號與密碼")

            st.subheader("刪除帳號")
            del_username = st.text_input("輸入要刪除的帳號")

            if st.button("刪除使用者"):
                if del_username:
                    delete_user(del_username)
                    st.success(f"🗑️ 已刪除帳號：{del_username}")
                    st.rerun()
                else:
                    st.error("請輸入帳號")

    # ----------------------------
    # **登出**
    # ----------------------------
    if option == "登出":
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.rerun()

# ================================
# 主程式執行
# ================================
if __name__ == "__main__":
    main()
