import random
import string
import calendar
from datetime import datetime
import hashlib

def generate_event_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_calendar_html(start_date, end_date, golden_dates, busy_dict, current_code):
    html = ""
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
                        hover_text = f"沒空的人：{', '.join(people)}"
                        # 【修改這裡】移除了超連結，改成單純的格子加上懸停提示
                        html += f"<td style='padding: 10px; background-color: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); text-decoration: line-through; color: gray;' title='{hover_text}'>{day}</td>"
            html += "</tr>"
        html += "</table>"
    return html

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, input_password):
    return stored_hash == hash_password(input_password)