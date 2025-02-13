try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    print("錯誤: tkinter 模組不可用，請確認是否已安裝。")
    exit()

import sqlite3
import pandas as pd
import textwrap
import tkinter.font as tkFont
import matplotlib.pyplot as plt
import numpy as np  # 用於計算角度與座標

# 設定 matplotlib 使用支援中文的字型與正確顯示負號
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

# ========================
# 版本及作者資訊設定 (更新至 1.0.11)
# ========================
CURRENT_VERSION = "1.0.11"
UPDATE_LOG = """版本更新紀錄：
1.0.0 - 初始版本。
1.0.1 - 修正部份錯誤，增加查詢功能。
1.0.2 - 加入水平捲軸功能。
1.0.3 - 加入版本更新記錄及作者資訊。
1.0.4 - 增加圖表分析功能：年度趨勢、成本差異、廠商分佈、管銷成本佔比分析，並整合至『資料分析』分頁，同時在成本差異直條圖與散點圖上加入數據標籤。
1.0.5 - 移除成本差異與效益分析、管銷成本佔比分析功能。
1.0.6 - 移除各廠商契約來價分析功能，廠商與市場分佈分析僅保留各廠商專案數比例（圓餅圖）。
1.0.7 - 調整各廠商專案數比例圓餅圖，利用引線標註廠商名稱，將標籤放置於左右兩側，並在標籤前顯示百分比。
1.0.8 - 將各扇區的標籤固定放置在視窗最左右兩側（分別 x=-1.3 與 x=+1.3），並垂直均分排列。
1.0.9 - 調整專案管理頁面資料顯示視窗的列高 (rowheight) 為 80，以避免工地名稱多行顯示時文字被遮蔽。
1.0.10 - 為資料顯示視窗加入交替行背景色。
1.0.11 - 修改刪除專案功能：可多重選取後一次刪除。
"""
AUTHOR = "KIM"

def show_about_info():
    info = (
        f"程式名稱：工程專案資料庫\n"
        f"目前版本：{CURRENT_VERSION}\n"
        f"作者：{AUTHOR}\n\n"
        f"更新紀錄：\n{UPDATE_LOG}"
    )
    messagebox.showinfo("版本資訊", info)

# ========================
# 建立主視窗
# ========================
root = tk.Tk()
root.title("工程專案資料庫")
root.geometry("1100x700")  # 調整視窗大小

# 加入選單列
menubar = tk.Menu(root)
about_menu = tk.Menu(menubar, tearoff=0)
about_menu.add_command(label="版本資訊", command=show_about_info)
menubar.add_cascade(label="關於", menu=about_menu)
root.config(menu=menubar)

# 設定 Treeview style，調整列高為 80
style = ttk.Style()
style.configure("Treeview", rowheight=80)

# ========================
# 資料庫及功能函式定義
# ========================
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

def add_project():
    try:
        contract_price = float(entry_contract.get().replace(',', ''))
        execution_budget = float(entry_execution.get().replace(',', ''))
        contractor_price = float(entry_contractor_price.get().replace(',', ''))
        indirect_cost = contract_price - execution_budget
    except ValueError:
        messagebox.showwarning("警告", "請輸入有效的數字！")
        return

    values = [
        entry_year.get(), 
        entry_site.get(), 
        entry_project.get(), 
        contract_price, 
        execution_budget, 
        contractor_price, 
        indirect_cost, 
        entry_contractor.get(), 
        entry_remarks.get()
    ]
    if not all(values[:3]):
        messagebox.showwarning("警告", "請填寫必要的欄位！")
        return

    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO projects (year, site_name, project_name, contract_price, 
        execution_budget, contractor_price, indirect_cost, contractor, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, values)
    conn.commit()
    conn.close()
    messagebox.showinfo("成功", "專案已新增")
    clear_entries()
    refresh_table()

def load_project():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("警告", "請選擇要編輯的專案")
        return
    item = tree.item(selected)
    values = item['values']
    clear_entries()
    entry_year.insert(0, values[1])
    entry_site.insert(0, values[2].replace("\n", ""))
    entry_project.insert(0, values[3])
    entry_contract.insert(0, values[4])
    entry_execution.insert(0, values[6])
    entry_contractor_price.insert(0, values[7])
    entry_contractor.insert(0, values[8])
    entry_remarks.insert(0, values[9] if values[9] else "")
    btn_update.config(state=tk.NORMAL)
    btn_add.config(state=tk.DISABLED)

def update_project():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("警告", "請選擇要更新的專案")
        return
    item = tree.item(selected)
    project_id = item['values'][0]
    try:
        contract_price = float(entry_contract.get().replace(',', ''))
        execution_budget = float(entry_execution.get().replace(',', ''))
        contractor_price = float(entry_contractor_price.get().replace(',', ''))
        indirect_cost = contract_price - execution_budget
    except ValueError:
        messagebox.showwarning("警告", "請輸入有效的數字！")
        return
    values = [
        entry_year.get(), 
        entry_site.get(), 
        entry_project.get(), 
        contract_price, 
        execution_budget, 
        contractor_price, 
        indirect_cost, 
        entry_contractor.get(), 
        entry_remarks.get(), 
        project_id
    ]
    if not all(values[:3]):
        messagebox.showwarning("警告", "請填寫必要的欄位！")
        return
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE projects 
        SET year=?, site_name=?, project_name=?, contract_price=?, 
            execution_budget=?, contractor_price=?, indirect_cost=?, contractor=?, remarks=?
        WHERE id=?
    """, values)
    conn.commit()
    conn.close()
    messagebox.showinfo("成功", "專案已更新")
    clear_entries()
    refresh_table()
    btn_update.config(state=tk.DISABLED)
    btn_add.config(state=tk.NORMAL)

def clear_entries():
    entry_year.delete(0, tk.END)
    entry_site.delete(0, tk.END)
    entry_project.delete(0, tk.END)
    entry_contract.delete(0, tk.END)
    entry_execution.delete(0, tk.END)
    entry_contractor_price.delete(0, tk.END)
    entry_contractor.delete(0, tk.END)
    entry_remarks.delete(0, tk.END)
    btn_update.config(state=tk.DISABLED)
    btn_add.config(state=tk.NORMAL)

def auto_adjust_columns():
    font = tkFont.Font()
    for col in columns:
        if col == "ID":
            desired_max = 50
        elif col == "年度":
            desired_max = 80
        elif col == "工地名稱":
            tree.column(col, width=150)
            continue
        elif col == "承攬項目":
            desired_max = 100
        else:
            desired_max = None
        max_width = font.measure(col)
        for child in tree.get_children():
            cell_text = tree.set(child, col)
            width = font.measure(cell_text)
            if width > max_width:
                max_width = width
        if desired_max is not None:
            tree.column(col, width=min(max_width+10, desired_max))
        else:
            tree.column(col, width=max_width+10)

def refresh_table():
    for item in tree.get_children():
        tree.delete(item)
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    for idx, row in enumerate(cursor.fetchall()):
        formatted_contract_price = f"{row[4]:,.2f}" if row[4] is not None else ""
        formatted_execution_budget = f"{row[5]:,.2f}" if row[5] is not None else ""
        formatted_contractor_price = f"{row[6]:,.2f}" if row[6] is not None else ""
        formatted_indirect_cost = f"{row[7]:,.2f}" if row[7] is not None else ""
        wrapped_site = textwrap.fill(row[2], width=15)
        tag = "evenrow" if idx % 2 == 0 else "oddrow"
        tree.insert("", "end", values=(
            row[0],
            row[1],
            wrapped_site,
            row[3],
            formatted_contract_price,
            formatted_indirect_cost,
            formatted_execution_budget,
            formatted_contractor_price,
            row[8],
            row[9]
        ), tags=(tag,))
    conn.close()
    auto_adjust_columns()

def query_projects():
    year = entry_query_year.get().strip()
    site = entry_query_site.get().strip()
    project = entry_query_project.get().strip()
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
    for item in tree.get_children():
        tree.delete(item)
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    for idx, row in enumerate(rows):
        formatted_contract_price = f"{row[4]:,.2f}" if row[4] is not None else ""
        formatted_execution_budget = f"{row[5]:,.2f}" if row[5] is not None else ""
        formatted_contractor_price = f"{row[6]:,.2f}" if row[6] is not None else ""
        formatted_indirect_cost = f"{row[7]:,.2f}" if row[7] is not None else ""
        wrapped_site = textwrap.fill(row[2], width=15)
        tag = "evenrow" if idx % 2 == 0 else "oddrow"
        tree.insert("", "end", values=(
            row[0],
            row[1],
            wrapped_site,
            row[3],
            formatted_contract_price,
            formatted_indirect_cost,
            formatted_execution_budget,
            formatted_contractor_price,
            row[8],
            row[9]
        ), tags=(tag,))
    auto_adjust_columns()

def delete_project():
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("警告", "請選擇要刪除的專案")
        return
    if messagebox.askyesno("確認", "確定要刪除選定的專案嗎？"):
        conn = sqlite3.connect("projects.db")
        cursor = conn.cursor()
        for item in selected_items:
            project_id = tree.item(item)['values'][0]
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("成功", "選定的專案已刪除")
        clear_entries()
        refresh_table()

def export_excel():
    conn = sqlite3.connect("projects.db")
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    df.columns = ["ID", "年度", "工地名稱", "承攬項目", "契約來價(未稅)", "執行預算(未稅)", "廠商發包價(未稅)", "管銷(契約間接費用)", "廠商", "備註"]
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
    if file_path:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("成功", "資料已匯出至 Excel")

def import_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
    if not file_path:
        return
    try:
        df = pd.read_excel(file_path)
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
        required_columns = ["年度", "工地名稱", "承攬項目"]
        for req in required_columns:
            if req not in df.columns:
                messagebox.showerror("錯誤", f"Excel檔案缺少必要欄位：{req}")
                return
        df = df.rename(columns=chinese_to_eng)
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        conn = sqlite3.connect("projects.db")
        cursor = conn.cursor()
        success_count = 0
        error_count = 0
        for _, row in df.iterrows():
            try:
                if pd.isna(row['year']) or pd.isna(row['site_name']) or pd.isna(row['project_name']):
                    error_count += 1
                    continue
                year_val = row['year']
                site_val = row['site_name']
                project_val = row['project_name']
                contract_price_val = 0 if pd.isna(row.get('contract_price', 0)) else row.get('contract_price', 0)
                execution_budget_val = 0 if pd.isna(row.get('execution_budget', 0)) else row.get('execution_budget', 0)
                contractor_price_val = 0 if pd.isna(row.get('contractor_price', 0)) else row.get('contractor_price', 0)
                if 'indirect_cost' in row and pd.notna(row['indirect_cost']):
                    indirect_cost_val = row['indirect_cost']
                else:
                    indirect_cost_val = contract_price_val - execution_budget_val
                contractor_val = row.get('contractor', "")
                remarks_val = row.get('remarks', "")
                values = [
                    year_val,
                    site_val,
                    project_val,
                    contract_price_val,
                    execution_budget_val,
                    contractor_price_val,
                    indirect_cost_val,
                    contractor_val,
                    remarks_val
                ]
                cursor.execute("""
                    INSERT INTO projects (year, site_name, project_name, contract_price, 
                    execution_budget, contractor_price, indirect_cost, contractor, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, values)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error inserting row: {e}")
        conn.commit()
        conn.close()
        msg = f"匯入完成\n成功: {success_count} 筆\n"
        if error_count > 0:
            msg += f"失敗: {error_count} 筆"
        messagebox.showinfo("匯入結果", msg)
        refresh_table()
    except Exception as e:
        messagebox.showerror("錯誤", f"匯入過程發生錯誤：{str(e)}")

# ========================
# 分析功能函式
# ========================

# 1. 年度趨勢分析（直條圖上加數據標籤）
def analyze_yearly_trend():
    conn = sqlite3.connect("projects.db")
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    df["contract_price"] = pd.to_numeric(df["contract_price"], errors="coerce")
    yearly_sum = df.groupby("year")["contract_price"].sum()
    yearly_count = df.groupby("year")["id"].count()
    
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    
    bars1 = ax[0].bar(yearly_sum.index, yearly_sum.values, color="skyblue")
    ax[0].set_title("每年度總契約來價")
    ax[0].set_xlabel("年度")
    ax[0].set_ylabel("契約來價")
    for bar in bars1:
        height = bar.get_height()
        ax[0].text(bar.get_x() + bar.get_width()/2, height, f"{height:,.0f}", ha="center", va="bottom", fontsize=9, color="black")
    
    bars2 = ax[1].bar(yearly_count.index, yearly_count.values, color="salmon")
    ax[1].set_title("每年度專案數量")
    ax[1].set_xlabel("年度")
    ax[1].set_ylabel("專案數量")
    for bar in bars2:
        height = bar.get_height()
        ax[1].text(bar.get_x() + bar.get_width()/2, height, f"{int(height)}", ha="center", va="bottom", fontsize=9, color="black")
    
    plt.tight_layout()
    plt.show()

# 2. 廠商與市場分佈分析（圓餅圖：各廠商專案數比例，標籤固定放置於視窗左右兩側垂直排列，貼齊邊緣）
def analyze_contractor_distribution():
    conn = sqlite3.connect("projects.db")
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    contractor_count = df.groupby("contractor")["id"].count()
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
        vendor = contractor_count.index[i]
        group = "right" if x >= 0 else "left"
        labels_info.append({
            "vendor": vendor,
            "percentage": percentage,
            "wedge_center": (x, y),
            "group": group
        })
    
    # 分組
    left_labels = [d for d in labels_info if d["group"] == "left"]
    right_labels = [d for d in labels_info if d["group"] == "right"]
    left_labels.sort(key=lambda d: d["wedge_center"][1], reverse=True)
    right_labels.sort(key=lambda d: d["wedge_center"][1], reverse=True)
    
    # 為左右兩組分配固定垂直位置：左右固定 x 座標分別 -1.3 與 +1.3，y 均勻分佈
    def assign_y_positions(group, side):
        n = len(group)
        if n == 0:
            return
        ys = np.linspace(0.9, -0.9, n)
        fixed_x = -1.3 if side=="left" else 1.3
        for i, d in enumerate(group):
            d["label_pos"] = (fixed_x, ys[i])
    assign_y_positions(left_labels, "left")
    assign_y_positions(right_labels, "right")
    
    # 標註各標籤：標籤內容為「百分比 廠商名稱」
    for d in left_labels + right_labels:
        x, y = d["wedge_center"]
        label_x, label_y = d["label_pos"]
        label_text = f"{d['percentage']:.1f}% {d['vendor']}"
        ha = "right" if d["group"]=="left" else "left"
        ax.annotate(label_text, xy=(x, y), xytext=(label_x, label_y),
                    horizontalalignment=ha, verticalalignment="center",
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"),
                    fontsize=10)
    plt.tight_layout()
    plt.show()

# ========================
# 建立 Notebook 分頁
# ========================
notebook = ttk.Notebook(root)
tab_manage = ttk.Frame(notebook)
tab_analysis = ttk.Frame(notebook)
notebook.add(tab_manage, text="專案管理")
notebook.add(tab_analysis, text="資料分析")
notebook.pack(fill=tk.BOTH, expand=True)

# ========================
# 專案管理分頁內容
# ========================
frame_inputs = tk.Frame(tab_manage)
frame_inputs.pack(pady=10)
tk.Label(frame_inputs, text="年度", anchor="w").grid(row=0, column=0, sticky="w")
tk.Label(frame_inputs, text="工地名稱", anchor="w").grid(row=0, column=2, sticky="w")
tk.Label(frame_inputs, text="承攬項目", anchor="w").grid(row=1, column=0, sticky="w")
tk.Label(frame_inputs, text="契約來價(未稅)", anchor="w").grid(row=1, column=2, sticky="w")
tk.Label(frame_inputs, text="執行預算(未稅)", anchor="w").grid(row=2, column=0, sticky="w")
tk.Label(frame_inputs, text="廠商發包價(未稅)", anchor="w").grid(row=2, column=2, sticky="w")
tk.Label(frame_inputs, text="廠商", anchor="w").grid(row=3, column=0, sticky="w")
tk.Label(frame_inputs, text="備註", anchor="w").grid(row=3, column=2, sticky="w")
entry_year = tk.Entry(frame_inputs)
entry_year.grid(row=0, column=1)
entry_site = tk.Entry(frame_inputs)
entry_site.grid(row=0, column=3)
entry_project = tk.Entry(frame_inputs)
entry_project.grid(row=1, column=1)
entry_contract = tk.Entry(frame_inputs)
entry_contract.grid(row=1, column=3)
entry_execution = tk.Entry(frame_inputs)
entry_execution.grid(row=2, column=1)
entry_contractor_price = tk.Entry(frame_inputs)
entry_contractor_price.grid(row=2, column=3)
entry_contractor = tk.Entry(frame_inputs)
entry_contractor.grid(row=3, column=1)
entry_remarks = tk.Entry(frame_inputs)
entry_remarks.grid(row=3, column=3)

frame_buttons = tk.Frame(tab_manage)
frame_buttons.pack()
btn_add = tk.Button(frame_buttons, text="新增專案", command=add_project)
btn_add.pack(side=tk.LEFT, padx=5)
btn_update = tk.Button(frame_buttons, text="修改專案", command=update_project, state=tk.DISABLED)
btn_update.pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="載入編輯", command=load_project).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="刪除專案", command=delete_project).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="匯出Excel", command=export_excel).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="匯入Excel", command=import_excel).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="全部專案", command=refresh_table).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="清空欄位", command=clear_entries).pack(side=tk.LEFT, padx=5)

frame_query = tk.Frame(tab_manage)
frame_query.pack(pady=10)
tk.Label(frame_query, text="查詢 - 年度", anchor="w").grid(row=0, column=0, sticky="w")
entry_query_year = tk.Entry(frame_query)
entry_query_year.grid(row=0, column=1)
tk.Label(frame_query, text="查詢 - 工地名稱", anchor="w").grid(row=0, column=2, sticky="w")
entry_query_site = tk.Entry(frame_query)
entry_query_site.grid(row=0, column=3)
tk.Label(frame_query, text="查詢 - 承攬項目", anchor="w").grid(row=0, column=4, sticky="w")
entry_query_project = tk.Entry(frame_query)
entry_query_project.grid(row=0, column=5)
btn_query = tk.Button(frame_query, text="查詢專案", command=query_projects)
btn_query.grid(row=0, column=6, padx=5)
btn_reset_query = tk.Button(frame_query, text="重置查詢", command=refresh_table)
btn_reset_query.grid(row=0, column=7, padx=5)

frame_table = tk.Frame(tab_manage)
frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
columns = ("ID", "年度", "工地名稱", "承攬項目", "契約來價", "管銷(契約間接費用)", "執行預算", "廠商發包價", "廠商", "備註")
tree = ttk.Treeview(frame_table, columns=columns, show="headings", selectmode="extended")
tree.heading("ID", text="ID")
tree.column("ID", width=50, anchor="center")
tree.heading("年度", text="年度")
tree.column("年度", width=80)
tree.heading("工地名稱", text="工地名稱")
tree.column("工地名稱", width=150)
tree.heading("承攬項目", text="承攬項目")
tree.column("承攬項目", width=100)
tree.heading("契約來價", text="契約來價")
tree.column("契約來價", width=120, anchor="e")
tree.heading("管銷(契約間接費用)", text="管銷(契約間接費用)")
tree.column("管銷(契約間接費用)", width=150, anchor="e")
tree.heading("執行預算", text="執行預算")
tree.column("執行預算", width=120, anchor="e")
tree.heading("廠商發包價", text="廠商發包價")
tree.column("廠商發包價", width=120, anchor="e")
tree.heading("廠商", text="廠商")
tree.column("廠商", width=100)
tree.heading("備註", text="備註")
tree.column("備註", width=200)
v_scrollbar = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=tree.yview)
v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
h_scrollbar = ttk.Scrollbar(frame_table, orient=tk.HORIZONTAL, command=tree.xview)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 設定交替列背景色
tree.tag_configure("evenrow", background="lightblue")
tree.tag_configure("oddrow", background="white")

# ========================
# 資料分析分頁內容
# ========================
frame_analysis = tk.Frame(tab_analysis)
frame_analysis.pack(pady=20)
lf_analysis = tk.LabelFrame(frame_analysis, text="圖表分析功能", padx=10, pady=10)
lf_analysis.pack()
btn_yearly = tk.Button(lf_analysis, text="年度趨勢分析", width=25, command=analyze_yearly_trend)
btn_yearly.grid(row=0, column=0, padx=5, pady=5)
btn_contractor = tk.Button(lf_analysis, text="廠商與市場分佈分析", width=25, command=analyze_contractor_distribution)
btn_contractor.grid(row=0, column=1, padx=5, pady=5)

# ========================
# 初始化資料庫與表格顯示
# ========================
init_db()
refresh_table()

root.mainloop()
