import streamlit as st
import requests
from core import database as db
from utils import helpers
from views import auth_views, event_views, form_views
from streamlit_cookies_manager import CookieManager 

# ==========================================
# 🌟 頁面基本設定 (必須是第一個 st. 指令)
# ==========================================
st.set_page_config(page_title="揪團時間表", page_icon="📅")

# ==========================================
# 🌟 針對手機版月曆的 CSS 終極響應式修正
# ==========================================
st.markdown("""
<style>
/* 當螢幕寬度小於 640px (涵蓋大部分手機直放尺寸) 時觸發 */
@media (max-width: 640px) {
    /* 1. 外層容器：強制橫向排列，並且縮小欄位間的縫隙 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important; 
    }
    
    /* 2. 終極殺招：內層的 7 個小欄位 */
    /* Streamlit 在極窄螢幕會強制子欄位變成 100%，我們必須把它壓回 1/7 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) > div {
        width: 14.28% !important;
        min-width: 0 !important; /* 徹底覆寫預設的 min-width: 100% */
        flex: 1 1 auto !important;
    }
    
    /* 3. 按鈕的終極瘦身：拿掉 padding、縮小字體以塞進狹窄的直放螢幕 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) button {
        padding: 0 !important;
        font-size: 13px !important; 
        min-height: 2.2rem !important;
    }
    
    /* 4. 上方星期幾 (一, 二, 三...) 的字體微調 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) div[data-testid="stMarkdownContainer"] p {
        font-size: 12px !important;
        margin-bottom: 0.2rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌟 Cookie 初始化 (正確寫法：直接宣告，不要放進 session_state)
# ==========================================
# CookieManager 每次執行都必須在頂層宣告，才會正常驅動底層元件
cookies = CookieManager()

if not cookies.ready():
    # 加上一個載入提示，如果真的需要讀取零點幾秒，至少不會是白屏
    st.markdown("<h4 style='text-align: center; color: gray; margin-top: 30vh;'>🍪 正在讀取登入狀態...</h4>", unsafe_allow_html=True)
    st.stop()

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
if "force_reload_form" not in st.session_state:
    st.session_state.force_reload_form = False

# ==========================================
# 🌟 自動登入攔截：檢查瀏覽器 Cookie 是否有紀錄
# ==========================================
if not st.session_state.logged_in and cookies.get("auto_login_user"):
    cached_user = cookies.get("auto_login_user")
    users_df = db.load_users()
    
    # 確認資料庫中真的有這個帳號
    if cached_user in users_df["帳號"].values:
        user_data = users_df[users_df["帳號"] == cached_user].iloc[0]
        st.session_state.logged_in = True
        st.session_state.username = cached_user
        st.session_state.display_name = user_data["顯示名稱"]
        
        # 如果使用者原本停在登入頁，就自動導向首頁
        if st.session_state.page == "login":
            st.session_state.page = "home"

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
                    db.register_user(user_email, helpers.hash_password("google_oauth_dummy"), user_name)
                
                st.session_state.logged_in = True
                st.session_state.username = user_email
                st.session_state.display_name = user_name
                
                # 🌟 Google 登入成功後，將帳號寫入 Cookie
                cookies["auto_login_user"] = user_email
                cookies.save()
                
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

# ==========================================
# 網頁路由 (Router)：分配工作給對應的模組
# ==========================================
if st.session_state.logged_in:
    # 傳入 cookies 給側邊欄，為了實現「登出並刪除 Cookie」功能
    auth_views.render_sidebar(cookies)

if not st.session_state.logged_in:
    # 傳入 cookies 給登入畫面，為了實現「登入後儲存 Cookie」功能
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