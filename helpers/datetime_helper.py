from datetime import date, datetime, timezone, timedelta

def create_date_time(date: date, time: str):
    return date.strftime(f"%Y-%m-%dT{time}+00:00")

def datetime_utc_now():
    return datetime.now(timezone.utc)
