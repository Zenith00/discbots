import datetime

import dateparser
from . import magic


class TimeParser:
    def __init__(self):
        pass

    def from_string(self, string: str) -> datetime.datetime:
        target = None
        try:
            seconds = int(string)
            target = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
            return target
        except ValueError:
            res = dateparser.parse(string)  # type: datetime.datetime
            if not res.tzinfo:
                res.replace(tzinfo=datetime.timezone.utc)
            return res
