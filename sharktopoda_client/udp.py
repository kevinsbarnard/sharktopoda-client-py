import json
from socket import AF_INET6, SOCK_DGRAM, socket, timeout
from threading import Thread

from sharktopoda_client.log import LogMixin


class Timeout(Exception):
    """
    Exception raised when a UDP receive timeout occurs.
    """

    pass


class EphemeralSocket:
    """
    Ephemeral socket context manager. Creates a new socket for a send/receive operation.
    """

    def __init__(self, timeout: float = 1.0) -> None:
        self._socket = None
        self._timeout = timeout

    def __enter__(self):
        self._socket = socket(AF_INET6, SOCK_DGRAM)
        self._socket.settimeout(self._timeout)
        return self._socket

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._socket.close()


class UDPServer(LogMixin):
    """
    IPv6 UDP server.
    """

    def __init__(self, port: int, handler: callable) -> None:
        self._port = port
        self._handler = handler

        self._socket = None
        self._thread = None
        self._ok = True

    @property
    def port(self) -> int:
        """
        The port the server is listening on.
        """
        return self._port

    @property
    def ok(self) -> bool:
        """
        Whether the server is running.
        """
        return self._ok

    def _spin(self) -> None:
        """
        Server thread main loop.
        """
        self.logger.info("UDP server thread started")

        while self._ok:
            # Receive
            request_bytes, addr = self.socket.recvfrom(4096)
            self.logger.debug("Received UDP datagram {data} from {addr}")

            # Decode
            request_json = request_bytes.decode("utf-8")
            request_data = json.loads(request_json)

            # Handle
            try:
                response_data = self._handler(request_data, addr)
            except Exception as e:
                self.logger.error(f"Error while handling UDP request: {e}")
                self._ok = False
                break

            if response_data is None:  # no response
                continue

            # Encode
            response_json = json.dumps(response_data)
            response_bytes = response_json.encode("utf-8")

            # Send
            self.socket.sendto(response_bytes, addr)

        self.logger.info("UDP server thread exiting")

    def start(self) -> None:
        """
        Start the UDP server.
        """
        self._ok = True
        self._thread = Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the UDP server.
        """
        self._ok = False

    @property
    def socket(self):
        """
        The UDP socket. Lazy-initialized.
        """
        if self._socket is None:
            self._socket = socket(AF_INET6, SOCK_DGRAM)
            host = ""  # listen on all interfaces
            self._socket.bind((host, self._port))
            self.logger.info(f"Opened UDP socket on {host}:{self._port}")
        return self._socket

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
            self.logger.info("Closed UDP socket")


class UDPClient(LogMixin):
    """
    IPv6 UDP client. Sends and receives data encoded as JSON.
    """

    def __init__(
        self, server_host: str, server_port: int, buffer_size: int = 4096, timeout: float = 1.0
    ) -> None:
        self._server_host = server_host
        self._server_port = server_port

        self._buffer_size = buffer_size
        self._timeout = timeout

    def request(self, data: dict) -> dict:
        """
        Issue a request to the UDP server.

        Args:
            data: Data to send.

        Returns:
            dict: Response data.
        """
        # Encode
        data_json = json.dumps(data)
        data_bytes = data_json.encode("utf-8")

        with EphemeralSocket(timeout=self._timeout) as sock:
            # Send
            sock.sendto(data_bytes, (self._server_host, self._server_port))
            self.logger.debug(
                f"Sent UDP datagram {data} to {self._server_host}:{self._server_port}"
            )

            # Receive
            try:
                response_data_bytes, addr = sock.recvfrom(self._buffer_size)
                self.logger.debug(f"Received UDP datagram {data} from {addr}")
            except timeout:
                self.logger.warning(f"UDP receive timed out")
                raise Timeout()

        # Decode
        response_data_json = response_data_bytes.decode("utf-8")
        response_data_dict = json.loads(response_data_json)

        return response_data_dict
