"""
Sharktopoda 2 data transfer objects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID


class Serializable(ABC):
    """
    Serializable interface. Supports encoding and decoding to and from a dictionary.
    """

    @abstractmethod
    def encode(self) -> dict:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def decode(cls, data: dict):
        raise NotImplementedError


@dataclass
class VideoPlayerState(Serializable):
    class PlayStatus(str, Enum):
        PLAYING = "playing"
        SHUTTLING_FORWARD = "shuttling forward"
        SHUTTLING_REVERSE = "shuttling reverse"
        PAUSED = "paused"

    status: PlayStatus
    rate: float

    def encode(self) -> dict:
        return {"status": self.status.value, "rate": self.rate}

    @classmethod
    def decode(cls, video_player_state: dict) -> "VideoPlayerState":
        return cls(
            status=VideoPlayerState.PlayStatus(video_player_state["status"]),
            rate=video_player_state["rate"],
        )


@dataclass
class VideoInfo(Serializable):

    uuid: UUID
    url: str
    duration_millis: int
    frame_rate: float
    is_key: bool

    def encode(self) -> dict:
        return {
            "uuid": str(self.uuid),
            "url": self.url,
            "durationMillis": self.duration_millis,
            "frameRate": self.frame_rate,
            "isKey": self.is_key,
        }

    @classmethod
    def decode(cls, video_info: dict) -> "VideoInfo":
        return cls(
            uuid=UUID(video_info["uuid"]),
            url=video_info["url"],
            duration_millis=video_info["durationMillis"],
            frame_rate=video_info["frameRate"],
            is_key=video_info["isKey"],
        )


@dataclass
class FrameCapture(Serializable):

    uuid: UUID
    elapsed_time_millis: int
    image_reference_uuid: UUID
    image_location: Path

    def encode(self) -> dict:
        return {
            "uuid": str(self.uuid),
            "elapsedTimeMillis": self.elapsed_time_millis,
            "imageReferenceUuid": str(self.image_reference_uuid),
            "imageLocation": str(self.image_location),
        }

    @classmethod
    def decode(cls, frame_capture: dict) -> "FrameCapture":
        return cls(
            uuid=UUID(frame_capture["uuid"]),
            elapsed_time_millis=frame_capture["elapsedTimeMillis"],
            image_reference_uuid=UUID(frame_capture["imageReferenceUuid"]),
            image_location=Path(frame_capture["imageLocation"]),
        )


@dataclass
class Localization(Serializable):

    uuid: UUID
    concept: str
    elapsed_time_millis: int
    x: int
    y: int
    width: int
    height: int
    duration_millis: int = 0
    color: Optional[str] = None

    def encode(self) -> dict:
        data = {
            "uuid": str(self.uuid),
            "concept": self.concept,
            "elapsedTimeMillis": self.elapsed_time_millis,
            "durationMillis": self.duration_millis,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

        if self.color is not None:
            data["color"] = self.color

        return data

    @classmethod
    def decode(cls, localization: dict) -> "Localization":
        return cls(
            uuid=UUID(localization["uuid"]),
            concept=localization["concept"],
            elapsed_time_millis=localization["elapsedTimeMillis"],
            duration_millis=localization["durationMillis"],
            x=localization["x"],
            y=localization["y"],
            width=localization["width"],
            height=localization["height"],
            color=localization["color"] if "color" in localization else None,
        )
