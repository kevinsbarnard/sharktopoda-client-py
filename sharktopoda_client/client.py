"""
Sharktopoda 2 client.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sharktopoda_client.log import LogMixin
from sharktopoda_client.udp import RxUDPServer, Timeout, UDPServer
from sharktopoda_client.dto import (
    FrameCapture,
    VideoInfo,
    Localization,
    VideoPlayerState,
)


class SharktopodaClient(LogMixin):
    """
    Sharktopoda client. Manages local state and communication with the server (application).
    """
    
    class VideoOpenState(Enum):
        CLOSED = 0
        OPENING = 1
        OPEN = 2

    def __init__(self, rx_udp_server: RxUDPServer):
        """
        Args:
            rx_udp_server: The ReactiveX UDP server to use for communication.
        """
        self.rx_udp_server = rx_udp_server

        self._connected = False
        self._video_open_state = {}  # keyed by video UUID
        self._focused_video_info = None
        self._all_video_info = None
        self._video_player_state = {}  # keyed by video UUID
        self._frame_captures = []
        self._uncommitted_localizations = {}  # keyed by localization UUID
        self._localizations = {}  # keyed by localization UUID
        self._selected_localizations = []

        self.rx_udp_server.receive_subject.subscribe(self._handle_message)
        
    @property
    def connected(self) -> bool:
        """
        Get whether the client is connected to the server.

        Returns:
            Whether the client is connected to the server.
        """
        return self._connected
    
    def video_open_state(self) -> dict:
        """
        Get the video open state dict.

        Returns:
            The video open state dict.
        """
        return self._video_open_state
    
    def focused_video_info(self) -> Optional[VideoInfo]:
        """
        Get the focused video info.

        Returns:
            The focused video info, or None if there is no focused video info.
        """
        return self._focused_video_info
    
    def all_video_info(self) -> Optional[List[VideoInfo]]:
        """
        Get all video info.

        Returns:
            All video info, or None if there is no all video info.
        """
        return self._all_video_info
    
    def video_player_state(self) -> dict:
        """
        Get the video player state dict.
        
        Returns:
            The video player state dict.
        """
    
    def frame_captures(self) -> List[FrameCapture]:
        """
        Get the frame captures.
        
        Returns:
            The frame captures.
        """
        return self._frame_captures
    
    def localizations(self) -> dict:
        """
        Get the localizations.
        
        Returns:
            The localizations.
        """
        return self._localizations
    
    def selected_localizations(self) -> list:
        """
        Get the selected localizations.
        
        Returns:
            The selected localizations.
        """
        return self._selected_localizations

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

        self._opened_video_state[uuid] = SharktopodaClient.VideoOpenState.OPENING

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
            self._video_open_state[uuid] = SharktopodaClient.VideoOpenState.OPEN
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
            self._video_open_state[uuid] = SharktopodaClient.VideoOpenState.CLOSED
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
            self._focused_video_info = VideoInfo.decode(response)
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
            self._all_video_info = list(map(VideoInfo.decode, response["videos"]))
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
            self._video_player_state[uuid] = VideoPlayerState.decode(response)
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
            frame_capture = FrameCapture.decode(response)
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


class SynchronousSharktopodaClient(LogMixin):
    """
    Synchronous Sharktopoda 2 client.
    """
    
    def __init__(self, udp_server: UDPServer):
        self._udp_server = udp_server
        
    def _send(self, data: dict):
        """
        Send data to the server.
        """
        self._udp_server.send(data)
    
    def _receive(self, timeout: int = 5) -> dict:
        """
        Receive data from the server.
        """
        return self._udp_server.receive(timeout=timeout)
    
    def _send_and_receive(self, data: dict, timeout: int = 5) -> dict:
        """
        Send data to the server and receive a response.
        """
        self._send(data)
        return self._receive(timeout=timeout)
    
    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            True if the connection was successful, False otherwise.
        """
        # Send the connect command and wait for the response
        connect_command = {
            "command": "connect",
            "port": self._udp_server.receive_port
        }
        try:
            connect_response = self._send_and_receive(connect_command)
        except Timeout:
            self.logger.error("Connect to Sharktopoda 2 timed out")
            return False
        
        # Check the response status
        if connect_response["status"] != "ok":
            self.logger.error("Failed to connect to Sharktopoda 2")
        
        # Connected!
        self.logger.info("Connected to Sharktopoda 2")
        return True
    
    def open(self, uuid: UUID, url: str) -> bool:
        """
        Open a video.
        
        Args:
            uuid: The UUID of the video.
            url: The URL of the video.
        
        Returns:
            True if the video was opened successfully, False otherwise.
        """
        open_command = {
            "command": "open",
            "uuid": str(uuid),
            "url": url
        }
        open_response = self._send_and_receive(open_command)
        
        # Check the response status
        if open_response["status"] != "ok":
            self.logger.error("Failed to initiate open video")
            return False
        
        # Wait for open done response
        open_done_response = self._receive(timeout=20)
        
        # Check the response status
        if open_done_response["status"] != "ok":
            cause = open_done_response["cause"]
            self.logger.error(f"Failed to open video: {cause}")
            return False
        
        opened_uuid = open_done_response["uuid"]
        self.logger.info(f"Opened video {opened_uuid}")
        return True
