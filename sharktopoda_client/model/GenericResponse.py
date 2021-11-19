from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from dataclasses_json import dataclass_json

from sharktopoda_client.JavaTypes import Duration, InetAddress, SerializedName
from sharktopoda_client.model.GenericCommand import GenericCommand


@dataclass_json
@dataclass
class GenericResponse:
    response: Optional[str] = None
    status: Optional[str] = None
    uuid: Optional[UUID] = None
    elapsedTime: Optional[Duration] = SerializedName('elapsed_time_millis', default=None)
    imageReferenceUuid: Optional[UUID] = None
    imageLocation: Optional[str] = None
    url: Optional[str] = None
    packetAddress: Optional[InetAddress] = None
    packetPort: Optional[int] = None
    
    @classmethod
    def from_cmd(cls, cmd: GenericCommand) -> 'GenericResponse':
        return cls(
            packetAddress=cmd.packetAddress,
            packetPort=cmd.packetPort,
            response=cmd.command,
            uuid=cmd.uuid
        )
    
    @classmethod
    def from_str(cls, response: str) -> 'GenericResponse':
        return cls(response=response)
    
    @classmethod
    def from_cmd_and_str(cls, cmd: GenericCommand, response: str) -> 'GenericResponse':
        return cls(
            packetAddress=cmd.packetAddress,
            packetPort=cmd.packetPort,
            response=response,
            uuid=cmd.uuid
        )
