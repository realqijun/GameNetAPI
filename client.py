from api.gns import GameNetSocket
from common import FORWARDER_PORT


def main():
    sock = GameNetSocket()
    sock.connect(('127.0.0.1', FORWARDER_PORT))


main()
