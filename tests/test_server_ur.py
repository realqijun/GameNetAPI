from api.gns import GameNetSocket
from common import SocketTimeoutException

server_addr = ("127.0.0.1", 6767)

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    reliable_packets_received = 0
    unreliable_packets_received = 0

    try:
        while True:
            data = sock.recv()
            if not data:
                break
            if data.startswith(b'REL:'):
                reliable_packets_received += 1
            elif data.startswith(b'UNR:'):
                unreliable_packets_received += 1
    except SocketTimeoutException as e:
        pass

    sock.close()
    print(f"Reliable packets received: {reliable_packets_received}")
    print(f"Unreliable packets received: {unreliable_packets_received}")

if __name__ == "__main__":
    main()