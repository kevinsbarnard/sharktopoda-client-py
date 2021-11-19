class Preconditions:
    @staticmethod
    def require(ok: bool, msg: str):
        if not ok:
            raise ValueError(msg)