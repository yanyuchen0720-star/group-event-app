import random
import string
import calendar
from datetime import datetime
import hashlib

def generate_event_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_calendar_html(start_date, end_date, golden_dates, busy_dict, current_code):
    # --- 新增的 CSS 魔法：讓手機點擊可以觸發浮動視窗 ---
    html = """
    <style>
    .my-tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        outline: none; /* 隱藏點擊時的預設外框 */
        width: 100%;
        -webkit-tap-highlight-color: transparent; /* 移除手機點擊時的預設藍色閃爍 */
    }
    .my-tooltip .my-tooltiptext {
        visibility: hidden;
        width: max-content;
        min-width: 80px;
        max-width: 160px;
        background-color: #4A4A4A;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 999;
        bottom: 130%; /* 浮動在日期正上方 */
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.2s;
        font-size: 14px;
        line-height: 1.5;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
        white-space: pre-wrap;
    }
    /* 畫出對話框下方的小三角形 */
    .my-tooltip .my-tooltiptext::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #4A4A4A transparent transparent transparent;
    }
    /* 重頭戲：電腦滑鼠懸停 (hover) 或手機點擊聚焦 (focus) 都會顯示名單 */
    .my-tooltip:hover .my-tooltiptext, 
    .my-tooltip:focus .my-tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """
    
    current_m = start_date.replace(day=1)
    months = []
    
    while current_m <= end_date:
        months.append((current_m.year, current_m.month))
        if current_m.month == 12:
            current_m = current_m.replace(year=current_m.year + 1, month=1)
        else:
            current_m = current_m.replace(month=current_m.month + 1)
    
    for year, month in months:
        cal = calendar.monthcalendar(year, month)
        html += f"<h4 style='text-align:center;'>{year}年 {month}月</h4>"
        html += "<table style='width:100%; text-align:center; border-collapse: collapse; margin-bottom: 20px; font-size: 18px;'>"
        html += "<tr><th>一</th><th>二</th><th>三</th><th>四</th><th>五</th><th>六</th><th>日</th></tr>"
        
        for week in cal:
            html += "<tr>"
            for day in week:
                if day == 0:
                    html += "<td style='padding: 10px;'></td>"
                else:
                    current_date = datetime(year, month, day).date()
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    if current_date < start_date or current_date > end_date:
                        html += f"<td style='padding: 10px; color: gray; opacity: 0.2;'>{day}</td>"
                    elif date_str in golden_dates:
                        html += f"<td style='padding: 10px; background-color: rgba(76, 175, 80, 0.3); border: 2px solid #4CAF50; border-radius: 8px; font-weight: bold; color: #4CAF50;'>{day}</td>"
                    else:
                        people = busy_dict.get(date_str, [])
                        hover_text = f"沒空：<br>{', '.join(people)}"
                        html += f"<td style='padding: 10px; background-color: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); color: gray;'>"
                        # 關鍵修改：加入 tabindex='0'，讓手機點擊時能觸發 Focus
                        html += f"<div class='my-tooltip' tabindex='0'>"
                        html += f"<span style='text-decoration: line-through;'>{day}</span>"
                        html += f"<span class='my-tooltiptext'>{hover_text}</span>"
                        html += f"</div></td>"
            html += "</tr>"
        html += "</table>"
    return html

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, input_password):
    return stored_hash == hash_password(input_password)