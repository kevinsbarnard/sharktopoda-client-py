"""
Sharktopoda 2 client.
"""

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
    
    def _handler(self, data: dict, addr: tuple) -> dict:
        """
        Handle a UDP packet.
        
        Args:
            data: The UDP packet data.
            addr: The address of the sender.
        """
        self.logger.debug(f"Received UDP datagram from {addr}: {data}")
        
        if data["command"] == "ping":
            # Send a ping response
            return {
                "response": "ping",
                "status": "ok"
            }
    
    def _request(self, data: dict) -> dict:
        return self._udp_client.request(data)
    
    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            True if the connection was successful, False otherwise.
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
            return False
        
        # Check the response status
        if connect_response["status"] != "ok":
            self.logger.error("Failed to connect to Sharktopoda 2")
        
        # Connected!
        self.logger.info("Connected to Sharktopoda 2")
        return True
    
    # def open(self, uuid: UUID, url: str) -> bool:
    #     """
    #     Open a video.
        
    #     Args:
    #         uuid: The UUID of the video.
    #         url: The URL of the video.
        
    #     Returns:
    #         True if the video was opened successfully, False otherwise.
    #     """
    #     open_command = {
    #         "command": "open",
    #         "uuid": str(uuid),
    #         "url": url
    #     }
    #     open_response = self._send_and_receive(open_command)
        
    #     # Check the response status
    #     if open_response["status"] != "ok":
    #         self.logger.error("Failed to initiate open video")
    #         return False
        
    #     # Wait for open done response
    #     open_done_response = self._receive(timeout=20)
        
    #     # Check the response status
    #     if open_done_response["status"] != "ok":
    #         cause = open_done_response["cause"]
    #         self.logger.error(f"Failed to open video: {cause}")
    #         return False
        
    #     opened_uuid = open_done_response["uuid"]
    #     self.logger.info(f"Opened video {opened_uuid}")
    #     return True
