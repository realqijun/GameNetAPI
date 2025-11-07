from api.gns import GameNetSocket
from common import SocketTimeoutException

server_addr = ("127.0.0.1", 6767)
tests = ["tests/test_cases/1.txt", "tests/test_cases/2.txt", "tests/test_cases/3.txt"]

def main():
    sock = GameNetSocket()
    sock.bind(server_addr)
    sock.listen()
    sock.accept()

    # server accepted a connection

    try:
        # receive 2 test packets first
        data = sock.recv()
        if not data:
            raise Exception("Client disconnected before sending anyth")
        data = sock.recv()
        if not data:
            raise Exception("Client disconnected before sending second message")

        received_packets = 2  # already received 2 packets above
        chunk = 1024
        for file in tests:
            with open(file, "r") as f:
                expected_data = f.read()
                while expected_data:
                    packet = sock.recv()
                    if not packet:
                        raise Exception("Client disconnected unexpectedly")
                    expected_chunk = expected_data[:chunk].encode()
                    if packet != expected_chunk:
                        raise Exception(f"Data mismatch for file {file}")
                    expected_data = expected_data[chunk:]
                    received_packets += 1

        print(f"Total packets received: {received_packets}")

    except SocketTimeoutException:
        print("Server timed out waiting for packet")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()
        print("Server closed.")

if __name__ == "__main__":
    main()