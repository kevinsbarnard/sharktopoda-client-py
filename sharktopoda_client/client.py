"""
Sharktopoda 2 client.
"""

from typing import List, Optional
from uuid import UUID
from sharktopoda_client.log import LogMixin
from sharktopoda_client.udp import Timeout, UDPClient, UDPServer
from sharktopoda_client.dto import (
    FrameCapture,
    VideoInfo,
    Localization,
    VideoPlayerState,
)


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
            return {
                "response": "ping",
                "status": "ok"
            }
        
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
                
    
    def _request(self, data: dict) -> dict:
        return self._udp_client.request(data)
    
    def connect(self):
        """
        Connect to the server.
        """
        # Send the connect command and wait for the response
        connect_command = {
            "command": "connect",
            "port": self._udp_server.port
        }
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
        open_command = {
            "command": "open",
            "uuid": str(uuid),
            "url": url
        }
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
        close_command = {
            "command": "close",
            "uuid": str(uuid)
        }
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
        show_command = {
            "command": "show",
            "uuid": str(uuid)
        }
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
        request_information_command = {
            "command": "request information"
        }
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
        request_all_information_command = {
            "command": "request all information"
        }
        request_all_information_response = self._request(request_all_information_command)
        
        # Check the response status
        if request_all_information_response["status"] != "ok":
            cause = request_all_information_response.get("cause", None)
            self.logger.error(f"Failed to request video information: {cause}")
            return None
        
        return list(map(VideoInfo.decode, request_all_information_response.get("videos", [])))
