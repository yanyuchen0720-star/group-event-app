import streamlit as st
from datetime import datetime
import calendar
from core import database as db
from utils import helpers

# ==========================================
# 接著放 def render_home(): ...
# def toggle_create_date(clicked_date): ...
# def render_create_event(): ...
# 以及 def render_join_event(): ...
# ==========================================

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
# 畫面 B：我是主揪（優化：單一月曆搭配年月切換與雙向連動）
# ==========================================
def toggle_create_date(clicked_date):
    current_val = list(st.session_state.create_date_picker)
    
    if not current_val:
        st.session_state.create_date_picker = [clicked_date]
    elif len(current_val) == 1:
        st.session_state.create_date_picker = sorted([current_val[0], clicked_date])
    else:
        st.session_state.create_date_picker = [clicked_date]

def render_create_event():
    if "create_date_picker" not in st.session_state:
        st.session_state.create_date_picker = []

    st.title("👑 建立新揪團")
    organizer_name = st.text_input("你在本揪團的暱稱 (主揪)：", value=st.session_state.display_name)
    event_name = st.text_input("活動名稱：")
    
    # 將 st.date_input 綁定 key，與 session_state 達成雙向連動
    date_range = st.date_input(
        "預計出遊區間 (請選『開始』與『結束』日)：", 
        key="create_date_picker"
    )
    
    st.divider()
    st.markdown("### 📅 點擊月曆快速選擇區間")
    st.caption("提示：點選第一個日期作為開始日，點選第二個日期作為結束日。月曆會自動渲染選取範圍，且與上方輸入框即時同步！")
    
    # 🌟 獲取今天日期，用作預設值與防呆
    today = datetime.today().date()
    
    # 🌟 初始化年月的 Session State，確保切換時狀態不遺失
    if "create_cal_year" not in st.session_state:
        st.session_state.create_cal_year = today.year
    if "create_cal_month" not in st.session_state:
        st.session_state.create_cal_month = today.month

    # 🌟 建立年、月的選擇下拉選單（橫向並排）
    year_cols, month_cols = st.columns(2)
    with year_cols:
        # 提供今年到未來 5 年的長遠選項
        year_options = list(range(today.year, today.year + 6))
        selected_year = st.selectbox(
            "選擇年份", 
            year_options, 
            index=year_options.index(st.session_state.create_cal_year)
        )
        st.session_state.create_cal_year = selected_year
        
    with month_cols:
        month_options = list(range(1, 13))
        selected_month = st.selectbox(
            "選擇月份", 
            month_options, 
            index=month_options.index(st.session_state.create_cal_month)
        )
        st.session_state.create_cal_month = selected_month

    # 🌟 根據選取的年份與月份，渲染單一月份的月曆
    year = st.session_state.create_cal_year
    month = st.session_state.create_cal_month
    
    st.markdown(f"<h5 style='text-align: center; margin-top: 10px;'>{year}年 {month}月</h5>", unsafe_allow_html=True)
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
                
                # 核心連動高亮邏輯：判斷該日期是否在目前選定的範圍內
                current_val = list(st.session_state.create_date_picker)
                is_selected = False
                if len(current_val) == 1:
                    is_selected = (current_date == current_val[0])
                elif len(current_val) == 2:
                    is_selected = (current_val[0] <= current_date <= current_val[1])
                    
                btn_type = "primary" if is_selected else "secondary"
                
                # 防呆機制：過去的日期不給點選
                if current_date < today:
                    cols[i].button(str(day), key=f"create_dis_{year}_{month}_{day}", disabled=True, use_container_width=True)
                else:
                    cols[i].button(
                        str(day), 
                        key=f"create_calbtn_{current_date.strftime('%Y-%m-%d')}", 
                        type=btn_type, 
                        on_click=toggle_create_date, 
                        args=(current_date,), 
                        use_container_width=True
                    )
            else:
                cols[i].markdown("<div style='min-height: 40px;'></div>", unsafe_allow_html=True)

    st.divider()
    if st.button("確認建立活動", type="primary"):
        if organizer_name and event_name and len(date_range) == 2:
            start_date, end_date = date_range
            new_code = helpers.generate_event_code()
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