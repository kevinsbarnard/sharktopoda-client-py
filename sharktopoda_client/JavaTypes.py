import datetime
from dataclasses import field, MISSING
import random
import string

from dataclasses_json import config


class Duration(datetime.timedelta):
    @classmethod
    def ofMillis(cls, millis: int) -> 'Duration':
        return Duration(milliseconds=millis)

    def toMillis(self) -> int:
        return self.microseconds // 1000
    


class InetAddress:
    pass  # TODO: implement java.net.InetAddress


def SerializedName(name, default=MISSING):  # dark magic
    return field(metadata=config(field_name=name), default=default)


def randomString(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits), k=length)
