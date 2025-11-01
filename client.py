from api.gns import GameNetSocket
from common import FORWARDER_PORT


def main():
    sock = GameNetSocket()
    sock.connect(('127.0.0.1', FORWARDER_PORT))
    for i in range(10):
        sock.send(f"I am Minh {i}".encode('utf-8'), True)


main()
