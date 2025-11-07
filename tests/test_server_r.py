from math import ceil
from api.gns import GameNetSocket
from common import SocketTimeoutException
from time import time

server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt",
         "tests/test_cases/2.txt",
         "tests/test_cases/3.txt",
         "tests/test_cases/4.txt",
         "tests/test_cases/5.txt"]

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    start = time()
    try:
        received_packets = 0
        chunk = 1024
        client_sent = 0
        for file in tests:
            with open(file, "r") as f:
                expected_data = f.read()
                expected_packets = ceil(len(expected_data) / chunk)
                client_sent += expected_packets
                for _ in range(expected_packets):
                    packet = sock.recv()
                    if not packet:
                        raise Exception("Client disconnected unexpectedly")
                    received_packets += 1

    except SocketTimeoutException:
        print("Server timed out waiting for packet")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()
        print("Server closed.")
        print(f"Total packets received: {received_packets}")
        print(f"Total packet rate: {received_packets / (time() - start):.2f} packets/sec")
        print(f"Packet delivery ratio: {(received_packets / client_sent):.2%}")

if __name__ == "__main__":
    main()