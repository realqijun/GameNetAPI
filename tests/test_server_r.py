from api.gns import GameNetSocket
from common import SocketTimeoutException
from time import time

server_addr = ("127.0.0.1", 6767)
# tests = ["tests/test_cases/3.txt"]
tests = ["tests/test_cases/1.txt", "tests/test_cases/2.txt", "tests/test_cases/3.txt", "tests/test_cases/4.txt"]

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    start = time()

    # server accepted a connection

    try:
        # # receive 2 test packets first
        # data = sock.recv()
        # if not data:
        #     raise Exception("Client disconnected before sending anyth")
        # data = sock.recv()
        # if not data:
        #     raise Exception("Client disconnected before sending second message")

        received_packets = 0  # already received 2 packets above
        chunk = 1024
        client_sent = 0
        for file in tests:
            with open(file, "r") as f:
                expected_data = f.read()
                client_sent += len(expected_data) / 1024
                while expected_data:
                    packet = sock.recv()
                    if not packet:
                        raise Exception("Client disconnected unexpectedly")
                    expected_chunk = expected_data[:chunk].encode()
                    if packet != expected_chunk:
                        raise Exception(f"Data mismatch for file {file}")
                    expected_data = expected_data[chunk:]
                    received_packets += 1

    except SocketTimeoutException:
        print("Server timed out waiting for packet")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()
        print(f"Total packets received: {received_packets}")
        print(f"Total packet rate: {received_packets / (time() - start):.2f} packets/sec")
        print(f"Packet delivery ratio: {(received_packets / client_sent):.2%}")
        print("Server closed.")

if __name__ == "__main__":
    main()