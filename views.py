import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import database as db
import utils

# ==========================================
# 側邊欄
# ==========================================
def render_sidebar():
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
            st.session_state.page = "login"
            st.rerun()

# ==========================================
# 畫面 0：登入與註冊門神
# ==========================================
def render_login(CLIENT_ID, REDIRECT_URI):
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
                if utils.verify_password(user_data["密碼雜湊"], login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.display_name = user_data["顯示名稱"]
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
def render_home():
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
def render_create_event():
    st.title("👑 建立新揪團")
    organizer_name = st.text_input("你在本揪團的暱稱 (主揪)：", value=st.session_state.display_name)
    event_name = st.text_input("活動名稱：")
    date_range = st.date_input("預計出遊區間 (請選『開始』與『結束』日)：", value=[])
    
    if st.button("確認建立活動", type="primary"):
        if organizer_name and event_name and len(date_range) == 2:
            start_date, end_date = date_range
            new_code = utils.generate_event_code()
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
def render_join_event():
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
def toggle_date(date_str):
    if date_str in st.session_state.form_selected_dates:
        st.session_state.form_selected_dates.remove(date_str)
    else:
        st.session_state.form_selected_dates.append(date_str)

def render_fill_form(REDIRECT_URI):
    current_code = st.session_state.current_event_code
    events_df = db.load_events()
    event_info = events_df[events_df["活動代碼"] == current_code].iloc[0]
    
    if st.session_state.form_event_code != current_code:
        st.session_state.form_event_code = current_code
        all_responses = db.load_responses()
        my_records = all_responses[
            (all_responses["活動代碼"] == current_code) & 
            (all_responses["參與者帳號"] == st.session_state.username)
        ]
        
        start_date = datetime.strptime(str(event_info['開始日期']), "%Y-%m-%d").date()
        end_date = datetime.strptime(str(event_info['結束日期']), "%Y-%m-%d").date()
        delta = end_date - start_date
        date_options = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
        
        if not my_records.empty:
            st.session_state.form_default_name = my_records["姓名"].iloc[0]
            saved_dates = my_records["沒空日期"].tolist()
            st.session_state.form_selected_dates = [d for d in saved_dates if d in date_options]
        else:
            st.session_state.form_default_name = st.session_state.display_name
            st.session_state.form_selected_dates = []

    st.title(f"📝 填寫請假表：{event_info['活動名稱']}")
    st.caption(f"👑 主揪：{event_info['主揪']} | 🔑 活動代碼：`{current_code}`")
    
    share_url = f"{REDIRECT_URI}?code={current_code}"
    st.info(f"🔗 **邀請朋友加入**：複製下方網址給朋友\n`{share_url}`")
    
    start_date = datetime.strptime(str(event_info['開始日期']), "%Y-%m-%d").date()
    end_date = datetime.strptime(str(event_info['結束日期']), "%Y-%m-%d").date()
    delta = end_date - start_date
    date_options = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]

    participant_name = st.text_input("你在本揪團的暱稱：", value=st.session_state.form_default_name)
    
    st.divider()
    st.markdown("### 📅 標記你「沒空」的日子")
    st.caption("提示：可以從下拉選單選擇，也可以直接點擊下方月曆。紅色按鈕代表那一天你請假囉！")
    
    st.multiselect("已選取的請假日清單：", date_options, key="form_selected_dates")
    
    current_m = start_date.replace(day=1)
    months = []
    while current_m <= end_date:
        months.append((current_m.year, current_m.month))
        if current_m.month == 12:
            current_m = current_m.replace(year=current_m.year + 1, month=1)
        else:
            current_m = current_m.replace(month=current_m.month + 1)
            
    for year, month in months:
        st.markdown(f"<h5 style='text-align: center; margin-top: 15px;'>{year}年 {month}月</h5>", unsafe_allow_html=True)
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        cols = st.columns(7)
        for i, wd in enumerate(weekdays):
            cols[i].markdown(f"<div style='text-align: center; font-size: 14px; color: gray;'>{wd}</div>", unsafe_allow_html=True)
            
        cal = calendar.monthcalendar(year, month)
        for week_idx, week in enumerate(cal):
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    current_date = datetime(year, month, day).date()
                    date_str = current_date.strftime("%Y-%m-%d")
                    if current_date < start_date or current_date > end_date:
                        cols[i].button(str(day), key=f"dis_{year}_{month}_{day}", disabled=True, use_container_width=True)
                    else:
                        is_selected = date_str in st.session_state.form_selected_dates
                        btn_type = "primary" if is_selected else "secondary"
                        cols[i].button(
                            str(day), 
                            key=f"calbtn_{date_str}", 
                            type=btn_type, 
                            on_click=toggle_date, 
                            args=(date_str,), 
                            use_container_width=True
                        )
                else:
                    cols[i].markdown("<div style='min-height: 40px;'></div>", unsafe_allow_html=True)

    st.divider()
    if st.button("送出並查看結果", type="primary", use_container_width=True):
        if participant_name:
            db.save_response(current_code, st.session_state.username, participant_name, st.session_state.form_selected_dates)
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
def render_view_results():
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
            st.caption("提示：🟩 綠色代表大家都有空。灰色代表有人請假，**點擊或長按可看誰沒空**。")
            
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