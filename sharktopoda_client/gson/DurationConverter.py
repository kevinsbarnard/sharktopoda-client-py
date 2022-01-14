from sharktopoda_client.JavaTypes import Duration


class DurationConverter:
    def deserialize(self, json_str: str, *_) -> Duration:
        return Duration.ofMillis(int(json_str))

    def serialize(self, duration: Duration, *_) -> str:
        return str(duration.toMillis())
