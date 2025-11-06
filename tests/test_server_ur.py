from api.gns import GameNetSocket
from common import SocketTimeoutException

server_addr = ("127.0.0.1", 6767)

def main():
    server = GameNetSocket()
    server.bind(server_addr)
    server.listen()
    server.accept()

    packets_received = 0

    try:
        while True:
            data = server.recv()
            if not data:
                break
            packets_received += 1
    except SocketTimeoutException as e:
        pass

    server.close()
    print(f"Total packets received: {packets_received}")

if __name__ == "__main__":
    main()