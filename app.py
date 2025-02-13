import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io

# 設定 matplotlib 使用支援中文的備選字型清單
plt.rcParams['font.sans-serif'] = [
    'Noto Sans CJK TC',  # Google 推出的免費中文字型，跨平台支援不錯
    'Microsoft JhengHei', # Windows 預設
    'SimHei',             # Linux 部分環境有安裝
    'WenQuanYi Zen Hei'   # Ubuntu 常見中文字型
]
plt.rcParams['axes.unicode_minus'] = False

# ==================================
# 版本及作者資訊 (對應原程式)
# ==================================
CURRENT_VERSION = "1.0.11"
UPDATE_LOG = """版本更新紀錄：
1.0.0 - 初始版本。
1.0.1 - 修正部份錯誤，增加查詢功能。
1.0.2 - 加入水平捲軸功能。
1.0.3 - 加入版本更新記錄及作者資訊。
1.0.4 - 增加圖表分析功能：年度趨勢、成本差異、廠商分佈、管銷成本佔比分析。
1.0.5 - 移除成本差異與效益分析、管銷成本佔比分析功能。
1.0.6 - 移除各廠商契約來價分析功能，僅保留廠商專案數比例（圓餅圖）。
1.0.7 - 調整廠商專案數比例圓餅圖，引線標註廠商名稱。
1.0.8 - 固定扇區標籤放置在圖表左右兩側，垂直均分排列。
1.0.9 - 調整專案管理頁面資料顯示視窗的列高。
1.0.10 - 為資料顯示視窗加入交替行背景色。
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
# 2. 新增專案
# ==================================
def add_project(year, site_name, project_name, contract_price,
                execution_budget, contractor_price, contractor, remarks):
    try:
        indirect_cost = contract_price - execution_budget
    except:
        indirect_cost = 0
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO projects (year, site_name, project_name, contract_price,
        execution_budget, contractor_price, indirect_cost, contractor, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (year, site_name, project_name, contract_price,
          execution_budget, contractor_price, indirect_cost, contractor, remarks))
    conn.commit()
    conn.close()

# ==================================
# 3. 查詢專案 (依條件過濾)
# ==================================
def query_projects(year="", site="", project=""):
    conn = sqlite3.connect("projects.db")
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    if year:
        query += " AND year LIKE ?"
        params.append(f"%{year}%")
    if site:
        query += " AND site_name LIKE ?"
        params.append(f"%{site}%")
    if project:
        query += " AND project_name LIKE ?"
        params.append(f"%{project}%")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ==================================
# 4. 讀取所有專案 (顯示用)
# ==================================
def get_all_projects():
    conn = sqlite3.connect("projects.db")
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

# ==================================
# 5. 更新專案
# ==================================
def update_project(pid, year, site_name, project_name, contract_price,
                   execution_budget, contractor_price, contractor, remarks):
    try:
        indirect_cost = contract_price - execution_budget
    except:
        indirect_cost = 0
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE projects
        SET year=?, site_name=?, project_name=?, contract_price=?,
            execution_budget=?, contractor_price=?, indirect_cost=?,
            contractor=?, remarks=?
        WHERE id=?
    """, (year, site_name, project_name, contract_price,
          execution_budget, contractor_price, indirect_cost,
          contractor, remarks, pid))
    conn.commit()
    conn.close()

# ==================================
# 6. 刪除專案 (可一次多筆)
# ==================================
def delete_projects(ids):
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    for pid in ids:
        cursor.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()

# ==================================
# 7. 匯出 Excel
# ==================================
def export_excel():
    """回傳一個 bytes 物件，給 streamlit download_button 使用"""
    df = get_all_projects()
    # 重新命名欄位(與原 Tkinter 程式對應)
    df.columns = ["ID", "年度", "工地名稱", "承攬項目", "契約來價(未稅)",
                  "執行預算(未稅)", "廠商發包價(未稅)", "管銷(契約間接費用)",
                  "廠商", "備註"]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="projects")
    processed_data = output.getvalue()
    return processed_data

# ==================================
# 8. 匯入 Excel
# ==================================
def import_excel(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            # 預期的中文欄位與英文欄位對應
            chinese_to_eng = {
                "ID": "id",
                "年度": "year",
                "工地名稱": "site_name",
                "承攬項目": "project_name",
                "契約來價(未稅)": "contract_price",
                "執行預算(未稅)": "execution_budget",
                "廠商發包價(未稅)": "contractor_price",
                "管銷(契約間接費用)": "indirect_cost",
                "廠商": "contractor",
                "備註": "remarks"
            }
            required_cols = ["年度", "工地名稱", "承攬項目"]
            for req in required_cols:
                if req not in df.columns:
                    st.error(f"Excel 檔案缺少必要欄位：{req}")
                    return

            # 轉換欄位名稱
            df = df.rename(columns=chinese_to_eng)
            # 若有 id 欄位，先移除，因為資料庫會自動產生
            if "id" in df.columns:
                df.drop("id", axis=1, inplace=True)

            # 將資料寫入資料庫
            conn = sqlite3.connect("projects.db")
            cursor = conn.cursor()
            success_count = 0
            error_count = 0
            for _, row in df.iterrows():
                # 必要欄位不能為空
                if pd.isna(row["year"]) or pd.isna(row["site_name"]) or pd.isna(row["project_name"]):
                    error_count += 1
                    continue

                year_val = str(row["year"]).strip()
                site_val = str(row["site_name"]).strip()
                proj_val = str(row["project_name"]).strip()
                cp_val = 0 if pd.isna(row.get("contract_price", 0)) else row.get("contract_price", 0)
                eb_val = 0 if pd.isna(row.get("execution_budget", 0)) else row.get("execution_budget", 0)
                ctp_val = 0 if pd.isna(row.get("contractor_price", 0)) else row.get("contractor_price", 0)
                if "indirect_cost" in row and pd.notna(row["indirect_cost"]):
                    ic_val = row["indirect_cost"]
                else:
                    ic_val = cp_val - eb_val
                contractor_val = str(row.get("contractor", "")).strip()
                remarks_val = str(row.get("remarks", "")).strip()

                try:
                    cursor.execute("""
                        INSERT INTO projects (year, site_name, project_name,
                            contract_price, execution_budget, contractor_price,
                            indirect_cost, contractor, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (year_val, site_val, proj_val, cp_val,
                          eb_val, ctp_val, ic_val, contractor_val, remarks_val))
                    success_count += 1
                except Exception as e:
                    error_count += 1
            conn.commit()
            conn.close()
            st.success(f"匯入完成！成功：{success_count}，失敗：{error_count}")
        except Exception as e:
            st.error(f"匯入過程發生錯誤：{e}")

# ==================================
# 9. 分析功能：年度趨勢分析
# ==================================
def analyze_yearly_trend():
    df = get_all_projects()
    if df.empty:
        st.warning("目前沒有專案資料，無法進行年度分析。")
        return

    # 轉數值
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
# 10. 分析功能：廠商分佈分析 (圓餅圖)
# ==================================
def analyze_contractor_distribution():
    df = get_all_projects()
    if df.empty:
        st.warning("目前沒有專案資料，無法進行廠商分佈分析。")
        return

    contractor_count = df.groupby("contractor")["id"].count()
    if contractor_count.empty:
        st.warning("資料中沒有廠商資訊，無法分析。")
        return

    total = contractor_count.sum()
    fig, ax = plt.subplots(figsize=(8, 6))
    explode = [0.05] * len(contractor_count)
    wedges, _ = ax.pie(contractor_count.values, explode=explode, startangle=90, labels=None)
    ax.set_title("各廠商專案數比例")

    # 收集各扇區資訊
    labels_info = []
    for i, wedge in enumerate(wedges):
        angle = (wedge.theta2 + wedge.theta1) / 2.0
        x = np.cos(np.deg2rad(angle))
        y = np.sin(np.deg2rad(angle))
        percentage = contractor_count.values[i] / total * 100
        vendor = contractor_count.index[i] if contractor_count.index[i] else "未填廠商"
        group = "right" if x >= 0 else "left"
        labels_info.append({
            "vendor": vendor,
            "percentage": percentage,
            "wedge_center": (x, y),
            "group": group
        })

    # 分組 (左/右)
    left_labels = [d for d in labels_info if d["group"] == "left"]
    right_labels = [d for d in labels_info if d["group"] == "right"]
    # 依 y 值排序，讓標籤由上而下排列
    left_labels.sort(key=lambda d: d["wedge_center"][1], reverse=True)
    right_labels.sort(key=lambda d: d["wedge_center"][1], reverse=True)

    def assign_y_positions(group, side):
        n = len(group)
        if n == 0:
            return
        ys = np.linspace(0.9, -0.9, n)
        fixed_x = -1.3 if side == "left" else 1.3
        for i, d in enumerate(group):
            d["label_pos"] = (fixed_x, ys[i])

    assign_y_positions(left_labels, "left")
    assign_y_positions(right_labels, "right")

    # 繪製標籤
    for d in left_labels + right_labels:
        x, y = d["wedge_center"]
        label_x, label_y = d["label_pos"]
        label_text = f"{d['percentage']:.1f}% {d['vendor']}"
        ha = "right" if d["group"] == "left" else "left"
        ax.annotate(label_text, xy=(x, y), xytext=(label_x, label_y),
                    ha=ha, va="center",
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"),
                    fontsize=10)
    st.pyplot(fig)

# ==================================
# Streamlit 主程式
# ==================================
def main():
    st.set_page_config(page_title="工程專案資料庫", layout="wide")
    st.title("🏗️ 工程專案資料庫")

    # 初始化資料庫
    init_db()

    # 建立三個分頁 (專案管理 / 資料分析 / 關於)
    tab1, tab2, tab3 = st.tabs(["專案管理", "資料分析", "關於"])

    # ============== 專案管理 ==============
    with tab1:
        st.subheader("🔨 專案管理")

        # --- 新增專案表單 ---
        with st.expander("新增專案"):
            with st.form("add_project_form"):
                col1, col2, col3 = st.columns(3)
                year = col1.text_input("年度")
                site_name = col2.text_input("工地名稱")
                project_name = col3.text_input("承攬項目")
                col4, col5, col6 = st.columns(3)
                contract_price = col4.number_input("契約來價(未稅)", min_value=0.0, format="%.2f")
                execution_budget = col5.number_input("執行預算(未稅)", min_value=0.0, format="%.2f")
                contractor_price = col6.number_input("廠商發包價(未稅)", min_value=0.0, format="%.2f")
                contractor = st.text_input("廠商")
                remarks = st.text_area("備註")

                submitted = st.form_submit_button("新增專案")
                if submitted:
                    if year and site_name and project_name:
                        add_project(year, site_name, project_name, contract_price,
                                    execution_budget, contractor_price, contractor, remarks)
                        st.success("✅ 專案已新增！")
                    else:
                        st.error("請填寫必要欄位：年度 / 工地名稱 / 承攬項目")

        # --- 查詢專案 ---
        st.subheader("🔍 專案查詢")
        with st.form("query_form"):
            q_col1, q_col2, q_col3, q_col4 = st.columns([1,1,1,0.5])
            query_year = q_col1.text_input("查詢 - 年度")
            query_site = q_col2.text_input("查詢 - 工地名稱")
            query_project_name = q_col3.text_input("查詢 - 承攬項目")
            query_btn = q_col4.form_submit_button("查詢")

        # 這裡定義一個「英文欄位 → 中文欄位」對應表
        rename_dict = {
            "id": "ID",
            "year": "年度",
            "site_name": "工地名稱",
            "project_name": "承攬項目",
            "contract_price": "契約來價(未稅)",
            "execution_budget": "執行預算(未稅)",
            "contractor_price": "廠商發包價(未稅)",
            "indirect_cost": "管銷(契約間接費用)",
            "contractor": "廠商",
            "remarks": "備註"
        }

        if query_btn:
            df_query = query_projects(query_year, query_site, query_project_name)
            df_query.rename(columns=rename_dict, inplace=True)
            st.dataframe(df_query, use_container_width=True)
        else:
            df_all = get_all_projects()
            df_all.rename(columns=rename_dict, inplace=True)
            st.dataframe(df_all, use_container_width=True)

        # --- 修改專案 ---
        st.subheader("✏️ 修改專案")
        with st.expander("修改指定專案"):
            st.write("請輸入要修改的專案 ID，並填寫更新後的資訊")
            with st.form("update_form"):
                pid = st.text_input("專案 ID（僅能輸入單筆）")
                col_u1, col_u2, col_u3 = st.columns(3)
                u_year = col_u1.text_input("年度")
                u_site_name = col_u2.text_input("工地名稱")
                u_project_name = col_u3.text_input("承攬項目")
                col_u4, col_u5, col_u6 = st.columns(3)
                u_contract_price = col_u4.number_input("契約來價(未稅)", min_value=0.0, format="%.2f")
                u_execution_budget = col_u5.number_input("執行預算(未稅)", min_value=0.0, format="%.2f")
                u_contractor_price = col_u6.number_input("廠商發包價(未稅)", min_value=0.0, format="%.2f")
                u_contractor = st.text_input("廠商")
                u_remarks = st.text_area("備註")

                update_submitted = st.form_submit_button("更新專案")
                if update_submitted:
                    if not pid.isdigit():
                        st.error("請輸入有效的專案 ID（數字）")
                    else:
                        if u_year and u_site_name and u_project_name:
                            update_project(int(pid), u_year, u_site_name, u_project_name,
                                           u_contract_price, u_execution_budget,
                                           u_contractor_price, u_contractor, u_remarks)
                            st.success(f"✅ 專案 ID {pid} 已更新！")
                        else:
                            st.error("請填寫必要欄位：年度 / 工地名稱 / 承攬項目")

        # --- 刪除專案 ---
        st.subheader("🗑️ 刪除專案")
        with st.expander("刪除指定專案（可多筆）"):
            st.write("輸入專案 ID（多筆以逗號分隔，如：1,3,5）")
            del_input = st.text_input("專案 ID 清單")
            if st.button("刪除專案"):
                if del_input.strip():
                    # 分割多個 ID
                    id_list = [x.strip() for x in del_input.split(",") if x.strip().isdigit()]
                    if id_list:
                        delete_projects(id_list)
                        st.warning(f"已刪除以下專案 ID：{', '.join(id_list)}")
                    else:
                        st.error("請輸入有效的專案 ID（數字），多筆以逗號分隔。")
                else:
                    st.error("請輸入要刪除的專案 ID")

        # --- 匯入 / 匯出 Excel ---
        st.subheader("📂 匯入 / 匯出 Excel")
        col_ie1, col_ie2 = st.columns(2)
        with col_ie1:
            uploaded_file = st.file_uploader("選擇要匯入的 Excel 檔案（.xlsx）", type=["xlsx"])
            if uploaded_file and st.button("匯入Excel"):
                import_excel(uploaded_file)
        with col_ie2:
            excel_data = export_excel()
            st.download_button(
                label="匯出Excel",
                data=excel_data,
                file_name="projects_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ============== 資料分析 ==============
    with tab2:
        st.subheader("📊 資料分析")
        st.write("使用下方按鈕進行圖表分析：")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            if st.button("年度趨勢分析"):
                analyze_yearly_trend()
        with col_a2:
            if st.button("廠商與市場分佈分析"):
                analyze_contractor_distribution()

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
