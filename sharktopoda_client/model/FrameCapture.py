from os import PathLike

from sharktopoda_client.JavaTypes import Duration


class FrameCapture:
    def __init__(self, saveLocation: PathLike = None, snapTime: Duration = None):
        self.saveLocation = saveLocation
        self.snapTime = snapTime
    
    def getSaveLocation(self) -> PathLike:
        return self.saveLocation
    
    def getSnapTime(self) -> Duration:
        return self.snapTime