from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from dataclasses_json import dataclass_json

from sharktopoda_client.JavaTypes import InetAddress, SerializedName


@dataclass_json
@dataclass
class GenericCommand:
    command: Optional[str] = None
    port: Optional[int] = None
    host: Optional[str] = None
    url: Optional[str] = None
    uuid: Optional[UUID] = None
    rate: Optional[float] = None
    elapsedTime: Optional[float] = SerializedName('elapsed_time_millis', default=None)
    imageLocation: Optional[str] = None
    imageReferenceUuid: Optional[UUID] = None
    packetAddress: Optional[InetAddress] = None
    packetPort: Optional[int] = None
