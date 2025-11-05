from typing import Tuple

CLIENT_PORT = 50000
FORWARDER_PORT = 55000
SERVER_PORT = 60000

ACK_TIMEOUT = 0.200
"""
How long does it take to skip the current ACK if the socket is stuck there
"""

RETRY_INCREMENT = 0.050
"""
The time offset to retransmit this packet
"""


AddrPort = Tuple[str, int]


class IllegalStateChangeException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"Invalid State Change: {self.message}"
