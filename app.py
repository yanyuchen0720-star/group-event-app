import streamlit as st
import requests
import database as db
import utils
import views  # 引入我們剛剛建立的 UI 模組！

# ==========================================
# 讀取 Google 金鑰
# ==========================================
try:
    CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
except:
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    REDIRECT_URI = ""

# ==========================================
# 狀態管理初始化 (大腦記憶體)
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "current_event_code" not in st.session_state:
    st.session_state.current_event_code = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "display_name" not in st.session_state:
    st.session_state.display_name = ""
if "form_event_code" not in st.session_state:
    st.session_state.form_event_code = ""
if "form_selected_dates" not in st.session_state:
    st.session_state.form_selected_dates = []
if "form_default_name" not in st.session_state:
    st.session_state.form_default_name = ""

# ==========================================
# 網址參數捕捉 (Google 登入與邀請碼攔截)
# ==========================================
if "code" in st.query_params:
    url_code = st.query_params["code"]
    if len(url_code) == 5:
        st.session_state.current_event_code = url_code
        if st.session_state.logged_in:
            st.session_state.page = "fill_form"
    elif len(url_code) > 20 and not st.session_state.logged_in:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": url_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        res = requests.post(token_url, data=data)
        if res.status_code == 200:
            access_token = res.json().get("access_token")
            user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_res = requests.get(user_info_url, headers=headers)
            
            if user_res.status_code == 200:
                user_info = user_res.json()
                user_email = user_info.get("email")
                user_name = user_info.get("name")
                
                users_df = db.load_users()
                if user_email not in users_df["帳號"].values:
                    db.register_user(user_email, utils.hash_password("google_oauth_dummy"), user_name)
                
                st.session_state.logged_in = True
                st.session_state.username = user_email
                st.session_state.display_name = user_name
                
                if st.session_state.current_event_code:
                    st.session_state.page = "fill_form"
                else:
                    st.session_state.page = "home"
                
                st.query_params.clear()
                st.rerun()
            else:
                st.error("獲取 Google 帳號資料失敗！")
        else:
            st.error("Google 登入驗證過期，請重新點擊按鈕！")

st.set_page_config(page_title="揪團時間表", page_icon="📅")

# ==========================================
# 網頁路由 (Router)：分配工作給 views.py
# ==========================================
if st.session_state.logged_in:
    views.render_sidebar()

if not st.session_state.logged_in:
    views.render_login(CLIENT_ID, REDIRECT_URI)
elif st.session_state.page == "home":
    views.render_home()
elif st.session_state.page == "create_event":
    views.render_create_event()
elif st.session_state.page == "join_event":
    views.render_join_event()
elif st.session_state.page == "fill_form":
    views.render_fill_form(REDIRECT_URI)
elif st.session_state.page == "view_results":
    views.render_view_results()