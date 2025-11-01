from api.gns import GameNetSocket
from common import SERVER_PORT
import time


def main():
    sock = GameNetSocket()
    sock.bind(('127.0.0.1', SERVER_PORT))
    sock.listen()
    sock.accept()
    for i in range(5):
        sock.send(f"I am Minh from Server {i}".encode('utf-8'), True)
    time.sleep(1)
    sock.close()
    while True:
        print(sock.recv().decode(encoding='utf-8'), flush=True)


main()
