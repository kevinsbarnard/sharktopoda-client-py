from dataclasses import field, MISSING

from dataclasses_json import config


class Duration:
    @classmethod
    def ofMillis(cls, millis: int) -> 'Duration':
        return Duration()  # TODO: implement

    def toMillis(self) -> int:
        return 0  # TODO: implement
    


class InetAddress:
    pass  # TODO: implement java.net.InetAddress


def SerializedName(name, default=MISSING):
    return field(metadata=config(field_name=name), default=default)
