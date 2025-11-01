from api.gns import GameNetSocket
from common import FORWARDER_PORT
import time


def main():
    sock = GameNetSocket()
    sock.connect(('127.0.0.1', FORWARDER_PORT))
    for i in range(5):
        sock.send(f"I am Minh {i}".encode('utf-8'), True)
    sock.close()
    while True:
        print(sock.recv().decode(encoding='utf-8'), flush=True)

main()
