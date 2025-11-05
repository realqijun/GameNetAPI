from api.gns import GameNetSocket
from common import FORWARDER_PORT, CLIENT_PORT
import time


def main():
    sock = GameNetSocket()
    sock.bind(('127.0.0.1', CLIENT_PORT))
    sock.connect(('127.0.0.1', FORWARDER_PORT))

    for i in range(32):
        message = f"I am Minh {i}"
        sock.send(message.encode('utf-8'), True)

    sock.close()


main()
