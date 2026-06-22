import streamlit as st
import requests
from core import database as db
from utils import helpers
from views import auth_views, event_views, form_views
from streamlit_cookies_manager import CookieManager 

# ==========================================
# 🌟 頁面基本設定
# ==========================================
st.set_page_config(page_title="揪團時間表", page_icon="📅")

st.markdown("""
<style>
@media (max-width: 640px) {
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important; 
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) > div {
        width: 14.28% !important;
        min-width: 0 !important; 
        flex: 1 1 auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) button {
        padding: 0 !important;
        font-size: 13px !important; 
        min-height: 2.2rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) div[data-testid="stMarkdownContainer"] p {
        font-size: 12px !important;
        margin-bottom: 0.2rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# Cookie 初始化
# ==========================================
cookies = CookieManager()
if not cookies.ready():
    st.markdown("<h4 style='text-align: center; color: gray; margin-top: 30vh;'>🍪 正在讀取登入狀態...</h4>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 讀取金鑰
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
# 狀態管理初始化
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
if "force_reload_form" not in st.session_state:
    st.session_state.force_reload_form = False

# 自動登入攔截
if not st.session_state.logged_in and cookies.get("auto_login_user"):
    cached_user = cookies.get("auto_login_user")
    users_df = db.load_users()
    if cached_user in users_df["帳號"].values:
        user_data = users_df[users_df["帳號"] == cached_user].iloc[0]
        st.session_state.logged_in = True
        st.session_state.username = cached_user
        st.session_state.display_name = user_data["顯示名稱"]
        if st.session_state.page == "login":
            st.session_state.page = "home"

# ==========================================
# 🌟 網址參數捕捉 (修正「跳回首頁卡死」的失憶症)
# ==========================================
# 🌟 先把從 Google OAuth 帶回來的 state (活動代碼) 撿回來
if "state" in st.query_params:
    st.session_state.current_event_code = st.query_params["state"]

if "code" in st.query_params:
    url_code = st.query_params["code"]
    
    # 情況 A：收到 5 碼的邀請碼
    if len(url_code) == 5:
        st.session_state.current_event_code = url_code
        
        # 🌟 關鍵防呆：確認「已經登入成功」，才把網址的 code 清空並跳轉！
        if st.session_state.logged_in:
            st.query_params.clear()
            st.session_state.page = "fill_form"
            st.rerun() 
            
    # 情況 B：收到 Google 驗證碼 (跳轉回來)
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
                    db.register_user(user_email, helpers.hash_password("google_oauth_dummy"), user_name)
                
                st.session_state.logged_in = True
                st.session_state.username = user_email
                st.session_state.display_name = user_name
                
                cookies["auto_login_user"] = user_email
                cookies.save()
                
                st.query_params.clear() 
                
                # 🌟 因為前面攔截了 state，這裡就不會是空的，能順利跳到請假表了！
                if st.session_state.current_event_code:
                    st.session_state.page = "fill_form"
                else:
                    st.session_state.page = "home"
                st.rerun()
            else:
                st.error("獲取 Google 帳號資料失敗！")
        else:
            st.error("Google 登入驗證過期，請重新點擊按鈕！")

# ==========================================
# 網頁路由
# ==========================================
if st.session_state.logged_in:
    auth_views.render_sidebar(cookies)

if not st.session_state.logged_in:
    auth_views.render_login(CLIENT_ID, REDIRECT_URI, cookies)
elif st.session_state.page == "home":
    event_views.render_home()
elif st.session_state.page == "create_event":
    event_views.render_create_event()
elif st.session_state.page == "join_event":
    event_views.render_join_event()
elif st.session_state.page == "fill_form":
    form_views.render_fill_form(REDIRECT_URI)
elif st.session_state.page == "view_results":
    form_views.render_view_results()