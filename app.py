import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import utils

# ==========================================
# 狀態管理
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

if "code" in st.query_params and st.session_state.page == "home":
    st.session_state.page = "fill_form"
    st.session_state.current_event_code = st.query_params["code"]

st.set_page_config(page_title="揪團時間表", page_icon="📅")

# ==========================================
# 側邊欄
# ==========================================
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown(f"### 👋 嗨，{st.session_state.display_name}")
        st.caption(f"帳號：{st.session_state.username}")
        
        st.divider()
        st.markdown("### 📂 我的揪團")
        
        events_df = db.load_events()
        responses_df = db.load_responses()
        
        if not events_df.empty:
            # 升級：改用 "主揪帳號" 核對身分
            created_events = events_df[events_df["主揪帳號"] == st.session_state.username]
            if not responses_df.empty:
                # 升級：改用 "參與者帳號" 核對身分
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
                            # 退出時傳入自己的帳號
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
            st.info("目前還沒有紀錄喔！快去首頁建立吧。")

        st.divider()
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.display_name = ""
            st.session_state.page = "login"
            st.rerun()

# ==========================================
# 畫面 0：登入與註冊門神
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 歡迎來到揪團神器")
    tab1, tab2 = st.tabs(["🔑 登入", "📝 註冊新帳號"])
    
    with tab1:
        st.subheader("登入你的帳號")
        login_user = st.text_input("帳號", key="login_user")
        login_pass = st.text_input("密碼", type="password", key="login_pass")
        if st.button("登入", type="primary"):
            users_df = db.load_users()
            if login_user in users_df["帳號"].values:
                user_data = users_df[users_df["帳號"] == login_user].iloc[0]
                if utils.verify_password(user_data["密碼雜湊"], login_pass):
                    st.success("登入成功！")
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.display_name = user_data["顯示名稱"]
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("密碼錯誤，請再試一次！")
            else:
                st.error("找不到這個帳號，請先註冊喔！")

    with tab2:
        st.subheader("註冊新帳號")
        reg_user = st.text_input("設定帳號 (英文數字)", key="reg_user")
        reg_name = st.text_input("顯示暱稱 (大家會看到這個名字)", key="reg_name")
        reg_pass = st.text_input("設定密碼", type="password", key="reg_pass")
        reg_pass2 = st.text_input("再次確認密碼", type="password", key="reg_pass2")
        if st.button("註冊"):
            if reg_user and reg_name and reg_pass:
                if reg_pass == reg_pass2:
                    hashed_pw = utils.hash_password(reg_pass)
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

# ==========================================
# 畫面 A：首頁
# ==========================================
if st.session_state.page == "home":
    st.title("📅 揪團喬時間神器")
    st.markdown("準備好開始了嗎？")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👑 我是主揪 (建立新揪團)", use_container_width=True, type="primary"):
            st.session_state.page = "create_event"
            st.rerun()
    with col2:
        if st.button("🙋 加入揪團 (輸入代碼)", use_container_width=True):
            st.session_state.page = "join_event"
            st.rerun()

# ==========================================
# 畫面 B：我是主揪
# ==========================================
elif st.session_state.page == "create_event":
    st.title("👑 建立新揪團")
    
    # 升級：解鎖了暱稱欄位！可以自由更改，預設值是自己的名字
    organizer_name = st.text_input("你在本揪團的暱稱 (主揪)：", value=st.session_state.display_name)
    event_name = st.text_input("活動名稱：")
    date_range = st.date_input("預計出遊區間 (請選『開始』與『結束』日)：", value=[])
    
    if st.button("確認建立活動", type="primary"):
        if organizer_name and event_name and len(date_range) == 2:
            start_date, end_date = date_range
            new_code = utils.generate_event_code()
            # 傳入自己的 st.session_state.username
            db.save_event(new_code, st.session_state.username, organizer_name, event_name, start_date, end_date)
            st.session_state.current_event_code = new_code
            st.session_state.page = "fill_form"
            st.rerun()
        else:
            st.warning("⚠️ 請填寫暱稱及活動名稱，並確保日期選了兩天喔！")
    if st.button("← 返回首頁"):
        st.session_state.page = "home"
        st.rerun()

# ==========================================
# 畫面 C：加入揪團
# ==========================================
elif st.session_state.page == "join_event":
    st.title("🙋 加入揪團")
    input_code = st.text_input("請輸入活動代碼 (5 碼)：").upper()
    if st.button("進入活動", type="primary"):
        events_df = db.load_events()
        if input_code in events_df["活動代碼"].values:
            st.session_state.current_event_code = input_code
            st.session_state.page = "fill_form"
            st.rerun()
        else:
            st.error("❌ 找不到這個活動代碼！")
    if st.button("← 返回首頁"):
        st.session_state.page = "home"
        st.rerun()

# ==========================================
# 畫面 D：填寫你的請假表
# ==========================================
elif st.session_state.page == "fill_form":
    current_code = st.session_state.current_event_code
    events_df = db.load_events()
    event_info = events_df[events_df["活動代碼"] == current_code].iloc[0]
    
    st.title(f"📝 填寫請假表：{event_info['活動名稱']}")
    st.caption(f"👑 主揪：{event_info['主揪']} | 🔑 活動代碼：`{current_code}`")
    
    start_date = datetime.strptime(str(event_info['開始日期']), "%Y-%m-%d").date()
    end_date = datetime.strptime(str(event_info['結束日期']), "%Y-%m-%d").date()
    delta = end_date - start_date
    date_options = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]

    # 升級：解鎖了暱稱欄位！可以自由更改，預設值是自己的名字
    participant_name = st.text_input("你在本揪團的暱稱：", value=st.session_state.display_name)
    selected_dates = st.multiselect(f"選擇你在這段期間「沒空」的日期：", date_options)

    if st.button("送出並查看結果", type="primary"):
        if participant_name:
            # 傳入自己的 st.session_state.username
            db.save_response(current_code, st.session_state.username, participant_name, selected_dates)
            st.session_state.page = "view_results"
            st.rerun()
        else:
            st.warning("⚠️ 名字一定要填喔！")
            
    if st.button("🏠 回首頁 (離開活動)"):
        st.session_state.page = "home"
        st.query_params.clear()
        st.rerun()

# ==========================================
# 畫面 E：即時統計結果
# ==========================================
elif st.session_state.page == "view_results":
    current_code = st.session_state.current_event_code
    events_df = db.load_events()
    
    if current_code not in events_df["活動代碼"].values:
        st.warning("這個活動已經被刪除了喔！")
        if st.button("🏠 回首頁"):
            st.session_state.page = "home"
            st.session_state.current_event_code = ""
            st.rerun()
    else:
        event_info = events_df[events_df["活動代碼"] == current_code].iloc[0]
        st.title(f"✨ 統計結果：{event_info['活動名稱']}")
        
        start_date = datetime.strptime(str(event_info['開始日期']), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(event_info['結束日期']), "%Y-%m-%d").date()
        delta = end_date - start_date
        date_options = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]

        all_responses = db.load_responses()
        event_responses = all_responses[all_responses["活動代碼"] == current_code]

        if not event_responses.empty:
            participants = event_responses["姓名"].unique()
            st.write(f"👥 目前已有 **{len(participants)}** 人填寫：{', '.join(participants)}")
            
            real_busy_dates = event_responses[event_responses["沒空日期"] != "完全有空"]
            
            busy_dict = {}
            for index, row in real_busy_dates.iterrows():
                d = row["沒空日期"]
                name = row["姓名"]
                if d not in busy_dict:
                    busy_dict[d] = []
                busy_dict[d].append(name)
            
            if not real_busy_dates.empty:
                golden_dates = [d for d in date_options if d not in busy_dict.keys()]
            else:
                golden_dates = date_options
                
            st.subheader("📅 黃金出遊月曆")
            st.caption("提示：🟩 綠色代表大家都有空。灰色代表有人請假，**滑鼠移過去可看誰沒空**。")
            
            calendar_html = utils.generate_calendar_html(start_date, end_date, golden_dates, busy_dict, current_code)
            st.markdown(calendar_html, unsafe_allow_html=True)
            
            if busy_dict:
                st.divider()
                st.subheader("🔍 查看特定日期的請假名單")
                busy_date_list = sorted(list(busy_dict.keys()))
                selected_date = st.selectbox("請選擇有人請假的日期：", ["-- 請選擇日期 --"] + busy_date_list)
                
                if selected_date != "-- 請選擇日期 --":
                    st.warning(f"📅 {selected_date} 共有 {len(busy_dict[selected_date])} 個人沒空：")
                    for name in busy_dict[selected_date]:
                        st.markdown(f"### 🙅 {name}")
                
        else:
            st.info("出了一點錯，找不到統計資料。")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 修改我的請假表", use_container_width=True):
                st.session_state.page = "fill_form"
                st.rerun()
        with col2:
            if st.button("🏠 回首頁 (離開活動)", use_container_width=True):
                st.session_state.page = "home"
                st.query_params.clear()
                st.rerun()