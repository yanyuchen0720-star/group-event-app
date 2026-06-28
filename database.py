import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==========================================
# 🌟 初始化 Supabase 雲端客戶端
# ==========================================
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ==========================================
# 1. 活動相關操作 (Events)
# ==========================================
def load_events():
    res = supabase.table("events").select("*").execute()
    # 如果雲端沒資料，回傳空的 DataFrame 並帶有預期中文欄位，防止 UI 報錯
    if not res.data:
        return pd.DataFrame(columns=["活動代碼", "主揪帳號", "主揪", "活動名稱", "開始日期", "結束日期"])
    
    # 讀取雲端資料並將英文欄位名完美對應回原本的中文 DataFrame 結構
    df = pd.DataFrame(res.data)
    df = df.rename(columns={
        "event_code": "活動代碼",
        "creator_account": "主揪帳號",
        "creator_name": "主揪",
        "event_name": "活動名稱",
        "start_date": "開始日期",
        "end_date": "結束日期"
    })
    return df

def save_event(new_code, user_account, organizer_name, event_name, start_date, end_date):
    supabase.table("events").insert({
        "event_code": new_code,
        "creator_account": user_account,
        "creator_name": organizer_name,
        "event_name": event_name,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }).execute()

def delete_event(current_code):
    # 連鎖刪除：刪除活動本身，同時刪除該活動的所有請假回應
    supabase.table("events").delete().eq("event_code", current_code).execute()
    supabase.table("responses").delete().eq("event_code", current_code).execute()

# ==========================================
# 2. 回應相關操作 (Responses)
# ==========================================
def load_responses():
    res = supabase.table("responses").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["活動代碼", "參與者帳號", "姓名", "沒空日期"])
    
    df = pd.DataFrame(res.data)
    df = df.rename(columns={
        "event_code": "活動代碼",
        "user_account": "參與者帳號",
        "user_name": "姓名",
        "busy_date": "沒空日期"
    })
    return df

def save_response(current_code, user_account, user_name, selected_dates):
    # 先清除該使用者在這個活動的舊請假紀錄
    supabase.table("responses").delete().eq("event_code", current_code).eq("user_account", user_account).execute()
    
    # 寫入新紀錄
    if not selected_dates:
        # 如果完全沒有勾選沒空日期，寫入一筆「完全有空」
        supabase.table("responses").insert({
            "event_code": current_code,
            "user_account": user_account,
            "user_name": user_name,
            "busy_date": "完全有空"
        }).execute()
    else:
        # 多筆日期一次打包整批寫入 (Bulk Insert)
        rows = [{
            "event_code": current_code,
            "user_account": user_account,
            "user_name": user_name,
            "busy_date": d
        } for d in selected_dates]
        supabase.table("responses").insert(rows).execute()

def leave_event(current_code, user_account):
    supabase.table("responses").delete().eq("event_code", current_code).eq("user_account", user_account).execute()

# ==========================================
# 3. 會員相關操作 (Users)
# ==========================================
def load_users():
    res = supabase.table("users").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["帳號", "密碼雜湊", "顯示名稱"])
    
    df = pd.DataFrame(res.data)
    df = df.rename(columns={
        "username": "帳號",
        "password_hash": "密碼雜湊",
        "display_name": "顯示名稱"
    })
    return df

def register_user(username, password_hash, display_name):
    try:
        supabase.table("users").insert({
            "username": username,
            "password_hash": password_hash,
            "display_name": display_name
        }).execute()
        return True
    except Exception as e:
        # 如果帳號重複(Primary Key 衝突)，Supabase 會拋出異常，此時回傳註冊失敗
        return False