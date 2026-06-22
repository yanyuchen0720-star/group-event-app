import streamlit as st
import pandas as pd
from core import database as db
from utils import helpers

# ==========================================
# 側邊欄 (新增接收 cookies 參數，並處理登出刪除 Cookie)
# ==========================================
def render_sidebar(cookies):
    with st.sidebar:
        st.markdown(f"### 👋 嗨，{st.session_state.display_name}")
        st.caption(f"帳號：{st.session_state.username}")
        st.divider()
        st.markdown("### 📂 我的揪團")
        events_df = db.load_events()
        responses_df = db.load_responses()
        
        if not events_df.empty:
            created_events = events_df[events_df["主揪帳號"] == st.session_state.username]
            if not responses_df.empty:
                joined_codes = responses_df[responses_df["參與者帳號"] == st.session_state.username]["活動代碼"].unique()
                joined_events = events_df[events_df["活動代碼"].isin(joined_codes)]
                joined_events = joined_events[~joined_events["活動代碼"].isin(created_events["活動代碼"])]
            else:
                joined_events = pd.DataFrame()
        else:
            created_events = pd.DataFrame()
            joined_events = pd.DataFrame()
            
        if not created_events.empty:
            with st.expander("👑 我發起的", expanded=False):
                for _, row in created_events.iterrows():
                    code = row["活動代碼"]
                    name = row["活動名稱"]
                    col1, col2, col3 = st.columns([5, 1.5, 1.5])
                    with col1:
                        if st.button(f"{name}", key=f"c_go_{code}", use_container_width=True):
                            st.session_state.current_event_code = code
                            st.session_state.page = "view_results"
                            st.rerun()
                    with col2:
                        if st.button("❌", key=f"c_lv_{code}", help="刪除我的請假表 (退出)"):
                            db.leave_event(code, st.session_state.username)
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"c_del_{code}", help="徹底刪除這個活動"):
                            db.delete_event(code)
                            if st.session_state.current_event_code == code:
                                st.session_state.page = "home"
                                st.session_state.current_event_code = ""
                            st.rerun()
                            
        if not joined_events.empty:
            with st.expander("🙋 我加入的", expanded=False):
                for _, row in joined_events.iterrows():
                    code = row["活動代碼"]
                    name = row["活動名稱"]
                    col1, col2 = st.columns([5, 1.5])
                    with col1:
                        if st.button(f"{name}", key=f"j_go_{code}", use_container_width=True):
                            st.session_state.current_event_code = code
                            st.session_state.page = "view_results"
                            st.rerun()
                    with col2:
                        if st.button("❌", key=f"j_lv_{code}", help="刪除我的請假表 (退出)"):
                            db.leave_event(code, st.session_state.username)
                            if st.session_state.current_event_code == code:
                                st.session_state.page = "home"
                                st.session_state.current_event_code = ""
                            st.rerun()
                            
        if created_events.empty and joined_events.empty:
            st.info("目前還沒有紀錄喔！")

        st.divider()
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.display_name = ""
            
            # 🌟 登出時，把瀏覽器裡的 Cookie 銷毀
            if "auto_login_user" in cookies:
                del cookies["auto_login_user"]
                cookies.save()
                
            st.session_state.page = "login"
            st.rerun()

# ==========================================
# 畫面 0：登入與註冊門神 (新增接收 cookies 參數，並處理登入寫入 Cookie)
# ==========================================
def render_login(CLIENT_ID, REDIRECT_URI, cookies):
    st.title("🔐 歡迎來到揪團神器")
    if CLIENT_ID:
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=openid%20email%20profile"
        st.link_button("🌐 使用 Google 帳號一鍵登入", auth_url, type="primary", use_container_width=True)
        st.divider()
        st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>或者使用傳統帳號密碼</p>", unsafe_allow_html=True)
        
    tab1, tab2 = st.tabs(["🔑 傳統登入", "📝 註冊新帳號"])
    with tab1:
        login_user = st.text_input("帳號", key="login_user")
        login_pass = st.text_input("密碼", type="password", key="login_pass")
        if st.button("登入"):
            users_df = db.load_users()
            if login_user in users_df["帳號"].values:
                user_data = users_df[users_df["帳號"] == login_user].iloc[0]
                if helpers.verify_password(user_data["密碼雜湊"], login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.display_name = user_data["顯示名稱"]
                    
                    # 🌟 傳統登入成功後，將帳號寫入 Cookie
                    cookies["auto_login_user"] = login_user
                    cookies.save()
                    
                    if st.session_state.current_event_code:
                        st.session_state.page = "fill_form"
                    else:
                        st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("密碼錯誤，請再試一次！")
            else:
                st.error("找不到這個帳號，請先註冊喔！")

    with tab2:
        reg_user = st.text_input("設定帳號 (英文數字)", key="reg_user")
        reg_name = st.text_input("顯示暱稱 (大家會看到這個名字)", key="reg_name")
        reg_pass = st.text_input("設定密碼", type="password", key="reg_pass")
        reg_pass2 = st.text_input("再次確認密碼", type="password", key="reg_pass2")
        if st.button("註冊"):
            if reg_user and reg_name and reg_pass:
                if reg_pass == reg_pass2:
                    hashed_pw = helpers.hash_password(reg_pass)
                    success = db.register_user(reg_user, hashed_pw, reg_name)
                    if success:
                        st.success("註冊成功！請切換到『登入』標籤頁進行登入。")
                    else:
                        st.error("這個帳號已經有人用了，換一個試試看吧！")
                else:
                    st.warning("兩次輸入的密碼不一樣喔！")
            else:
                st.warning("請填寫所有欄位！")
    st.stop()