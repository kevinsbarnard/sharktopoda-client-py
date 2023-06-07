"""
Sharktopoda 2 client.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from threading import Thread
from typing import List, Optional
from uuid import UUID
from socket import socket, AF_INET, SOCK_DGRAM

from rx.subject import Subject
from rx.scheduler import EventLoopScheduler

from sharktopoda_client.log import LogMixin


class RxUDPServer(LogMixin):
    """
    ReactiveX UDP server. Handles sending and receiving UDP packets asynchronously via RxPy subjects.
    """

    def __init__(self, send_host: str, send_port: int, receive_port: int) -> None:
        # UDP socket
        self._socket = None
        self._send_host = send_host
        self._send_port = send_port
        self._receive_port = receive_port

        # Rx
        self._send_subject = Subject()
        self._receive_subject = Subject()
        self._scheduler = EventLoopScheduler()

        self._ok = True

        def receive():
            while self._ok:
                try:
                    # Block until we receive a datagram
                    datagram, (host, port) = self.socket.recvfrom(4096)

                    self.logger.debug(
                        f"Received UDP datagram {datagram} from {host}:{port}"
                    )

                    if host != self._send_host:  # ignore data from other hosts
                        continue

                    # Decode the datagram
                    json_data = datagram.decode('utf-8')
                    data = json.loads(json_data)

                    # Send the decoded data to the receive subject
                    self._receive_subject.on_next(data)

                except Exception as e:
                    self.logger.error(f"Error while reading UDP datagram {e}")
                    self._ok = False

            if self._socket is not None:  # close socket if it exists
                self.socket.close()
                self._socket = None
                self.logger.info("Closed UDP socket")

        self._receiver_thread = Thread(target=receive, daemon=True)
        self._receiver_thread.start()
        self.logger.debug("Started UDP receiver thread")

        self._send_subject.subscribe(self._send, scheduler=self._scheduler)

    def _send(self, data: dict):
        # Encode the data
        json_data = json.dumps(data)
        datagram = json_data.encode('utf-8')

        # Send the packet
        self.socket.sendto(datagram, (self._send_host, self._send_port))

        self.logger.debug(
            f"Sent UDP datagram {datagram} to {self._send_host}:{self._send_port}"
        )

    @property
    def socket(self):
        if self._socket is None:
            self._socket = socket(AF_INET, SOCK_DGRAM)
            host = ""  # listen on all interfaces
            self._socket.bind((host, self._receive_port))
            self.logger.info(f"Opened UDP socket on {host}:{self._receive_port}")
        return self._socket

    @property
    def send_subject(self) -> Subject:
        return self._send_subject

    @property
    def receive_subject(self) -> Subject:
        return self._receive_subject


class VideoOpenState(Enum):
    CLOSED = 0
    OPENING = 1
    OPEN = 2


class PlayStatus(str, Enum):
    PLAYING = "playing"
    SHUTTLING_FORWARD = "shuttling forward"
    SHUTTLING_REVERSE = "shuttling reverse"
    PAUSED = "paused"


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
    status: PlayStatus
    rate: float

    def encode(self) -> dict:
        return {"status": self.status.value, "rate": self.rate}

    @classmethod
    def decode(cls, video_player_state: dict) -> "VideoPlayerState":
        return cls(
            status=PlayStatus(video_player_state["status"]),
            rate=video_player_state["rate"],
        )


@dataclass
class VideoInfo:
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
class FrameCapture:
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
class Localization:
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


class SharktopodaClient(LogMixin):
    """
    Sharktopoda client. Manages local state and communication with the server (application).
    """

    def __init__(self, rx_udp_server: RxUDPServer):
        """
        Args:
            rx_udp_server: The ReactiveX UDP server to use for communication.
        """
        self.rx_udp_server = rx_udp_server

        self._connected = False
        self._video_open_state = {}
        self._focused_video_info = None
        self._all_video_info = None
        self._video_player_state = {}
        self._frame_captures = []
        self._uncommitted_localizations = {}
        self._localizations = {}
        self._selected_localizations = {}

        self.rx_udp_server.receive_subject.subscribe(self._handle_message)

    def _commit_localizations(self):
        self._localizations.update(self._uncommitted_localizations)

    def _revert_localizations(self):
        self._uncommitted_localizations.clear()
        self._uncommitted_localizations.update(self._localizations)

    def send(self, message: dict):
        """
        Send a message.

        Args:
            message: The message to send.
        """
        self.rx_udp_server.send_subject.on_next(message)

    def _handle_message(self, message: dict):
        """
        Handle a message received from the server.
        """
        if "command" in message:
            self._handle_command(message)
        elif "response" in message:
            self._handle_response(message)
        else:
            self.logger.warning(f"Unknown message type: {message}")

    def _handle_command(self, command: dict):
        """
        Handle a command received from the server. Invokes a callback based on the command type.

        Args:
            command: The command to handle.
        """
        command_type = command["command"]

        {
            "ping": self._on_ping_command,
        }.get(
            command_type,
            lambda: self.logger.warning(f"Unknown command type: {command_type}"),
        )(command)

    def _handle_response(self, response: dict):
        """
        Handle a response received from the server. Invokes a callback based on the response type.

        Args:
            response: The response to handle.
        """
        response_type = response["response"]

        {
            "connect": self._on_connect_response,
            "open": self._on_open_response,
            "open done": self._on_open_done_response,
            "close": self._on_close_response,
            "show": self._on_show_response,
            "request information": self._on_request_information_response,
            "request all information": self._on_request_all_information_response,
            "play": self._on_play_response,
            "pause": self._on_pause_response,
            "request player state": self._on_request_player_state_response,
            "seek elapsed time": self._on_seek_elapsed_time_response,
            "frame advance": self._on_frame_advance_response,
            "frame capture": self._on_frame_capture_response,
            "frame capture done": self._on_frame_capture_done_response,
            "add localizations": self._on_add_localizations_response,
            "remove localizations": self._on_remove_localizations_response,
            "update localizations": self._on_update_localizations_response,
            "clear localizations": self._on_clear_localizations_response,
            "select localizations": self._on_select_localizations_response,
        }.get(
            response_type,
            lambda: self.logger.warning(f"Unknown response type: {response_type}"),
        )(
            response
        )

    def _on_ping_command(self, command: dict):
        """
        Send a ping response.
        """
        self.send({"response": "ping", "status": "ok"})

    def _on_connect_response(self, response: dict):
        """
        Handle a connect response.
        """
        if response["status"] == "ok":
            self.logger.info("Connected")
            self._connected = True
        else:
            self.logger.error(f"Failed to connect: {response}")

    def connect(self, port: int):
        """
        Connect to the server.
        """
        self._connected = False

        self.send({"command": "connect", "port": port})

    def open(self, uuid: UUID, url: str):
        """
        Open a URL.
        """
        self.send({"command": "open", "uuid": str(uuid), "url": url})

        self._opened_video_state[uuid] = VideoOpenState.OPENING

    def _on_open_response(self, response: dict):
        """
        Handle an open response.
        """
        if response["status"] == "ok":
            pass
        else:
            self.logger.error(f"Failed to initiate open video")

    def _on_open_done_response(self, response: dict):
        """
        Handle an open done response.
        """
        if response["status"] == "ok":
            uuid = UUID(response["uuid"])
            self.logger.info(f"Opened video {uuid}")
            self._video_open_state[uuid] = VideoOpenState.OPEN
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to open video: {cause}")

    def close(self, uuid: UUID):
        """
        Close a video.
        """
        self.send({"command": "close", "uuid": str(uuid)})

    def _on_close_response(self, response: dict):
        """
        Handle a close response.
        """
        if response["status"] == "ok":
            uuid = UUID(response["uuid"])
            self.logger.info(f"Closed video {uuid}")
            self._video_open_state[uuid] = VideoOpenState.CLOSED
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to close video: {cause}")

    def show(self, uuid: UUID):
        """
        Show a video.
        """
        self.send({"command": "show", "uuid": str(uuid)})

    def _on_show_response(self, response: dict):
        """
        Handle a show response.
        """
        if response["status"] == "ok":
            pass
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to show video: {cause}")

    def request_information(self):
        """
        Request video information for the focused or top-most (in z-order) window.
        """
        self._focused_video_info = None

        self.send({"command": "request information"})

    def _on_request_information_response(self, response: dict):
        """
        Handle a request information response.
        """
        if response["status"] == "ok":
            self._focused_video_info = self._get_video_info(response)
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to request information: {cause}")

    def request_all_information(self):
        """
        Request video information for all videos.
        """
        self._all_video_info = None

        self.send({"command": "request all information"})

    def _on_request_all_information_response(self, response: dict):
        """
        Handle a request all information response.
        """
        if response["status"] == "ok":
            self._all_video_info = list(map(self._get_video_info, response["videos"]))
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to request all information: {cause}")

    def play(self, uuid: UUID, rate: Optional[float] = None):
        """
        Play a video.
        """
        play_command = {"command": "play", "uuid": str(uuid)}

        if rate is not None:
            play_command["rate"] = rate

        self.send(play_command)

    def _on_play_response(self, response: dict):
        """
        Handle a play response.
        """
        if response["status"] == "ok":
            pass
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to play video: {cause}")

    def pause(self, uuid: UUID):
        """
        Pause a video.
        """
        self.send({"command": "pause", "uuid": str(uuid)})

    def _on_pause_response(self, response: dict):
        """
        Handle a pause response.
        """
        if response["status"] == "ok":
            pass
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to pause video: {cause}")

    def request_player_state(self, uuid: UUID):
        """
        Request the player state for a video.
        """
        self._video_player_state.pop(uuid, None)

        self.send({"command": "request player state", "uuid": str(uuid)})

    def _on_request_player_state_response(self, response: dict):
        """
        Handle a request player state response.
        """
        if response["status"] == "ok":
            uuid = UUID(response["uuid"])
            self._video_player_state[uuid] = self._get_video_player_state(response)
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to request player state: {cause}")

    def seek_elapsed_time(self, uuid: UUID, elapsed_time_millis: float):
        """
        Seek to an elapsed time in a video.
        """
        self.send(
            {
                "command": "seek elapsed time",
                "uuid": str(uuid),
                "elapsedTimeMillis": elapsed_time_millis,
            }
        )

    def _on_seek_elapsed_time_response(self, response: dict):
        """
        Handle a seek elapsed time response.
        """
        if response["status"] == "ok":
            pass
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to seek elapsed time: {cause}")

    def frame_advance(self, uuid: UUID, direction: int):
        """
        Advance a video by a single frame.
        """
        self.send(
            {"command": "frame advance", "uuid": str(uuid), "direction": direction}
        )

    def _on_frame_advance_response(self, response: dict):
        """
        Handle a frame advance response.
        """
        if response["status"] == "ok":
            pass
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to frame advance: {cause}")

    def frame_capture(
        self, uuid: UUID, image_location: Path, image_reference_uuid: UUID
    ):
        """
        Capture a frame from a video.
        """
        self.send(
            {
                "command": "frame capture",
                "uuid": str(uuid),
                "imageLocation": str(image_location.absolute()),
                "imageReferenceUuid": str(image_reference_uuid),
            }
        )

    def _on_frame_capture_response(self, response: dict):
        """
        Handle a frame capture response.
        """
        if response["status"] == "ok":
            pass
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to frame capture: {cause}")

    def _on_frame_capture_done_response(self, response: dict):
        """
        Handle a frame capture done response.
        """
        if response["status"] == "ok":
            frame_capture = self._get_frame_capture(response)
            self._frame_captures.append(frame_capture)
            self.logger.info(
                f"Captured frame {frame_capture.image_reference_uuid} in video {frame_capture.uuid}"
            )
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to capture frame: {cause}")

    def add_localizations(self, uuid: UUID, localizations: List[Localization]):
        """
        Add localizations to a video.
        """
        self.send(
            {
                "command": "add localizations",
                "uuid": str(uuid),
                "localizations": [
                    localization.encode() for localization in localizations
                ],
            }
        )

        for localization in localizations:
            self._uncommitted_localizations[localization.uuid] = localization

    def _on_add_localizations_response(self, response: dict):
        """
        Handle an add localizations response.
        """
        if response["status"] == "ok":
            self._commit_localizations()
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to add localizations: {cause}")
            self._revert_localizations()

    def remove_localizations(self, uuid: UUID, localization_uuids: List[UUID]):
        """
        Remove localizations from a video.
        """
        self.send(
            {
                "command": "remove localizations",
                "uuid": str(uuid),
                "localizations": [
                    str(localization_uuid) for localization_uuid in localization_uuids
                ],
            }
        )

        for localization_uuid in localization_uuids:
            self._uncommitted_localizations.pop(localization_uuid, None)

    def _on_remove_localizations_response(self, response: dict):
        """
        Handle a remove localizations response.
        """
        if response["status"] == "ok":
            self._commit_localizations()
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to remove localizations: {cause}")
            self._revert_localizations()

    def update_localizations(self, uuid: UUID, localizations: List[Localization]):
        """
        Update localizations in a video.
        """
        self.send(
            {
                "command": "update localizations",
                "uuid": str(uuid),
                "localizations": [
                    localization.encode() for localization in localizations
                ],
            }
        )

        for localization in localizations:
            self._uncommitted_localizations[localization.uuid] = localization

    def _on_update_localizations_response(self, response: dict):
        """
        Handle an update localizations response.
        """
        if response["status"] == "ok":
            self._commit_localizations()
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to update localizations: {cause}")
            self._revert_localizations()

    def clear_localizations(self, uuid: UUID):
        """
        Clear localizations from a video.
        """
        self.send({"command": "clear localizations", "uuid": str(uuid)})

        self._uncommitted_localizations.clear()

    def _on_clear_localizations_response(self, response: dict):
        """
        Handle a clear localizations response.
        """
        if response["status"] == "ok":
            self._commit_localizations()
        else:
            cause = response["cause"]
            self.logger.error(f"Failed to clear localizations: {cause}")
            self._revert_localizations()

    def select_localizations(self, uuid: UUID, localization_uuids: List[UUID]):
        """
        Select localizations in a video.
        """
        self.send(
            {
                "command": "select localizations",
                "uuid": str(uuid),
                "localizations": [
                    str(localization_uuid) for localization_uuid in localization_uuids
                ],
            }
        )

        self._selected_localizations[uuid] = localization_uuids

    def _on_select_localizations_response(self, response: dict):
        """
        Handle a select localizations response.
        """
        if response["status"] == "ok":
            pass
        else:  # No recourse for unexpected failure. Just log it for now.
            cause = response["cause"]
            self.logger.error(f"Failed to select localizations: {cause}")
