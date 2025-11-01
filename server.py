from api.gns import GameNetSocket
from common import SERVER_PORT


def main():
    sock = GameNetSocket()
    sock.bind(('127.0.0.1', SERVER_PORT))
    sock.listen()
    sock.accept()
    while True:
        print(sock.recv().decode(encoding='utf-8'))

main()
