from api.gns import GameNetSocket
from common import SERVER_PORT, FORWARDER_PORT
import time


def main():
    sock = GameNetSocket()
    sock.bind(('127.0.0.1', SERVER_PORT))
    sock.connect(('127.0.0.1', FORWARDER_PORT))
    for i in range(5):
        sock.send(f"I am Minh from server {i}".encode('utf-8'), True)
    sock.close()
    for i in range(5):
        print(sock.recv().decode(encoding='utf-8'), flush=True)


main()
