"""
Sharktopoda 2 client.
"""

from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sharktopoda_client.dto import (FrameCapture, Localization, VideoInfo,
                                    VideoPlayerState)
from sharktopoda_client.log import LogMixin
from sharktopoda_client.udp import Timeout, UDPClient, UDPServer


class SharktopodaClient(LogMixin):
    """
    Sharktopoda 2 client.
    """

    def __init__(self, send_host: str, send_port: int, receive_port: int):
        self._udp_client = UDPClient(send_host, send_port)

        self._udp_server = UDPServer(receive_port, self._handler)
        self._udp_server.start()

    def _handler(self, data: dict, addr: tuple) -> Optional[dict]:
        """
        Handle a UDP packet.

        Args:
            data: The UDP packet data.
            addr: The address of the sender.
        """
        self.logger.debug(f"Received UDP datagram from {addr}: {data}")

        command = data.get("command", None)
        response = data.get("response", None)

        if command == "ping":
            # Send a ping response
            return {"response": "ping", "status": "ok"}

        elif response == "open done":
            status = data.get("status", None)
            if status == "ok":
                # Opened a video
                uuid = UUID(data["uuid"])
                self.logger.info(f"Open video success: {uuid}")
            elif status == "failed":
                # Failed to open a video
                cause = data.get("cause", None)
                self.logger.error(f"Failed to open video: {cause}")

        elif response == "frame capture done":
            status = data.get("status", None)
            if status == "ok":
                # Captured frame
                frame_capture = FrameCapture.decode(data)
                self.logger.info(f"Captured frame: {frame_capture}")
            elif status == "failed":
                # Failed to capture frame
                cause = data.get("cause", None)
                self.logger.error(f"Failed to capture frame: {cause}")

    def _request(self, data: dict) -> dict:
        return self._udp_client.request(data)

    def connect(self):
        """
        Connect to the server.
        """
        # Send the connect command and wait for the response
        connect_command = {"command": "connect", "port": self._udp_server.port}
        try:
            connect_response = self._request(connect_command)
        except Timeout:
            self.logger.error("Connect to Sharktopoda 2 timed out")
            return

        # Check the response status
        if connect_response["status"] != "ok":
            self.logger.error("Failed to connect to Sharktopoda 2")
            return

        self.logger.info("Connected to Sharktopoda 2")

    def open(self, uuid: UUID, url: str):
        """
        Open a video.

        Args:
            uuid: The UUID of the video.
            url: The URL of the video.
        """
        open_command = {"command": "open", "uuid": str(uuid), "url": url}
        open_response = self._request(open_command)

        # Check the response status
        if open_response["status"] != "ok":
            self.logger.error("Failed to initiate open video")
            return

        self.logger.info(f"Opened video {uuid} at {url}")

    def close(self, uuid: UUID):
        """
        Close a video.

        Args:
            uuid: The UUID of the video.
        """
        close_command = {"command": "close", "uuid": str(uuid)}
        close_response = self._request(close_command)

        # Check the response status
        if close_response["status"] != "ok":
            cause = close_response.get("cause", None)
            self.logger.error(f"Failed to close video: {cause}")
            return

        self.logger.info(f"Closed video {uuid}")

    def show(self, uuid: UUID):
        """
        Show a video.

        Args:
            uuid: The UUID of the video.
        """
        show_command = {"command": "show", "uuid": str(uuid)}
        show_response = self._request(show_command)

        # Check the response status
        if show_response["status"] != "ok":
            cause = show_response.get("cause", None)
            self.logger.error(f"Failed to show video: {cause}")
            return

        self.logger.info(f"Showed video {uuid}")

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

    def play(self, uuid: UUID, rate: float = 1.0):
        """
        Play a video at a given rate.

        Args:
            uuid: The UUID of the video.
            rate: The playback rate.
        """
        play_command = {"command": "play", "uuid": str(uuid), "rate": rate}
        play_response = self._request(play_command)

        # Check the response status
        if play_response["status"] != "ok":
            cause = play_response.get("cause", None)
            self.logger.error(f"Failed to play video: {cause}")
            return

        self.logger.info(f"Played video {uuid} at {rate:.2f}x")

    def pause(self, uuid: UUID):
        """
        Pause a video.

        Args:
            uuid: The UUID of the video.
        """
        pause_command = {"command": "pause", "uuid": str(uuid)}
        pause_response = self._request(pause_command)

        # Check the response status
        if pause_response["status"] != "ok":
            cause = pause_response.get("cause", None)
            self.logger.error(f"Failed to pause video: {cause}")
            return

        self.logger.info(f"Paused video {uuid}")

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

    def seek_elapsed_time(self, uuid: UUID, elapsed_time_millis: int):
        """
        Seek a video to a given elapsed time.

        Args:
            uuid: The UUID of the video.
            elapsed_time_millis: The elapsed time in milliseconds.
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
            return

        self.logger.info(f"Seeked video {uuid} to {elapsed_time_millis} ms")

    def frame_advance(self, uuid: UUID, direction: int):
        """
        Advance a video by one frame.

        Args:
            uuid: The UUID of the video.
            direction: The direction to advance the frame.
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
            return

        self.logger.info(
            f"Advanced frame of video {uuid} {'forward' if direction > 0 else 'backward'}"
        )

    def frame_capture(
        self, uuid: UUID, image_location: Path, image_reference_uuid: UUID
    ) -> Optional[bytes]:
        """
        Capture the current frame of a video.

        Args:
            uuid: The UUID of the video.
            image_location: The location to save the image.
            image_reference_uuid: The UUID of the image reference.
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
            return

    def add_localizations(self, uuid: UUID, localizations: List[Localization]):
        """
        Add localizations to a video.

        Args:
            uuid: The UUID of the video.
            localizations: The localizations to add.
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
            return

        self.logger.info(f"Added {len(localizations)} localizations to video {uuid}")

    def remove_localizations(self, uuid: UUID, localization_uuids: List[UUID]):
        """
        Remove localizations from a video.

        Args:
            uuid: The UUID of the video.
            localization_uuids: The UUIDs of the localizations to remove.
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
            return

        self.logger.info(
            f"Removed {len(localization_uuids)} localizations from video {uuid}"
        )

    def update_localizations(self, uuid: UUID, localizations: List[Localization]):
        """
        Update localizations of a video.

        Args:
            uuid: The UUID of the video.
            localizations: The localizations to update.
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
            return

        self.logger.info(f"Updated {len(localizations)} localizations of video {uuid}")

    def clear_localizations(self, uuid: UUID):
        """
        Clear all localizations of a video.

        Args:
            uuid: The UUID of the video.
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
            return

        self.logger.info(f"Cleared localizations of video {uuid}")

    def select_localizations(self, uuid: UUID, localization_uuids: List[UUID]):
        """
        Select localizations of a video.

        Args:
            uuid: The UUID of the video.
            localization_uuids: The UUIDs of the localizations to select.
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
            return

        self.logger.info(
            f"Selected {len(localization_uuids)} localizations of video {uuid}"
        )
