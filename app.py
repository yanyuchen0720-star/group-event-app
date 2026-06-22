import streamlit as st
import requests
from core import database as db
from utils import helpers
# 🌟 修正點 1：將拆分出來的三個 UI 小弟都引入
from views import auth_views, event_views, form_views 

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
# 🌟 新增：針對手機版月曆的 CSS 強制修正
# ==========================================
st.markdown("""
<style>
/* 當螢幕寬度小於 640px (手機) 時觸發 */
@media (max-width: 640px) {
    /* 利用 :has 選擇器，"只"針對擁有 7 個子元素(即月曆的7天)的水平區塊強制不換行 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
    }
    
    /* 縮小手機版按鈕的內邊距與字體，確保 7 個按鈕塞得進螢幕 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) button {
        padding: 0.2rem 0rem !important;
        font-size: 14px !important;
        min-height: 2.5rem !important;
    }
    
    /* 縮小上方星期幾 (一, 二, 三...) 的字體 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) div[data-testid="stMarkdownContainer"] p {
        font-size: 13px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 網頁路由 (Router)：分配工作給對應的模組
# ==========================================
if st.session_state.logged_in:
    # 側邊欄由 auth_views 負責
    auth_views.render_sidebar()

if not st.session_state.logged_in:
    # 登入頁面由 auth_views 負責
    auth_views.render_login(CLIENT_ID, REDIRECT_URI)
elif st.session_state.page == "home":
    # 首頁由 event_views 負責
    event_views.render_home()
elif st.session_state.page == "create_event":
    # 建立揪團由 event_views 負責
    event_views.render_create_event()
elif st.session_state.page == "join_event":
    # 加入揪團由 event_views 負責
    event_views.render_join_event()
elif st.session_state.page == "fill_form":
    # 填寫表單由 form_views 負責
    form_views.render_fill_form(REDIRECT_URI)
elif st.session_state.page == "view_results":
    # 看結果也是由 form_views 負責
    form_views.render_view_results()