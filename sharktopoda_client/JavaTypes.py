import datetime
from dataclasses import field, MISSING
import random
import string

from dataclasses_json import config

class InetAddress:
    pass  # TODO: implement java.net.InetAddress


def SerializedName(name, default=MISSING, encoder=None, decoder=None):
    return field(metadata=config(field_name=name, encoder=encoder, decoder=decoder), default=default)


def randomString(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
