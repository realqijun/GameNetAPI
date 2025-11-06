from typing import Tuple

CLIENT_PORT = 50000
FORWARDER_PORT = 55000
SERVER_PORT = 60000

MAX_SEND_WINDOW_SIZE = 4096
"""
Maximum number of packets that can be sent at the same time
"""

MAX_RETRY = 15
"""
Maximum number of times a packet get (re)transmitted
"""

SKIP_AHEAD_TIMEOUT = 0.750
"""
How long does it take to skip the current ACK if the socket is stuck there
"""

RETRY_INCREMENT = 0.050
"""
The time offset to retransmit this packet
"""

TIME_WAIT_TIME = 5.000
"""
The amount of time to wait for in TIME_WAIT
"""

AddrPort = Tuple[str, int]


class IllegalStateChangeException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"Invalid State Change: {self.message}"


class SocketTimeoutException(Exception):
    def __str__(self):
        return "Socket timed out"
