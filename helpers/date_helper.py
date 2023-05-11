from datetime import date
def create_date_time(date: date, time: str):
    return date.strftime(f"%Y-%m-%dT{time}")