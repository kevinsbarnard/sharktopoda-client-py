from uuid import UUID
from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Video:
    uuid: UUID = None
    url: str = None
    
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
