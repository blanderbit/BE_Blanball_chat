import pandas
from datetime import datetime


def round_date_and_time(datetime: datetime) -> None:
    return pandas.to_datetime(datetime.isoformat()).round("1min").to_pydatetime()
