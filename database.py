import pandas as pd
import os

EVENTS_FILE = "events_data.csv"
RESPONSES_FILE = "responses_data.csv"
USERS_FILE = "users_data.csv"

def load_events():
    if not os.path.exists(EVENTS_FILE):
        # 升級：多加一欄「主揪帳號」
        return pd.DataFrame(columns=["活動代碼", "主揪帳號", "主揪", "活動名稱", "開始日期", "結束日期"])
    return pd.read_csv(EVENTS_FILE)

def load_responses():
    if not os.path.exists(RESPONSES_FILE):
        # 升級：多加一欄「參與者帳號」
        return pd.DataFrame(columns=["活動代碼", "參與者帳號", "姓名", "沒空日期"])
    return pd.read_csv(RESPONSES_FILE)

# 升級：存檔時，一併把 user_account (帳號) 存進去
def save_event(new_code, user_account, organizer_name, event_name, start_date, end_date):
    events_df = load_events()
    new_event = pd.DataFrame({
        "活動代碼": [new_code],
        "主揪帳號": [user_account],
        "主揪": [organizer_name],
        "活動名稱": [event_name],
        "開始日期": [start_date],
        "結束日期": [end_date]
    })
    events_df = pd.concat([events_df, new_event], ignore_index=True)
    events_df.to_csv(EVENTS_FILE, index=False)

# 升級：存檔時，一併把 user_account 存進去
def save_response(current_code, user_account, participant_name, selected_dates):
    responses_df = load_responses()
    if len(selected_dates) > 0:
        new_data = pd.DataFrame({
            "活動代碼": [current_code] * len(selected_dates),
            "參與者帳號": [user_account] * len(selected_dates),
            "姓名": [participant_name] * len(selected_dates),
            "沒空日期": selected_dates
        })
    else:
        new_data = pd.DataFrame({
            "活動代碼": [current_code],
            "參與者帳號": [user_account],
            "姓名": [participant_name],
            "沒空日期": ["完全有空"]
        })
    
    # 清除舊紀錄時，認「帳號」而不是認名字
    responses_df = responses_df[~((responses_df["活動代碼"] == current_code) & (responses_df["參與者帳號"] == user_account))]
    responses_df = pd.concat([responses_df, new_data], ignore_index=True)
    responses_df.to_csv(RESPONSES_FILE, index=False)

def delete_event(current_code):
    events_df = load_events()
    events_df = events_df[events_df["活動代碼"] != current_code]
    events_df.to_csv(EVENTS_FILE, index=False)
    
    responses_df = load_responses()
    responses_df = responses_df[responses_df["活動代碼"] != current_code]
    responses_df.to_csv(RESPONSES_FILE, index=False)

# 升級：退出活動時，用「帳號」來確認身分，確保不會刪到同名同姓的人
def leave_event(current_code, user_account):
    responses_df = load_responses()
    responses_df = responses_df[~((responses_df["活動代碼"] == current_code) & (responses_df["參與者帳號"] == user_account))]
    responses_df.to_csv(RESPONSES_FILE, index=False)

def load_users():
    if not os.path.exists(USERS_FILE):
        return pd.DataFrame(columns=["帳號", "密碼雜湊", "顯示名稱"])
    return pd.read_csv(USERS_FILE)

def register_user(username, password_hash, display_name):
    users_df = load_users()
    if username in users_df["帳號"].values:
        return False
    new_user = pd.DataFrame({
        "帳號": [username],
        "密碼雜湊": [password_hash],
        "顯示名稱": [display_name]
    })
    users_df = pd.concat([users_df, new_user], ignore_index=True)
    users_df.to_csv(USERS_FILE, index=False)
    return True