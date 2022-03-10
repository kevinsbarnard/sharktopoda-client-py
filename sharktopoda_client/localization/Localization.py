from typing import Optional
from uuid import UUID, uuid4
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from sharktopoda_client.JavaTypes import SerializedName


@dataclass_json
@dataclass
class Localization:
    concept: Optional[str] = None
    elapsedTime: Optional[int] = SerializedName('elapsedTimeMillis', default=None)
    duration: Optional[int] = SerializedName('durationMillis', default=None)
    videoReferenceUuid: Optional[UUID] = None
    annotationUuid: Optional[UUID] = None
    localizationUuid: Optional[UUID] = None
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sourceId: Optional[str] = None
    
    def __post_init__(self):
        if self.localizationUuid is None:
            self.localizationUuid = uuid4()
    
    @classmethod
    def from_other(cls, n: 'Localization') -> 'Localization':
        return cls(
            concept=n.concept,
            elapsedTime=n.elapsedTime,
            duration=n.duration,
            videoReferenceUuid=n.videoReferenceUuid,
            annotationUuid=n.annotationUuid,
            localizationUuid=n.localizationUuid,
            x=n.x,
            y=n.y,
            width=n.width,
            height=n.height
        )
    
    def __eq__(self, o: object) -> bool:
        if self is o:
            return True
        if o is None or type(self) != type(o):
            return False

        return self.localizationUuid == o.localizationUuid
    
    def __hash__(self) -> int:
        return hash(self.localizationUuid)
    
    def __str__(self) -> str:
        return 'Localization{' + \
            'concept=' + self.concept + '\'' + \
            ', elapsedTime=' + str(self.elapsedTime) + \
            ', localizationUuid=' + str(self.localizationUuid) + \
            '}'
    