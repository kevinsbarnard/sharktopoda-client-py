from uuid import UUID


class Video:
    def __init__(self, uuid: UUID = None, url: str = None):
        self.uuid = uuid
        self.url = url
    
    def getUuid(self) -> UUID:
        return self.uuid
    
    def getUrl(self) -> str:
        return self.url
    
    def __eq__(self, o: 'Video') -> bool:
        if self is o:
            return True
        if o is None or type(self) != type(o):
            return False
        
        return self.uuid == o.uuid
    
    def __hash__(self) -> int:
        return hash(self.uuid)
