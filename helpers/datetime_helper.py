import calendar
from datetime import date, datetime, timezone

def create_date_time(date: date, time: str):
    return date.strftime(f"%Y-%m-%dT{time}+00:00")

def datetime_utc_now():
    return datetime.now(timezone.utc)

def get_last_day_of_current_month():
    # Get the last day of the month from a given date
    input_dt = date.today()
    # monthrange() to gets the date range
    # year = 2022, month = 9
    res = calendar.monthrange(input_dt.year, input_dt.month)
    day = res[1]
    
    return day
    # note:
    # res [0]  = weekday of first day (between 0-6 ~ Mon-Sun))
    # res [1] = last day of the month

def generate_report_start_date():
     return date.today().replace(day=1)

def generate_report_end_date():
    return  datetime_utc_now().replace(day=get_last_day_of_current_month(), hour=23, minute=59)