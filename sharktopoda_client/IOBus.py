from typing import Any

from rx.core.typing import Subject as SubjectType
from rx.subject import Subject

class IOBus:
    def __init__(self) -> None:
        self._incoming: SubjectType[Any] = Subject()
        self._outgoing: SubjectType[Any] = Subject()
    
    def getIncoming(self) -> SubjectType[Any]:
        return self._incoming
    
    def getOutgoing(self) -> SubjectType[Any]:
        return self._outgoing
    
    