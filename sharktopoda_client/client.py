"""
Sharktopoda 2 client.
"""

from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sharktopoda_client.dto import (FrameCapture, Localization, VideoInfo,
                                    VideoPlayerState)
from sharktopoda_client.localization import LocalizationController, NoOpLocalizationController
from sharktopoda_client.log import LogMixin
from sharktopoda_client.udp import Timeout, UDPClient, UDPServer


class SharktopodaClient(LogMixin):
    """
    Sharktopoda 2 client.
    """

    def __init__(self, send_host: str, send_port: int, receive_port: int, localization_controller: Optional[LocalizationController] = None, timeout: float = 1.0):
        """
        Initialize the client.
        
        Args:
            send_host: The IPv6 host to send UDP packets to.
            send_port: The port to send UDP packets to.
            receive_port: The port to receive UDP packets on.
            localization_controller: The localization controller to use. If None, a NoOpLocalizationController will be used.
            timeout: The timeout for UDP client requests.
        """
        self._udp_client = UDPClient(send_host, send_port, timeout=timeout)

        self._udp_server = UDPServer(receive_port, self._handler)
        assert self._udp_server.socket is not None  # force socket creation, may raise exception
        self._udp_server.start()
        
        self._localization_controller = localization_controller or NoOpLocalizationController()
        
        self._open_callbacks = {}

    def _handler(self, data: dict, addr: tuple) -> Optional[dict]:
        """
        Handle a UDP packet.

        Args:
            data: The UDP packet data.
            addr: The address of the sender.
        """
        self.logger.debug(f"Received UDP datagram from {addr}: {data}")

        command = data.get("command", None)

        def ok() -> dict:
            return {"response": command, "status": "ok"}

        if command == "ping":
            return ok()

        elif command == "open done":
            status = data.get("status", None)
            if status == "ok":
                # Opened a video
                uuid = UUID(data["uuid"])
                self.logger.info(f"Open video success: {uuid}")
                
                # Call the open callback and remove it
                if uuid in self._open_callbacks:
                    self._open_callbacks[uuid]()
                    del self._open_callbacks[uuid]
            elif status == "failed":
                # Failed to open a video
                cause = data.get("cause", None)
                self.logger.error(f"Failed to open video: {cause}")

        elif command == "frame capture done":
            status = data.get("status", None)
            if status == "ok":
                # Captured frame
                frame_capture = FrameCapture.decode(data)
                self.logger.info(f"Captured frame: {frame_capture}")
            elif status == "failed":
                # Failed to capture frame
                cause = data.get("cause", None)
                self.logger.error(f"Failed to capture frame: {cause}")
        
        elif command == "add localizations" or command == "update localizations":
            uuid = UUID(data["uuid"])
            localizations = list(map(Localization.decode, data["localizations"]))
            self.logger.info(f"Received {len(localizations)} localizations for video {uuid}")
            self._localization_controller.add_update_localizations(uuid, localizations)
            return ok()
        
        elif command == "remove localizations":
            uuid = UUID(data["uuid"])
            localization_uuids = list(map(UUID, data["localizations"]))
            self.logger.info(f"Received {len(localization_uuids)} localization removals for video {uuid}")
            self._localization_controller.remove_localizations(uuid, localization_uuids)
            return ok()
        
        elif command == "clear localizations":
            uuid = UUID(data["uuid"])
            self.logger.info(f"Received localization clear for video {uuid}")
            self._localization_controller.clear_collection(uuid)
            return ok()
        
        elif command == "select localizations":
            uuid = UUID(data["uuid"])
            localization_uuids = list(map(UUID, data["localizations"]))
            self.logger.info(f"Received localization selection for video {uuid}")
            self._localization_controller.select_localizations(uuid, localization_uuids)
            return ok()

    def _request(self, data: dict) -> Optional[dict]:
        try:
            return self._udp_client.request(data)
        except Timeout:
            self.logger.error("Request to Sharktopoda 2 timed out")
            return None

    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        # Send the connect command and wait for the response
        connect_command = {"command": "connect", "port": self._udp_server.port}
        connect_response = self._request(connect_command)
        if connect_response is None:
            self.logger.error("Connection to Sharktopoda 2 timed out")
            return False

        # Check the response status
        if connect_response["status"] != "ok":
            self.logger.error("Failed to connect to Sharktopoda 2")
            return False

        self.logger.info("Connected to Sharktopoda 2")
        return True

    def open(self, uuid: UUID, url: str, callback: Optional[callable] = None) -> bool:
        """
        Open a video.

        Args:
            uuid: The UUID of the video.
            url: The URL of the video.
            callback: An optional callback function to call when the video is opened.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        open_command = {"command": "open", "uuid": str(uuid), "url": url}
        open_response = self._request(open_command)

        # Check the response status
        if open_response["status"] != "ok":
            self.logger.error("Failed to initiate open video")
            return False

        self.logger.info(f"Initiated open video {uuid} at {url}")
        
        # Store the callback
        if callback is not None:
            self._open_callbacks[uuid] = callback
        
        return True

    def close(self, uuid: UUID) -> bool:
        """
        Close a video.

        Args:
            uuid: The UUID of the video.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        close_command = {"command": "close", "uuid": str(uuid)}
        close_response = self._request(close_command)

        # Check the response status
        if close_response["status"] != "ok":
            cause = close_response.get("cause", None)
            self.logger.error(f"Failed to close video: {cause}")
            return False

        self.logger.info(f"Closed video {uuid}")
        return True

    def show(self, uuid: UUID) -> bool:
        """
        Show a video.

        Args:
            uuid: The UUID of the video.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        show_command = {"command": "show", "uuid": str(uuid)}
        show_response = self._request(show_command)

        # Check the response status
        if show_response["status"] != "ok":
            cause = show_response.get("cause", None)
            self.logger.error(f"Failed to show video: {cause}")
            return False

        self.logger.info(f"Showed video {uuid}")
        return True

    def request_information(self) -> Optional[VideoInfo]:
        """
        Request information about the current video.

        Returns:
            The video information, or None if there is no video.
        """
        request_information_command = {"command": "request information"}
        request_information_response = self._request(request_information_command)

        # Check the response status
        if request_information_response["status"] != "ok":
            cause = request_information_response.get("cause", None)
            self.logger.error(f"Failed to request video information: {cause}")
            return None

        return VideoInfo.decode(request_information_response)

    def request_all_information(self) -> Optional[List[VideoInfo]]:
        """
        Request information about all videos.

        Returns:
            The video information, or None if there is no video.
        """
        request_all_information_command = {"command": "request all information"}
        request_all_information_response = self._request(
            request_all_information_command
        )

        # Check the response status
        if request_all_information_response["status"] != "ok":
            cause = request_all_information_response.get("cause", None)
            self.logger.error(f"Failed to request video information: {cause}")
            return None

        return list(
            map(VideoInfo.decode, request_all_information_response.get("videos", []))
        )

    def play(self, uuid: UUID, rate: float = 1.0) -> bool:
        """
        Play a video at a given rate.

        Args:
            uuid: The UUID of the video.
            rate: The playback rate.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        play_command = {"command": "play", "uuid": str(uuid), "rate": rate}
        play_response = self._request(play_command)

        # Check the response status
        if play_response["status"] != "ok":
            cause = play_response.get("cause", None)
            self.logger.error(f"Failed to play video: {cause}")
            return False

        self.logger.info(f"Played video {uuid} at {rate:.2f}x")
        return True

    def pause(self, uuid: UUID) -> bool:
        """
        Pause a video.

        Args:
            uuid: The UUID of the video.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        pause_command = {"command": "pause", "uuid": str(uuid)}
        pause_response = self._request(pause_command)

        # Check the response status
        if pause_response["status"] != "ok":
            cause = pause_response.get("cause", None)
            self.logger.error(f"Failed to pause video: {cause}")
            return False

        self.logger.info(f"Paused video {uuid}")
        return True

    def request_elapsed_time(self, uuid: UUID) -> Optional[float]:
        """
        Request the elapsed time of a video.

        Returns:
            The elapsed time, or None if there is no video.
        """
        request_elapsed_time_command = {
            "command": "request elapsed time",
            "uuid": str(uuid),
        }
        request_elapsed_time_response = self._request(request_elapsed_time_command)

        # Check the response status
        if request_elapsed_time_response["status"] != "ok":
            cause = request_elapsed_time_response.get("cause", None)
            self.logger.error(f"Failed to request elapsed time: {cause}")
            return None

        return request_elapsed_time_response["elapsed time"]

    def request_player_state(self, uuid: UUID) -> Optional[VideoPlayerState]:
        """
        Request the state of a video player.

        Returns:
            The player state, or None if there is no video.
        """
        request_player_state_command = {
            "command": "request player state",
            "uuid": str(uuid),
        }
        request_player_state_response = self._request(request_player_state_command)

        # Check the response status
        if request_player_state_response["status"] != "ok":
            cause = request_player_state_response.get("cause", None)
            self.logger.error(f"Failed to request player state: {cause}")
            return None

        return VideoPlayerState.decode(request_player_state_response)

    def seek_elapsed_time(self, uuid: UUID, elapsed_time_millis: int) -> bool:
        """
        Seek a video to a given elapsed time.

        Args:
            uuid: The UUID of the video.
            elapsed_time_millis: The elapsed time in milliseconds.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        seek_elapsed_time_command = {
            "command": "seek elapsed time",
            "uuid": str(uuid),
            "elapsedTimeMillis": elapsed_time_millis,
        }
        seek_elapsed_time_response = self._request(seek_elapsed_time_command)

        # Check the response status
        if seek_elapsed_time_response["status"] != "ok":
            cause = seek_elapsed_time_response.get("cause", None)
            self.logger.error(f"Failed to seek elapsed time: {cause}")
            return False

        self.logger.info(f"Seeked video {uuid} to {elapsed_time_millis} ms")
        return True

    def frame_advance(self, uuid: UUID, direction: int) -> bool:
        """
        Advance a video by one frame.

        Args:
            uuid: The UUID of the video.
            direction: The direction to advance the frame.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        frame_advance_command = {
            "command": "frame advance",
            "uuid": str(uuid),
            "direction": direction,
        }
        frame_advance_response = self._request(frame_advance_command)

        # Check the response status
        if frame_advance_response["status"] != "ok":
            cause = frame_advance_response.get("cause", None)
            self.logger.error(f"Failed to advance frame: {cause}")
            return False

        self.logger.info(
            f"Advanced frame of video {uuid} {'forward' if direction > 0 else 'backward'}"
        )
        return True

    def frame_capture(
        self, uuid: UUID, image_location: Path, image_reference_uuid: UUID
    ) -> Optional[bytes]:
        """
        Capture the current frame of a video.

        Args:
            uuid: The UUID of the video.
            image_location: The location to save the image.
            image_reference_uuid: The UUID of the image reference.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        frame_capture_command = {
            "command": "frame capture",
            "uuid": str(uuid),
            "imageLocation": str(image_location),
            "imageReferenceUuid": str(image_reference_uuid),
        }
        frame_capture_response = self._request(frame_capture_command)

        # Check the response status
        if frame_capture_response["status"] != "ok":
            cause = frame_capture_response.get("cause", None)
            self.logger.error(f"Failed to initiate frame capture: {cause}")
            return False

        return True

    def add_localizations(self, uuid: UUID, localizations: List[Localization]) -> bool:
        """
        Add localizations to a video.

        Args:
            uuid: The UUID of the video.
            localizations: The localizations to add.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        add_localizations_command = {
            "command": "add localizations",
            "uuid": str(uuid),
            "localizations": list(map(Localization.encode, localizations)),
        }
        add_localizations_response = self._request(add_localizations_command)

        # Check the response status
        if add_localizations_response["status"] != "ok":
            cause = add_localizations_response.get("cause", None)
            self.logger.error(f"Failed to add localizations: {cause}")
            return False

        self._localization_controller.add_update_localizations(uuid, localizations)
        
        self.logger.info(f"Added {len(localizations)} localizations to video {uuid}")
        return True

    def remove_localizations(self, uuid: UUID, localization_uuids: List[UUID]) -> bool:
        """
        Remove localizations from a video.

        Args:
            uuid: The UUID of the video.
            localization_uuids: The UUIDs of the localizations to remove.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        remove_localizations_command = {
            "command": "remove localizations",
            "uuid": str(uuid),
            "localizations": list(map(str, localization_uuids)),
        }
        remove_localizations_response = self._request(remove_localizations_command)

        # Check the response status
        if remove_localizations_response["status"] != "ok":
            cause = remove_localizations_response.get("cause", None)
            self.logger.error(f"Failed to remove localizations: {cause}")
            return False

        self._localization_controller.remove_localizations(uuid, localization_uuids)
        
        self.logger.info(
            f"Removed {len(localization_uuids)} localizations from video {uuid}"
        )
        return True

    def update_localizations(self, uuid: UUID, localizations: List[Localization]) -> bool:
        """
        Update localizations of a video.

        Args:
            uuid: The UUID of the video.
            localizations: The localizations to update.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        update_localizations_command = {
            "command": "update localizations",
            "uuid": str(uuid),
            "localizations": list(map(Localization.encode, localizations)),
        }
        update_localizations_response = self._request(update_localizations_command)

        # Check the response status
        if update_localizations_response["status"] != "ok":
            cause = update_localizations_response.get("cause", None)
            self.logger.error(f"Failed to update localizations: {cause}")
            return False
        
        self._localization_controller.add_update_localizations(uuid, localizations)

        self.logger.info(f"Updated {len(localizations)} localizations of video {uuid}")
        return True

    def clear_localizations(self, uuid: UUID) -> bool:
        """
        Clear all localizations of a video.

        Args:
            uuid: The UUID of the video.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        clear_localizations_command = {
            "command": "clear localizations",
            "uuid": str(uuid),
        }
        clear_localizations_response = self._request(clear_localizations_command)

        # Check the response status
        if clear_localizations_response["status"] != "ok":
            cause = clear_localizations_response.get("cause", None)
            self.logger.error(f"Failed to clear localizations: {cause}")
            return False
        
        self._localization_controller.clear_collection(uuid)

        self.logger.info(f"Cleared localizations of video {uuid}")
        return True

    def select_localizations(self, uuid: UUID, localization_uuids: List[UUID]) -> bool:
        """
        Select localizations of a video.

        Args:
            uuid: The UUID of the video.
            localization_uuids: The UUIDs of the localizations to select.
        
        Returns:
            True if the operation was successful, False otherwise.
        """
        select_localizations_command = {
            "command": "select localizations",
            "uuid": str(uuid),
            "localizations": list(map(str, localization_uuids)),
        }
        select_localizations_response = self._request(select_localizations_command)

        # Check the response status
        if select_localizations_response["status"] != "ok":
            self.logger.error(f"Failed to select localizations")
            return False
        
        self._localization_controller.clear_collection(uuid)

        self.logger.info(
            f"Selected {len(localization_uuids)} localizations of video {uuid}"
        )
        return True

    def stop_server(self):
        """
        Stop the UDP server.
        """
        self._udp_server.stop()

    def __del__(self):
        self.stop_server()
