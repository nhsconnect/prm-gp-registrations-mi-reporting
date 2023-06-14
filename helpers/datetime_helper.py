from datetime import date, datetime, timezone

def create_date_time(date: date, time: str):
    return date.strftime(f"%Y-%m-%dT{time}")

def datetime_utc_now():
    return datetime.now(timezone.utc)
