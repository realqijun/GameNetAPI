from api.gns import GameNetSocket
from common import SocketTimeoutException
import socket

server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    received_packets = 0

    try:
        while True:
            data = sock.recv()
            if not data:
                break
            received_packets += 1
    except SocketTimeoutException as e:
        pass

    sock.close()
    print(f"Total packets received: {received_packets}")

if __name__ == "__main__":
    main()