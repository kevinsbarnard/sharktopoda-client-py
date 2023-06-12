import json
from threading import Thread
from socket import socket, AF_INET, SOCK_DGRAM

from rx.subject import Subject
from rx.scheduler import EventLoopScheduler

from sharktopoda_client.log import LogMixin


class Timeout(Exception):
    """
    Exception raised when a UDP receive timeout occurs.
    """
    pass


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


class UDPServer(LogMixin):
    """
    UDP server. Wrapper for UDP socket.
    """
    
    def __init__(self, send_host: str, send_port: int, receive_port: int) -> None:
        # UDP socket
        self._socket = None
        self._send_host = send_host
        self._send_port = send_port
        self._receive_port = receive_port
    
    def send(self, data: dict) -> None:
        """
        Send a UDP datagram to the send host and port.
        
        Args:
            data: Data to send.
        """
        # Encode the data
        json_data = json.dumps(data)
        datagram = json_data.encode('utf-8')

        # Send the packet
        self.socket.sendto(datagram, (self._send_host, self._send_port))

        self.logger.debug(
            f"Sent UDP datagram {datagram} to {self._send_host}:{self._send_port}"
        )
    
    def receive(self, timeout: int = 5) -> dict:
        """
        Receive a UDP datagram. Blocks until a datagram is received.
        
        Returns:
            dict: Decoded data.
        """
        # Block until we receive a datagram
        self.socket.settimeout(timeout)
        try:
            datagram, (host, port) = self.socket.recvfrom(4096)
        except timeout:
            raise TimeoutError("Timed out waiting for UDP datagram")

        self.logger.debug(
            f"Received UDP datagram {datagram} from {host}:{port}"
        )
        
        # Decode the datagram
        json_data = datagram.decode('utf-8')
        data = json.loads(json_data)
        return data
    
    @property
    def send_host(self) -> str:
        return self._send_host
    
    @property
    def send_port(self) -> int:
        return self._send_port
    
    @property
    def receive_port(self) -> int:
        return self._receive_port
    
    @property
    def socket(self):
        if self._socket is None:
            self._socket = socket(AF_INET, SOCK_DGRAM)
            host = ""  # listen on all interfaces
            self._socket.bind((host, self._receive_port))
            self.logger.info(f"Opened UDP socket on {host}:{self._receive_port}")
        return self._socket
