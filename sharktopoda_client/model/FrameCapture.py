from os import PathLike


class FrameCapture:
    def __init__(self, saveLocation: PathLike = None, snapTime: int = None):
        self.saveLocation = saveLocation
        self.snapTime = snapTime
    
    def getSaveLocation(self) -> PathLike:
        return self.saveLocation
    
    def getSnapTime(self) -> int:
        return self.snapTime