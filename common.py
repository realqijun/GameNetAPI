from typing import Tuple

CLIENT_PORT = 50000
FORWARDER_PORT = 55000
SERVER_PORT = 60000


class IllegalStateChangeException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"Invalid State Change: {self.message}"


AddrPort = Tuple[str, int]
