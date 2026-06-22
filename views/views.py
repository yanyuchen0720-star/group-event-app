import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from core import database as db
from utils import helpers

def toggle_date(date_str):
    current_dates = list(st.session_state.form_selected_dates)
    if date_str in current_dates:
        current_dates.remove(date_str)
    else:
        current_dates.append(date_str)
    st.session_state.form_selected_dates = current_dates

def render_fill_form(REDIRECT_URI):
    current_code = st.session_state.current_event_code
    events_df = db.load_events()
    event_info = events_df[events_df["活動代碼"] == current_code].iloc[0]
    
    # 🌟 真・修復：讀取我們剛才在 app.py 建立的強制重整旗標
    force_reload = st.session_state.get("force_reload_form", False)
    
    # 如果是切換了不同活動，或者是被強制要求重整，就去資料庫拿資料
    if st.session_state.form_event_code != current_code or force_reload:
        st.session_state.form_event_code = current_code
        st.session_state.force_reload_form = False  # 🌟 資料拿完後，馬上把旗標關掉
        
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
            
            # 呼叫 helpers (原 utils) 裡面的 HTML 產生器
            calendar_html = helpers.generate_calendar_html(start_date, end_date, golden_dates, busy_dict, current_code)
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
                # 🌟 核心按鈕：在這裡按下時，將旗標開啟，指示填寫頁面重新向資料庫要資料
                st.session_state.force_reload_form = True 
                st.rerun()
        with col2:
            if st.button("🏠 回首頁 (離開活動)", use_container_width=True):
                st.session_state.page = "home"
                st.query_params.clear()
                st.rerun()